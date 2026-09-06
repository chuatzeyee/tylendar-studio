# Building the Tylendar Android app on macOS

The app lives in `android/` and is a thin remote control for the frame. It
talks to the GitHub API with a fine grained token you create in step 6; it
contains no secrets and needs no Google account, no Play Console, and no
developer fee. Distribution is plain adb sideload.

Time budget: about 30 minutes, most of it downloads.

## 1. Install the toolchain

```bash
brew install --cask android-studio android-platform-tools
```

This gives you:

- Android Studio, which bundles its own JDK 21 and the Android SDK manager.
  You do not need to install Java separately.
- `adb` on your PATH (from `android-platform-tools`), used to install the
  APK onto the phone.

## 2. Get the code

```bash
git clone https://github.com/chuatzeyee/Tylendar.git
cd Tylendar
```

Already cloned? Just `git pull`.

## 3. First launch of Android Studio

Open Android Studio once before opening the project. A setup wizard runs on
first launch:

1. Pick the Standard install type.
2. Accept the license agreements when prompted.
3. Let it download the SDK. It lands in `~/Library/Android/sdk`.

Then File > Open and select the `Tylendar/android` folder. Select the
`android` folder itself, not the repo root; the repo root is a Python and
firmware project and Studio will not know what to do with it.

Studio writes `android/local.properties` (the SDK path, machine specific,
gitignored) and starts a Gradle sync. The first sync downloads the Android
Gradle Plugin, Compose, and every dependency, so it takes a few minutes.
Every later sync is seconds.

If sync asks to upgrade Gradle or the Android Gradle Plugin, decline. The
project pins Gradle 9.7.1 and AGP 9.3.0 deliberately; the build is verified
against exactly those.

## 4. Build the APK

Either press the Run button in Studio with a device connected (it builds,
installs, and launches in one step, skipping step 5), or build from
Terminal:

```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
cd Tylendar/android
./gradlew :app:assembleDebug
```

The APK lands at:

```
android/app/build/outputs/apk/debug/app-debug.apk
```

A debug APK is signed with an auto generated debug key and installs fine.
No keystore setup is needed until you ever want a release build.

## 5. Sideload to the phone

Enable developer mode on the phone (Unihertz Titan 2, Android 16):

1. Settings > About phone > tap Build number seven times.
2. Settings > System > Developer options > enable USB debugging.

USB install:

```bash
# plug in USB-C, accept the "Allow USB debugging?" prompt on the phone
adb devices        # should list the phone as "device", not "unauthorized"
adb install app/build/outputs/apk/debug/app-debug.apk
```

Wireless install (same WiFi network):

1. Developer options > Wireless debugging > enable it.
2. Tap "Pair device with pairing code". The phone shows an IP:port and a
   six digit code.
3. On the Mac:

```bash
adb pair <pairing-ip:port>      # enter the six digit code
adb connect <ip:port>           # the address shown on the main
                                # Wireless debugging screen, a
                                # different port than pairing
adb install app/build/outputs/apk/debug/app-debug.apk
```

Reinstalling over an existing version: `adb install -r ...`.

Sideloading via adb is exempt from the developer verification requirement
rolling out in Singapore from 2026-09-30, so this path stays free.

## 6. First run: the token

The app opens on a token gate. It needs a fine grained GitHub personal
access token that can write to this repo. The token is entered once, lives
only in the app's on device storage (excluded from all Android backups),
and is never committed anywhere.

1. Tap CREATE A TOKEN in the app, or open
   https://github.com/settings/personal-access-tokens/new
2. Resource owner: you. Repository access: Only select repositories >
   Tylendar.
3. Permissions > Repository permissions:
   - Contents: Read and write (lets the app change page, mode, hotspot)
   - Actions: Read and write (lets the app trigger and watch renders)
4. Generate, copy the `github_pat_...` value, paste it into the app, tap
   UNLOCK.

The app verifies the token can actually write before letting you in, the
same probe the web portal uses. If a permission box was missed, it tells
you which one.

## 7. Using it

- Swipe the carousel to browse the seven pages; the one the frame is
  showing wears a red seal. Tap SET AS FRAME PAGE to commit: the
  preview flips instantly to a committed thumbnail (caption reads
  PREVIEW) and the GitHub render starts. About two minutes later the
  preview swaps to the real freshly rendered frame image (caption
  reads LIVE).
- On the poem page, IN ENGLISH opens the full translation of today's
  poem.
- RENDER NOW re-renders without changing anything, in auto, light, or
  dark.
- The frame itself picks changes up at its next scheduled wake (shown in
  the app), or immediately if you press the EN button on the frame.
- Hardware keyboard shortcuts: A, P, C, L, W, M, Y switch pages, R forces
  a render.

## Troubleshooting

- `adb devices` shows `unauthorized`: look at the phone, accept the USB
  debugging prompt, and check "Always allow".
- `adb devices` shows nothing over USB: try another cable (it must be a
  data cable), and check the phone's USB mode is not "Charging only".
- Gradle sync fails with a JDK error in Terminal: the `JAVA_HOME` export
  in step 4 must point at Studio's bundled JDK; a system Java that is too
  old will fail.
- `INSTALL_FAILED_UPDATE_INCOMPATIBLE` on install: an older build signed
  with a different debug key is on the phone. `adb uninstall
  com.chuatzeyee.tylendar` and install again.
- App says the token is missing a permission: edit the token on GitHub
  (Settings > Developer settings > Personal access tokens > Fine-grained
  tokens), grant the named permission as Read and write, save, and unlock
  again with the same token.
