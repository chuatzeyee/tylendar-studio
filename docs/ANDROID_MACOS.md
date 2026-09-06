# Building Tylendar Studio on macOS

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
git clone https://github.com/chuatzeyee/tylendar-studio.git
cd tylendar-studio
```

Already cloned? Just `git pull`.

## 3. First launch of Android Studio

Open Android Studio once before opening the project. A setup wizard runs on
first launch:

1. Pick the Standard install type.
2. Accept the license agreements when prompted.
3. Let it download the SDK. It lands in `~/Library/Android/sdk`.

Then File > Open and select the `tylendar-studio/android` folder. Select the
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
cd tylendar-studio/android
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

## 6. First run and connection

The app opens in a local demo with ten prints. Browse, change options, read
poems, and try a selection without signing in.

To control a frame, tap **Demo collection** and enter the GitHub repository
that renders it, in `owner/repository` format. Create a fine-grained token
at <https://github.com/settings/personal-access-tokens/new>, restricted to
that repository, with Contents and Actions read/write access. Paste the
token and choose **Connect frame**.

Connection validation reads repository data. The app encrypts a validated
token with Android Keystore and excludes it from backups. A failed save
keeps the draft available to retry.

## 7. Using it

- Browse the categories or print cards, then adjust the selected print's
  options. **Apply to frame** saves the draft together in one commit.
  **Discard changes** restores the saved selection.
- **Read today’s poem in English** opens the bundled English reading.
- **Render saved settings** requests a new image. On the almanac,
  **Next render only** can force light or dark for that one run.
- **Latest render** shows the generated image. The gallery thumbnails are
  illustrative samples; the app cannot confirm the frame's physical display.
- **Manage the photo rotation** opens the connected repository's web portal.
- The frame fetches the latest image at its next scheduled wake, or when
  restarted with the EN button.
- Keyboard shortcuts: A, P, C, L, W, M, Y, J, O, and F browse the almanac,
  poem, character, landscape, weather, month, year, vocabulary, photos, and
  flora. R renders saved settings. Browsing never applies a draft.

![Tylendar Studio Android gallery](screenshots/app.png)

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
