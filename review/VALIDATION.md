# Validation — Tylendar Studio

Date: 2026-09-06. All source changes and project artifacts are in `Tylendar-studio`.

## Passed

| Check | Result |
| --- | --- |
| Original project integrity | All **103** original source and asset files match their copy-time SHA-256 hashes. No source/assets added or removed. Git history, caches, generated builds, and machine configuration are excluded from the source snapshot. |
| Portal unit/API tests | **13 passed, 0 failed**, using Node's built-in test runner. |
| Browser integration | Headless Chrome passes demo isolation, collection filters, draft changes, grouped apply, discard, English poems, edition selection, label validation, photo add/remove/cancel, invalid-file feedback, GET-only connection validation, a one-time dark render override, authenticated image loading, settings preservation, exact-commit render association, failed-save recovery, and disconnect/session clearing. |
| Browser layout | No document-level horizontal overflow at **360×800**, **390×844**, **900×900**, and **1440×1100**. Desktop and phone screenshots were visually inspected. Reduced-motion mode enabled during checks. |
| Browser errors | No uncaught page errors in the exercised flows. GitHub traffic was intercepted locally; no real writes or workflow dispatches occurred. |
| Android compile/APK | `assembleDebug` succeeds. Package: **com.chuatzeyee.tylendar.studio**, version **1.1-studio**. |
| Android unit tests | **7 passed, 0 failures/errors/skips**. Covers Singapore time boundaries, weekend/dark previews, next-wake rollover, matching render commits, settings patch preservation, invalid JSON, labels, and repository paths. |
| Android lint | `lintDebug` succeeds with **0 errors and 22 warnings**. Warnings concern inherited target/dependency versions and launcher resources; they are recorded in the generated lint report. |

## Runtime limitation

Android runtime and visual testing could not be completed. This environment has no `/dev/kvm`. A separate software emulator was created under `.build-support/android-review`, with ADB port 5038 and emulator port 5580; it did not finish booting within seven minutes. It was stopped and the isolated ADB server was shut down. No APK was installed on a user device.

The Android layout, encrypted credential storage, hardware-key interactions, and private-preview display therefore have compile/static validation but have not been exercised on a running Android device in this session. The next device review should cover a square screen, a portrait screen, 150% text, soft-keyboard dialogs, reconnection after process restart, and Keystore persistence.

No live frame, production GitHub workflow, or deployment was tested. A frame acknowledgement cannot be tested because the firmware provides no telemetry.

## Artifacts

- `screenshots/portal-desktop.png`
- `screenshots/portal-tablet.png`
- `screenshots/portal-mobile.png`
- `screenshots/portal-small-mobile.png`
- `../android/app/build/outputs/apk/debug/app-debug.apk`
- `../android/app/build/reports/tests/testDebugUnitTest/index.html`
- `../android/app/build/reports/lint-results-debug.html`
- `change-inventory.json`
- `android-emulator.log` — software-emulator attempt

## Reproduction

Portal tests: `npm test` from `portal`.

Original integrity: `python3 -B review/verify_original.py` from the copy root.

Browser tests: serve `portal` on localhost port 8765, then run `python3 -B review/browser_review.py`. The script uses the installed Chrome binary, intercepts GitHub traffic, and saves screenshots inside the copy.

Android: `./gradlew testDebugUnitTest assembleDebug lintDebug` from `android`, using the project's pinned toolchain and an installed SDK. This workspace's successful runs used the installed JDK/Gradle under `/home/dmgadmin/android-build` and a private Gradle cache under `.build-support/gradle`.
