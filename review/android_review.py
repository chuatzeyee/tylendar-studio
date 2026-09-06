"""Boot a disposable emulator and test the Studio APK; never targets a user's device."""
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('ANDROID_HOME', '/home/dmgadmin/android-build/sdk'))
SUPPORT = ROOT / '.build-support/android-review'
AVDS = SUPPORT / 'avd'
AVD = AVDS / 'studio-review.avd'
SHOTS = ROOT / 'review/screenshots'
ADB = str(SDK / 'platform-tools/adb')
ENV = dict(os.environ, ANDROID_HOME=str(SDK), ANDROID_SDK_ROOT=str(SDK), ANDROID_USER_HOME=str(SUPPORT),
           ANDROID_EMULATOR_HOME=str(SUPPORT), ANDROID_AVD_HOME=str(AVDS), ANDROID_ADB_SERVER_PORT='5038')


def adb(*args, check=True, timeout=40):
    return subprocess.run([ADB, '-P', '5038', '-s', 'emulator-5580', *args], env=ENV, capture_output=True, check=check, timeout=timeout)


def tree():
    adb('shell', 'uiautomator', 'dump', '/sdcard/studio-review.xml')
    data = adb('exec-out', 'cat', '/sdcard/studio-review.xml').stdout
    return ET.fromstring(data)


def wait_for_app():
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        root = tree()
        if any(node.attrib.get('text') == 'THE OPEN FRAME' for node in root.iter('node')):
            # The accessibility tree can appear while Android is still removing
            # the splash surface. Let it finish before a capture or key event.
            time.sleep(3)
            return
        time.sleep(1)
    raise AssertionError('The gallery did not finish opening.')


def tap_text(text, max_scrolls=7):
    for _ in range(max_scrolls):
        root = tree()
        for node in root.iter('node'):
            if text in node.attrib.get('text', '') or text in node.attrib.get('content-desc', ''):
                x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.attrib['bounds']))
                if x2 > x1 and y2 > y1:
                    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
                    time.sleep(1)
                    return
        adb('shell', 'input', 'swipe', '560', '630', '560', '230', '400')
        time.sleep(.8)
    screenshot('android-failure.png')
    (SUPPORT / 'failure.xml').write_bytes(ET.tostring(root))
    raise AssertionError(f'Could not find {text}')


def screenshot(name):
    (SHOTS / name).write_bytes(adb('exec-out', 'screencap', '-p').stdout)


def main():
    AVD.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(exist_ok=True)
    (AVDS / 'studio-review.ini').write_text(f'avd.ini.encoding=UTF-8\npath={AVD}\ntarget=android-35\n')
    (AVD / 'config.ini').write_text('\n'.join([
        'avd.ini.encoding=UTF-8', 'avd.id=studio-review', 'avd.name=studio-review', 'abi.type=x86_64',
        'hw.cpu.arch=x86_64', 'hw.cpu.ncore=4', 'hw.ramSize=2048', 'hw.keyboard=yes', 'hw.mainKeys=no',
        'hw.lcd.width=720', 'hw.lcd.height=720', 'hw.lcd.density=240', 'hw.gpu.enabled=yes', 'hw.gpu.mode=swiftshader_indirect',
        'hw.audioInput=no', 'hw.audioOutput=no', 'hw.camera.back=none', 'hw.camera.front=none',
        'disk.dataPartition.size=2G', 'fastboot.forceColdBoot=yes', 'fastboot.forceFastBoot=no',
        'image.sysdir.1=system-images/android-35/google_apis/x86_64/', 'tag.id=google_apis', 'target=android-35',
    ]) + '\n')
    subprocess.run([ADB, '-P', '5038', 'start-server'], env=ENV, check=True, timeout=30)
    log = (ROOT / 'review/android-emulator.log').open('w')
    emulator = subprocess.Popen([str(SDK / 'emulator/emulator'), '-avd', 'studio-review', '-port', '5580',
        '-no-window', '-no-audio', '-no-boot-anim', '-no-snapshot', '-no-metrics', '-gpu', 'swiftshader_indirect',
        '-accel', 'auto'], env=ENV, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 420
        while time.monotonic() < deadline:
            if emulator.poll() is not None:
                raise RuntimeError('Emulator exited. See review/android-emulator.log.')
            result = adb('shell', 'getprop', 'sys.boot_completed', check=False, timeout=15)
            if result.stdout.strip() == b'1':
                break
            time.sleep(3)
        else:
            raise RuntimeError('Emulator did not finish booting within seven minutes.')
        print('Disposable emulator booted.', flush=True)
        for setting in ['window_animation_scale', 'transition_animation_scale', 'animator_duration_scale']:
            adb('shell', 'settings', 'put', 'global', setting, '0')
        apk = ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk'
        adb('install', '-r', str(apk), timeout=90)
        adb('shell', 'pm', 'clear', 'com.chuatzeyee.tylendar.studio')
        adb('shell', 'settings', 'put', 'system', 'font_scale', '1.0')
        adb('shell', 'wm', 'size', '720x1280')
        adb('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
        adb('shell', 'input', 'keyevent', 'KEYCODE_MENU')
        adb('shell', 'am', 'start', '-W', '-n', 'com.chuatzeyee.tylendar.studio/com.chuatzeyee.tylendar.MainActivity')
        wait_for_app()
        root = tree()
        assert any('Tylendar' in node.attrib.get('text', '') for node in root.iter('node'))
        screenshot('android-portrait.png')
        (ROOT / 'docs/screenshots/app.png').write_bytes((SHOTS / 'android-portrait.png').read_bytes())
        adb('shell', 'am', 'force-stop', 'com.chuatzeyee.tylendar.studio')
        adb('shell', 'wm', 'size', '720x720')
        adb('shell', 'am', 'start', '-W', '-n', 'com.chuatzeyee.tylendar.studio/com.chuatzeyee.tylendar.MainActivity')
        wait_for_app()
        screenshot('android-square.png')
        adb('shell', 'input', 'keyevent', 'KEYCODE_P')
        time.sleep(2)
        tap_text('Try on the demo frame')
        tap_text('Read today’s poem')
        screenshot('android-poem.png')
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        adb('shell', 'am', 'force-stop', 'com.chuatzeyee.tylendar.studio')
        adb('shell', 'wm', 'size', '720x1280')
        adb('shell', 'settings', 'put', 'system', 'font_scale', '1.5')
        adb('shell', 'am', 'start', '-W', '-n', 'com.chuatzeyee.tylendar.studio/com.chuatzeyee.tylendar.MainActivity')
        wait_for_app()
        screenshot('android-portrait-large-text.png')
        tap_text('Demo collection')
        screenshot('android-connection-large-text.png')
        logs = adb('logcat', '-d', '-s', 'AndroidRuntime:E').stdout.decode(errors='replace')
        assert 'FATAL EXCEPTION' not in logs, logs
        print('PASS: isolated installation, square layout, hardware-key browsing, demo apply, poem dialog, portrait layout, 150% text, connection dialog, and no runtime crashes.', flush=True)
    finally:
        adb('emu', 'kill', check=False, timeout=10)
        try: emulator.wait(timeout=20)
        except subprocess.TimeoutExpired: emulator.terminate()
        subprocess.run([ADB, '-P', '5038', 'kill-server'], env=ENV, capture_output=True, timeout=10)
        log.close()


if __name__ == '__main__':
    main()
