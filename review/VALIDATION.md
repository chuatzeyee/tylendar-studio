# Tylendar Studio validation

Reviewed on 2026-09-06. All project changes and generated review artifacts are confined to `Tylendar-studio`.

## Interface cleanup

Both clients use **The Open Frame**, an upright 泰曆 seal, a walnut brown preview frame, and **OPEN-SOURCE E-INK GALLERY**. Decorative diagonal arrows and dot separators have been removed. The web masthead no longer includes the date or timezone, and print sequence numbering has been removed.

Web labels are at least 14px and body text is 16px. Android labels are at least 14sp and body text is 16sp. Mobile controls wrap where needed, the print cards have room for their larger labels, and the Android gallery uses one column on narrow screens or with larger system text.

## Completed checks

| Check | Result |
| --- | --- |
| Original project integrity | All 103 original source and asset files match the recorded SHA-256 hashes. No source or assets were added or removed in `../Tylendar`. |
| Portal unit and API tests | 13 passed, 0 failed. |
| Browser integration | Passed demo isolation, filters, previews, draft apply/discard, editions, poems, frame labels, photo add/remove/cancel, invalid-file feedback, read-only connection, grouped save, render association, private image retrieval, failed-save recovery, and disconnect/session clearing. GitHub traffic was intercepted locally. |
| Browser layout | No document overflow at widths 360, 390, 680, 768, 900, 1024, and 1440. Connection dialogs fit at each width. Visible UI text is at least 14px, and the seal has no transform. |
| Browser runtime | No uncaught page errors in the integration checks. Desktop and mobile screenshots were visually inspected. |
| Android build | `assembleDebug` succeeds for `com.chuatzeyee.tylendar.studio`, version `1.1-studio`. |
| Android unit tests | 7 passed, 0 failures, errors, or skips. |
| Android runtime | Passed on an isolated Android 35 emulator with KVM: portrait and square layouts, keyboard browsing, demo apply, poem dialog, 150% system text, connection dialog, and no runtime crashes. |
| Android lint | `lintDebug` succeeds with 0 errors and 22 existing warnings concerning dependency/SDK versions and launcher resources. |
| Documentation | README local file links resolve. The README and macOS Android guide describe the current demo, connection, and draft/apply behavior. |

The native runtime check exposed a keyboard listener attached after its focus target. Moving the listener before the focus target restored hardware-key browsing; the emulator check passes with that correction.

## Screenshots

The README uses newly captured local images:

- `docs/screenshots/portal.png`: desktop web gallery.
- `docs/screenshots/portal-tablet.png`: tablet web gallery.
- `docs/screenshots/portal-mobile.png`: phone web gallery.
- `docs/screenshots/app.png`: native Android portrait gallery.

`review/capture_screenshots.py` also refreshes the desktop, tablet, and two mobile sizes in `review/screenshots/`. The historical `pages-*.png` filenames now contain the current local gallery. They are not captures of the deployed site. Native review captures include portrait, square, poem, large-text portrait, and large-text connection views. Bundled print artwork in `docs/previews/` remains the illustrative content displayed inside the frames.

## Reproduction

Run the web unit tests:

```bash
npm test --prefix portal
```

Serve `portal/` on localhost port 8765, then run these scripts with Python Playwright and Chrome installed:

```bash
python3 -B review/browser_review.py
python3 -B review/capture_screenshots.py
```

`CHROME_BIN` and `PORTAL_URL` can override the capture script's browser path and URL. The default URL is `http://127.0.0.1:8765`.

Build Android from `android/` with the pinned toolchain and an installed SDK:

```bash
./gradlew testDebugUnitTest assembleDebug lintDebug
```

The APK, unit-test report, and lint report are under `android/app/build/`. Runtime captures use `python3 -B review/android_review.py` from the repository root. The script reads `ANDROID_HOME`, creates a dedicated AVD under `.build-support/android-review`, uses ADB port 5038 and emulator port 5580, and shuts down that emulator afterward. It does not target a user device.

Verify the original source snapshot with `python3 -B review/verify_original.py`.

## Limits

These validation runs used the local portal and intercepted GitHub requests. Publishing the cleanup to `main` triggers the **Deploy portal** workflow. Deployment results are recorded in GitHub Actions for [chuatzeyee/tylendar-studio](https://github.com/chuatzeyee/tylendar-studio/actions).

No physical frame was tested. The firmware has no acknowledgement or telemetry, so a successful render cannot confirm that a frame downloaded it. Android credential persistence and private repository requests were not exercised in this demo run; they still need a review with a connected test repository.
