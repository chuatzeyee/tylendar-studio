# Flashing the ESP32-L from a MacBook Pro

This guide takes you from a fresh MacBook to a running Tylendar. Every
step is written for the Good Display ESP32-L demo board (the one bundled
with the GDEM102F91 kit). Total time is about 20 minutes, most of it
waiting for the ESP32 toolchain download.

## What you need

- The Good Display ESP32-L board
- A USB-C cable that carries data. Charge only cables are the most
  common cause of "no port appears". If in doubt, use the cable that
  came with a phone or SSD, not a cheap charging cable.
- The Arduino IDE 2.x from https://www.arduino.cc/en/software
- This repository cloned or downloaded to your Mac

You do not need the display connected to flash. Flash first, test the
serial output, then assemble.

## Step 1: Connect the board and find the port

1. Plug the board into the MacBook with the USB-C cable.
2. On Apple Silicon Macs, macOS may show a popup asking to allow the
   accessory to connect. Click Allow. If you dismissed it, go to
   System Settings, Privacy and Security, and set "Allow accessories
   to connect" to "Ask for New Accessories", then replug.
3. Open Terminal and run:

   ```
   ls /dev/cu.*
   ```

4. Look for a new entry such as `/dev/cu.usbserial-1420` or
   `/dev/cu.wchusbserial1420`. That is your board. The ESP32-L uses a
   CH340 USB chip, which macOS has supported natively since Mojave, so
   for most Macs no driver install is needed.

If no `usbserial` port appears:

- Try another cable first. Then another USB port.
- Check the board shows a power LED when plugged in.
- As a last resort, install the vendor driver from
  https://github.com/WCHSoftGroup/ch34xser_macos and follow its README,
  including approving the system extension in Privacy and Security.
  After a reboot the port appears as `/dev/cu.wchusbserial*`.

Always use the `cu.` entry, not the `tty.` entry with the same name.

## Step 2: Install the Arduino IDE and the ESP32 core

1. Install and open Arduino IDE 2.x.
2. Open Settings (Cmd+Comma). In "Additional boards manager URLs"
   paste:

   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```

3. Open the Boards Manager (second icon in the left sidebar), search
   for `esp32`, and install "esp32 by Espressif Systems". This is a
   large download, let it finish completely.

## Step 3: Open the sketch and configure it

1. In Terminal, create your local config from the template. It is
   gitignored, so your WiFi passwords never end up in git:

   ```
   cp firmware/Tylendar/config.example.h firmware/Tylendar/config.h
   ```

2. In the IDE choose File, Open, and select
   `firmware/Tylendar/Tylendar.ino` from this repo. The IDE opens the
   whole folder including the driver files, you will see tabs for
   `config.h`, `epd_gdem102f91.h`, and `epd_gdem102f91.cpp`.
3. Click the `config.h` tab and fill in the WiFi list. The board tries
   each network in order at every wake, so list every place the frame
   lives; delete the second line if there is only one:

   ```
   #define WIFI_NETWORKS \
     { \
       {"YOUR_HOME_SSID", "YOUR_HOME_PASSWORD"}, \
       {"YOUR_WORK_SSID", "YOUR_WORK_PASSWORD"}, \
     }
   ```

   The ESP32 only supports 2.4 GHz WiFi. If your router runs a combined
   2.4/5 GHz network with one name, that is fine, the ESP32 will find
   the 2.4 GHz side. Corporate login networks (802.1X) and captive
   portals will not work; ask for the guest or IoT network instead.
4. If you forked the repo, also change `IMAGE_URL` to point at your
   fork. If you are using chuatzeyee/Tylendar directly, leave it.

## Step 4: Board settings

In the Tools menu set:

| Setting | Value |
| --- | --- |
| Board | "WEMOS LOLIN32" (under esp32) |
| Upload Speed | 460800 |
| Port | your `/dev/cu.usbserial*` port |

Two notes:

- If you cannot find WEMOS LOLIN32, "ESP32 Dev Module" with default
  settings also works for this board.
- Keep upload speed at 460800. The Apple native CH340 driver does not
  support 921600 and uploads at that speed fail or corrupt. 460800 is
  the fastest reliable rate.

## Step 5: Upload

1. Click the Upload arrow (or Cmd+U).
2. The IDE compiles for a minute or two, then prints
   `Connecting........` and a progress percentage. The ESP32-L has an
   auto reset circuit, so it should enter the bootloader by itself.
3. Success looks like `Hash of data verified` then
   `Hard resetting via RTS pin`.

If it hangs at `Connecting........_____....._____`:

1. Hold the BOOT button on the board (labelled BOOT or IO0).
2. While holding it, click Upload again.
3. Keep holding until the progress percentage starts, then release.

If it still fails, drop Upload Speed to 115200 and retry, and confirm
nothing else (a serial monitor, another IDE window) has the port open.

## Step 6: Verify over serial

1. Open the Serial Monitor (magnifier icon, top right) and set the
   baud rate to 115200.
2. Press the EN (reset) button on the board.
3. You should see the sketch log its progress: joining WiFi, syncing
   time over NTP, downloading the image, then either driving the panel
   (if connected) or reporting a display failure, and finally the deep
   sleep time until the next scheduled wake (00:20, 07:30, 13:00, or
   19:00).

If the panel is not connected yet, a display init failure at this stage
is expected and harmless. The important part is that WiFi joins and the
download reports 153600 bytes.

## Step 7: Reflashing later

The board wakes for under a minute at a time, four times a day, and
spends the rest in deep sleep, where the USB serial port still enumerates but the chip will not
respond to auto reset reliably. To reflash a sleeping board, use the
BOOT button method from step 5, it works in any state.

## Troubleshooting quick table

| Symptom | Fix |
| --- | --- |
| No /dev/cu.usbserial port | Data capable cable, allow accessory, WCH driver |
| Upload fails at 921600 | Use 460800 with the native macOS driver |
| Hangs at Connecting... | Hold BOOT while upload starts |
| Port busy error | Close serial monitors and other IDE windows |
| Garbage in serial monitor | Set monitor baud to 115200 |
| WiFi never joins | 2.4 GHz only, check SSID and password in config.h |
| Download size mismatch | Run the render workflow once so tylendar.bin exists |
