# Tylendar Studio

An isolated redesign of the Tylendar web portal and Android remote. Both open into a local demo with bundled artwork. No credentials or network connection are needed to explore the collection.

The original `../Tylendar` project remains unchanged. Its renderer, firmware, fonts, datasets, and hardware documentation were copied so this folder is self-contained. Git history, caches, old build outputs, and machine configuration were excluded. The firmware and generator code have not been changed.

## What changed

- A shared visual direction: warm paper, botanical green, charcoal frames, seal-red actions, and generous serif titles.
- Ten prints grouped into Daily, Nature, Calendar, and Personal collections, with local previews, enlarged artwork, and a surprise selection.
- The same browse → adjust → apply interaction on web and Android. Browsing, keyboard shortcuts, and option changes produce a draft. Apply saves all changed fields in one commit; discard restores the saved selection.
- Explicit separation between illustrative previews, the latest generated image, and the frame’s next scheduled wake. Neither client claims to know what is physically on the frame.
- Configurable GitHub owner/repository; main remains the supported renderer branch.
- Read-only connection validation, clear request failures, bounded network calls, settings validation, conflict retries, and preservation of unrelated settings.
- Render tracking tied to the settings commit SHA. Manual dispatch uses a numeric run baseline and workflow event filter.
- The original one-time light/dark almanac render overrides are retained separately from persistent settings.
- Local English poem readings, automatic weekend almanac previews, and Singapore-aware refresh timing.
- Responsive web layout, native scrolling layouts, larger controls, keyboard navigation, semantic labels, browser reduced-motion support, and error messages that retain drafts.
- Portal photo upload, resizing, removal confirmation, invalid-file feedback, and local demo photos. Native photo management opens the connected repository’s web portal.
- Authenticated image retrieval so private repository previews do not rely on unauthenticated raw URLs.
- Browser credentials are stored for the tab’s session. Android credentials are encrypted using Android Keystore and excluded from backups.
- Android app identity is `com.chuatzeyee.tylendar.studio`, label **Tylendar Studio**, version **1.1-studio**. It can coexist with the original app.

## Open the web portal

Live portal: **https://chuatzeyee.github.io/tylendar-studio/**

Source repository: **https://github.com/chuatzeyee/tylendar-studio**

The portal starts in demo mode. To run it locally, from this directory:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory portal
```

Open **http://127.0.0.1:8765**. No JavaScript dependencies or build step are required. Serving over HTTP is necessary for ES modules and local dataset loading.

The **Deploy portal** GitHub Actions workflow tests the portal and publishes the self-contained `portal` directory to GitHub Pages. Changes to `portal/**` or the deployment workflow on `main` deploy automatically; the workflow can also be run manually. Pages uses **GitHub Actions** as its build source.

## Android build

The reviewed APK is `android/app/build/outputs/apk/debug/app-debug.apk`.

Open `android` in Android Studio, configure the SDK/JDK as described in the existing toolchain documentation, and run:

```bash
./gradlew testDebugUnitTest assembleDebug lintDebug
```

The current workspace uses the installed JDK and SDK and a private dependency cache under `.build-support`. This directory is local build support and must not be committed. `android/local.properties` is machine-specific.

Android hardware keys A/P/C/L/W/M/Y/J/O/F browse the corresponding prints without saving. R renders the saved settings. Applying a draft always requires the explicit apply button.

## Connect a frame

Use the connection button and enter the repository containing the generator and `render.yml`, plus a fine-grained GitHub token with Contents and Actions read/write access. The connection uses GET requests to validate access; actual write permissions are checked when GitHub handles a save or render request.

Connecting replaces the local demo draft with repository settings. Applying a draft writes to the selected repository. Photo uploads and removals in the portal take effect immediately. Demo photos are held in memory and disappear when the page is closed.

Browser integration tests intercept GitHub requests locally. Publishing this repository and its portal does not connect a physical frame. To test live settings and rendering in this copy, connect to `chuatzeyee/tylendar-studio`; to use a physical frame, connect the repository its firmware actually downloads from. No APK has been installed on a user device.

## Review and validation

- `review/REVIEW.md`: original findings, resolutions, and remaining limits.
- `review/VALIDATION.md`: final test results and environmental limitations.
- `review/screenshots/`: desktop, tablet, and phone portal captures.
- `review/browser_review.py`: browser regression checks with mocked GitHub traffic.
- `review/android_review.py`: optional disposable-emulator check; uses its own AVD and ADB port.
- `review/verify_original.py`: verifies original source/assets against the recorded hashes.

Run the dependency-free portal tests with `npm test` from `portal`.
