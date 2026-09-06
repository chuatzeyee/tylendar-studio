# Tylendar Android app: research findings and plan

Research date: 2026-08-30. Compiled from an 11-agent research pass (5
research lenses, 5 independent fact checkers, 1 completeness critic).
Every load-bearing claim below (prices, dates, policy rules, versions,
hardware specs) was verified by a second agent against primary sources.

Goal, as revised: a native Android app that replaces the GitHub Pages
portal (`portal/index.html`) as the remote control for the frame. The
app runs on the owner's UniHertz Titan 2 and must look and feel right
on its 1:1 square screen. An earlier, larger study of a full native
renderer app (re-implementing all 7 pages in Compose) was completed
before the goal was narrowed; its findings are preserved in Appendix A
because the groundwork (device, accounts, toolchain, design language)
carries over and the renderer remains a possible future direction.

---

## 1. Verdict

Straightforward and cheap. The portal is a single static HTML page that
talks to exactly two GitHub REST endpoints with a fine grained PAT; a
native app is a thin, well-dressed client around the same two calls.

- Effort: roughly 15 to 25 hours. One weekend for a working remote
  (token gate, live preview, page/mode/hotspot, force render), a second
  for the home screen widget and polish.
- Cost: $0. Installing your own APK over USB (adb) requires no
  developer account of any kind and is permanently exempt from Google's
  new developer verification regime (section 4).
- No server, no backend, no new secrets. The app reuses the portal's
  fine grained PAT model unchanged.

## 2. What the app replaces: portal feature inventory

Enumerated from `portal/index.html` (916 lines). Parity checklist for
the app:

| Feature | How the portal does it | Notes for the app |
| --- | --- | --- |
| Token gate | PAT pasted once, kept in localStorage, page blank until validated | App: paste once into a settings sheet, store encrypted (section 6.3) |
| Token validation | `GET /repos/{owner}/{repo}`, require `permissions.push` | Same |
| Scope probe | Dry-run `PUT` on settings.json with a bogus sha (409/422 expected) and a dispatch with a bogus ref, so both write scopes are proven without writing | Replicate exactly; it is the only reliable check for fine grained PATs |
| Live preview | `raw.githubusercontent.com/.../output/preview.png` with a cache-busting query | Coil image, pull-to-refresh, also the widget image |
| Render status | `GET /actions/workflows/render.yml/runs?per_page=1` plus latest commits | Same, poll after dispatch until the run completes |
| Next wake line | Computed from the fixed ESP32 wake times 00:20, 07:30, 13:00, 19:00 SGT | Same computation, plus a countdown |
| Read settings | `GET /contents/generator/settings.json?ref=main` (content + sha) | Same |
| Change page (7 pages) | `PUT /contents/generator/settings.json`, rereading the sha first; the render bot commits 4x a day so a racing PUT gets 409 and retries | Keep the reread-sha-and-retry loop verbatim |
| Change mode (auto/light/dark) | Same PUT | Same |
| Change hotspot label | Same PUT; ASCII only, the bundled Latin font on the frame has no CJK | Validate ASCII in the text field |
| Force render | `POST /actions/workflows/render.yml/dispatches` with input `mode` (auto/light/dark, that one render only) | Same |
| Rate limit handling | Reads `x-ratelimit-remaining` | Authenticated limit is 5,000 req/hour, ample; still surface the error |

Headers on every call: `Accept: application/vnd.github+json`,
`X-GitHub-Api-Version: 2022-11-28`, `Authorization: Bearer <PAT>`.

What the app cannot replace: the physical EN button on the board is
still the only way to make the frame fetch immediately. The app, like
the portal, changes what the frame will show at its next wake.

A settings commit triggers a re-render automatically (render.yml runs
on push to `generator/**`), done in about two minutes; the app should
show that pipeline state (committed, rendering, rendered, next wake)
as one clear status line, the same story the portal tells.

## 3. Target device: UniHertz Titan 2 (verified)

| Property | Value |
| --- | --- |
| Main display | 4.5 inch square IPS LCD, 1440x1440 (1:1), about 453 ppi, 60 Hz (early 120 Hz reports were wrong; the Elite is the high refresh model) |
| Window in dp | Roughly 480x480dp at density 3, but the shipped density is unverified: check with `adb shell wm density`. 480dp sits exactly on the Compact/Medium WindowSizeClass boundary, so do not branch on size classes; branch on measured aspect if needed |
| Rear display | 2 inch, 410x502 px. No public third-party API found; Unihertz documents only wallpapers, watch faces, and whole apps via their SubDisplayLauncher |
| Keyboard | Four-row backlit physical QWERTY with a capacitive touch surface (Scroll Assistant / Cursor Assistant inject scroll events; exact event behavior untested, needs the real device) |
| OS | Shipped Android 15; Android 16 OTA rolled out 2026-02-26; Android 17 promised. Google Play certified |
| SoC / RAM | Dimensity 7300 (4x A78 + 4x A55), 12GB / 512GB |
| Price | $489.99 on unihertz.com (2026-08), $400 MSRP at the Oct 2025 launch |
| Quirk | Per-app "App Compatibility Mode" (Settings > Intelligent Assistant) letterboxes misbehaving apps; a correctly built app never needs it |

Layout consequences for this app: no `android:screenOrientation`
lock needed (the remote is a simple scrolling column that works at any
aspect), edge-to-edge insets still apply (status bar exists even with
a hardware keyboard), and every control should be reachable by
hardware keys (section 7.4).

## 4. Accounts and money (verified against Google's own pages)

Two separate Google systems in 2026, do not confuse them:

1. Google Play Console (play.google.com/console): only for Play Store
   distribution. US$25 one time.
2. Android Developer Console (android.google.com/developerconsole):
   the new developer verification regime for apps installed outside
   Play. Has a free tier.

Singapore specifics: verification enforcement starts 2026-09-30 in
Singapore (also Brazil, Indonesia, Thailand) but at launch applies only
to 7 participating app stores. Direct APK sideloading is officially
"not yet affected" until the global rollout in 2027. ADB installs are
permanently exempt by explicit policy.

Options, cheapest first:

- Path A, adb sideload, $0, recommended: no account at all. Build the
  APK, `adb install -r` to the Titan 2. Permanently exempt from
  verification. Updates over USB or wireless adb.
- Path B, Limited Distribution tier (Android Developer Console), $0:
  needs a Google Account with 2-step verification and a linked Google
  payments profile, but no fee and no government ID. Up to 20 enrolled
  devices. The backstop for cable-free installs after 2027.
- Path C, full ADC verification, $25 one time: unlimited public direct
  distribution (GitHub Releases etc). Government ID plus registering
  the package name AND signing key. Google's warning, quoted: "If you
  lose your signing key you won't be able to register your packages."
  Back up the keystore.
- Path D, Google Play Console, $25 one time: government ID + payment
  card verification (prepaid rejected, fee non-refundable on failed
  verification); personal accounts created after 2023-11-13 must run a
  closed test with 12+ testers opted in continuously for 14 days
  before production access; developer name and email are public; new
  Play apps upload AAB with Play App Signing; targetSdk 36 required
  from 2026-08-31.

Free wider-sharing channels without Play: GitHub Releases + Obtainium
(silent auto-updates need Android 12+, the Titan 2 qualifies), or
F-Droid (FLOSS only, they build and sign it themselves).

Recommendation: Path A now, enroll Path B whenever convenient, ignore
C and D unless the app grows an audience.

## 5. macOS toolchain: zero to APK (verified current, 2026-08)

Apple Silicon assumed. Disk budget 20 to 25 GB.

### 5.1 Install

```bash
# Homebrew, if missing
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

brew install --cask android-studio          # Quail 3 Patch 1, 2026.1.3
brew install --cask android-platform-tools  # adb 37.0.1 in Terminal
```

No separate JDK: Android Studio bundles JetBrains Runtime 21.

### 5.2 Environment (~/.zshrc)

```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"
```

### 5.3 First launch

Run the setup wizard (Standard). Then accept licenses for command line
builds too, or the first `./gradlew` run fails:

```bash
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses
```

If cmdline-tools is missing: Settings > Languages & Frameworks >
Android SDK > SDK Tools > check "Android SDK Command-line Tools".

### 5.4 Pinned version stack

The research surfaced a version conflict between agents; this is the
single pinned stack that compiles:

| Component | Version | Why |
| --- | --- | --- |
| Android Studio | Quail 3 Patch 1 (2026.1.3) | Current stable |
| compileSdk | 37 (Android 17, stable 2026-06-16) | Compose BOM 2026.08.00 requires it |
| targetSdk | 36 | Play's 2026-08-31 floor; safe on the Titan 2's Android 16 |
| minSdk | 29 | Nothing older matters here |
| AGP | 9.3.0 | BOM 2026.08.00 needs AGP >= 9.2.0 |
| Gradle | 9.7.1 | AGP 9.3 needs >= 9.5.0 |
| Kotlin | 2.2.x + org.jetbrains.kotlin.plugin.compose | Current |
| Compose BOM | androidx.compose:compose-bom:2026.08.00 | Compose 1.12 |

New Project > Empty Activity (Compose) > Kotlin DSL > minSdk 29, then
set the versions above in `gradle/libs.versions.toml`.

### 5.5 Build and install

```bash
./gradlew assembleDebug
# app/build/outputs/apk/debug/app-debug.apk
```

Phone: Settings > About phone > tap Build number 7 times > Developer
options > USB debugging. Then:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Wireless: Developer options > Wireless debugging > Pair device with
pairing code, then on the Mac `adb pair IP:PAIRPORT` (6 digit code),
`adb connect IP:CONNECTPORT` (two different ports, both shown on the
phone), then install as usual.

### 5.6 Square-screen emulator

Device Manager > + > New Hardware Profile: 4.5 inch, 1440x1440.
System image: API 36 (Android 16) arm64-v8a, native on Apple Silicon
via Hypervisor.framework. The emulator cannot simulate the physical
keyboard or the capacitive scroll surface; keyboard behavior needs the
real device. Also test on a stock 20:9 profile (any Pixel).

### 5.7 Release signing and keystore hygiene

```bash
mkdir -p ~/keystores
keytool -genkeypair -v -keystore ~/keystores/tylendar-release.jks \
  -alias tylendar -keyalg RSA -keysize 2048 -validity 10000
```

`keystore.properties` in the project root, wired into signingConfigs.
This repo is public, so before the app module's first commit:

- `*.jks` and `keystore.properties` go into `.gitignore`.
- Back up the keystore (a lost key permanently blocks Path C package
  registration later).
- Never echo passwords into CI logs.

`./gradlew assembleRelease` produces the sideload APK. Optional later:
a GitHub Actions job signs releases (keystore as a base64 secret) and
attaches APKs to GitHub Releases, pairing with Obtainium for updates.

## 6. App architecture

### 6.1 Stack

Single module, single activity, Kotlin + Jetpack Compose. Libraries:

| Library | Role |
| --- | --- |
| androidx.compose BOM 2026.08.00 | UI |
| com.squareup.okhttp3:okhttp 5.x | GitHub API calls (default UA is fine everywhere) |
| org.jetbrains.kotlinx:kotlinx-serialization-json 1.9.x | API payloads, settings.json |
| io.coil-kt.coil3:coil-compose 3.x | preview.png |
| androidx.datastore:datastore-preferences 1.1.x | Settings and token storage |
| androidx.glance:glance-appwidget 1.1.1 | Home screen widget |
| androidx.work:work-runtime-ktx 2.10.x | Widget refresh |

No ViewModel framework ceremony needed beyond one screen-level state
holder; the whole app is four API calls and a poll loop.

### 6.2 GitHub client behavior (mirror the portal exactly)

- Reread `GET /contents/generator/settings.json?ref=main` immediately
  before every `PUT` to get a fresh sha; on 409 (the render bot pushed
  mid-flight) reread and retry, bounded at 3 attempts like render.yml's
  own push loop.
- Preserve unknown keys in settings.json when editing (parse, modify
  one field, re-serialize all fields).
- After a dispatch or settings commit, poll
  `/actions/workflows/render.yml/runs?per_page=1` every few seconds
  until `status == completed`, then bust the preview image cache.
- Preview URL: `https://raw.githubusercontent.com/chuatzeyee/Tylendar/main/output/preview.png?t=<millis>`
  (raw.githubusercontent caching makes the cache-buster mandatory).
- Token validation on entry: `GET /repos/{owner}/{repo}` requiring
  `permissions.push`, then the portal's probe trick, a real PUT with
  `sha: "000...0"` and a real dispatch with a nonexistent ref; GitHub
  refuses the action (409/422) only after the permission check passed,
  so both write scopes are proven with zero side effects. This is the
  only reliable scope check for fine grained PATs.

### 6.3 Token security (stricter than the portal)

The PAT is a write credential to this repo. Rules for the app:

- Entered at runtime only. Never in source, BuildConfig, or any
  flavor of the APK (strings/apktool extraction is trivial).
- Stored in Preferences DataStore, excluded from Auto Backup and
  device transfer via `android:dataExtractionRules` (otherwise Google
  backs the token up to the cloud).
- Never logged (no OkHttp logging interceptor in release builds),
  never passed as WorkManager input data (WorkManager persists inputs
  unencrypted in its database; the widget worker reads the token from
  DataStore itself).
- Fine grained PATs expire; on any 401, drop to the token sheet with
  a "token expired or revoked, paste a new one" message rather than a
  generic error.
- The same rule applies to the Google Calendar secret ICS address if
  the app ever grows calendar features: it stays in GitHub Actions
  secrets, never in the app.

### 6.4 Widget

Glance widget showing the live frame: fetch preview.png via a
WorkManager worker (not Coil composables; Glance needs a Bitmap
through ImageProvider), caption with page name and next wake. Refresh
scheduled a few minutes after each render cron lands (00:05, 07:05,
12:35, 18:35 SGT, so fetch around :15 past), plus refresh on widget
tap. WorkManager has a 15 minute periodic floor and Doze defers exact
times; for a wall calendar mirror, minute-level drift is fine, so no
exact-alarm permissions. Glance cannot use custom fonts; the caption
uses system fonts, the image carries the aesthetic.

### 6.5 Effort

| Phase | Scope | Estimate |
| --- | --- | --- |
| 1 | Token gate + storage, home screen (preview, status, next wake), page picker, mode, hotspot, force render | 12-16 h |
| 2 | Glance widget + WorkManager refresh, keyboard shortcuts, polish, app icon | 6-10 h |

## 7. Design

The app should read as a companion object to the frame: same paper,
same ink, same restraint. It is a remote control, so clarity beats
cleverness everywhere.

### 7.1 Language

- Palette, exactly the frame's four: ink #0C0C0C, paper #FFFFFF, red
  #BA2029, yellow #ECB70F (sparingly; small yellow on white is low
  contrast on LCD, use it only as the accent tag it is on the frame).
- Type: Fraunces variable (OFL, 360KB, opsz 9-144) for everything:
  opsz 144 for the big elements, opsz 9 with +0.08em tracking for
  letterspaced caps labels (NEXT WAKE, RENDERING, the portal's visual
  vocabulary). No CJK font needed in phase 1: every string the app
  shows is Latin (page names, status) and the hotspot field is ASCII
  by rule. That keeps the APK tiny (~12-15MB).
- Chromeless: no app bar, no bottom nav. Material 3 only for the
  bottom sheets (token, hotspot editor), retinted paper/ink/red with
  square corners and hairline (1.5dp) outlines. No ripple; a brief
  ink-dip pressed state.
- Hairline rules to separate sections, exactly like the rendered
  pages. Generous margins (the frame's 52/640 proportion, about 8% of
  width).

### 7.2 Screens (it is really one screen plus sheets)

Home, a single scrolling column:

1. The frame: preview.png inside a thin ink border with a wide paper
   mat, a miniature of the RODALM on the wall. Pull down to refresh.
   Off-today/stale state shows a letterspaced UPDATED 12:35 caption.
2. Status line: one sentence, letterspaced caps, exactly like the
   portal: RENDERED, NEXT WAKE 19:00 (IN 2H 14M), or RENDERING with a
   quiet indeterminate hairline. Mention of the EN button when a
   change is pending: "or press EN on the frame".
3. Page picker: a grid of the 7 pages using the committed thumbnails
   in `docs/previews/` (fetched from raw.githubusercontent, cached) so
   picking a page is visual, not a name list. Current page carries a
   small red seal chip. Tap commits immediately (portal behavior).
4. Mode row: AUTO / LIGHT / DARK as three letterspaced text buttons,
   current one in red.
5. Hotspot row: current label, tap opens an editor sheet (ASCII only,
   with the reason stated inline: the frame's Latin font has no CJK).
6. Force render: one full-width outlined button, with an
   auto/light/dark choice, then live run status until complete.
7. Footer: token chip (masked), tap to replace or remove; repo link.

First run: the token gate is the only onboarding, one paste + the two
inline steps to create a fine grained token (Contents and Actions,
read and write, this repo only), copied from the portal's copy.

### 7.3 Square screen behavior

The column layout works at 1:1 naturally. Only refinement: on aspect
ratios below about 1.2 (Titan 2), place the preview and the status
side by side at the top so the fold shows preview + status + page grid
without scrolling. No WindowSizeClass; one measured-aspect branch.

### 7.4 Titan 2 keyboard

- Arrow keys move focus (Compose default focus traversal, verify with
  the hardware).
- Enter activates.
- Letter shortcuts A/P/C/L/W/M/Y jump straight to setting that page,
  R = force render, T = focus the page grid, disabled while a text
  field has focus.
- The capacitive Scroll Assistant should scroll the column if it
  injects standard scroll events; untested, verify on device, do not
  build anything that depends on it.

### 7.5 Icon

Adaptive launcher icon: the red seal square with the 泰 mark (or a
plain red square with a paper border), plus the Android 13+ monochrome
themed-icon layer. Name on the launcher: Tylendar.

## 8. Risks and open items

1. Fine grained PAT expiry: a periodic re-paste chore by design.
   Mitigated by the clear 401 re-entry flow. (A GitHub App with device
   flow would remove it but is wildly out of proportion here.)
2. raw.githubusercontent caching: solved by cache-busting, but the
   widget worker should also send no-cache headers.
3. Titan 2 keyboard events: capacitive scroll behavior and key codes
   unverified until tried on the real device.
4. Actions API polling from a widget worker counts against the 5,000
   req/hour limit: a non-issue at 4 fetches/day plus manual use.
5. If settings.json ever gains keys, the app must round-trip them
   (already required by 6.2).

---

# Appendix A: the full native renderer study

Findings from the original, broader question ("can Tylendar become an
Android app that renders all pages natively, dynamically resized").
Superseded as a plan by the remote control app above, kept for the
record; all claims below were adversarially verified on 2026-08-30.

## A.1 Verdict (for the renderer)

Feasible, HIGH confidence, 60 to 100 hours if pixel-perfect parity is
relaxed. The repo is unusually portable: the huangli math is
lunar-python, and the same author (6tail) ships lunar-java
(cn.6tail:lunar:1.7.7, MIT, Maven Central, package com.nlf.calendar)
with every getter generate.py uses (yi/ji, ganzhi pillars, jieqi,
festivals, chong/sha, nayin). Page data (poems.json 41KB,
characters.json, Singapore holidays) copies straight into assets.

Recommended approach was native Kotlin + Compose, re-implementing page
layouts, NOT porting the bitmap renderer: generate.py draws 1,618
lines of absolute coordinates on a fixed 640x960 canvas (W,H at
generate.py:45); on 1440x1440 that pillarboxes 240px per side, 33% of
the screen. Rejected alternatives: Chaquopy (MIT since 12.0.1, Pillow
wheels, would render pixel-identically but inherits the fixed 2:3
bitmap; ~25-40MB APK penalty, not the 60-100MB sometimes claimed) and
Flutter/CMP (needless second toolchain).

## A.2 Key porting facts (verified against the repo to the line)

- lunar-java parity is unproven across version lines (repo pins
  lunar-python 1.4.8, lunar-java is 1.7.x, yi/ji tables were corrected
  between versions): a day-one spot check against frame output is
  mandatory.
- Traditional Chinese: generate.py runs OpenCC s2hk at RUNTIME over
  all huangli strings plus a hand fixup (generate.py:26-40, 227), and
  lunar-java also emits simplified. Build-time converting the JSON is
  not enough: generate a build-time s2hk lookup table over
  lunar-java's finite string universe (the subset_fonts.py source-scan
  trick), ship it as an asset, include the fixup. Re-subset
  ChironSungHK against lunar-java's output universe too.
- The ICS calendar is not decoration: with events, the frame REPLACES
  the yi/ji rows with a time/title/venue table (generate.py:383-411)
  and feeds month-page event dots; any faithful port must spec that
  variant everywhere (all breakpoints, dark mode, widget).
- Dark mode's real trigger is hour >= 18 (generate.py:502), shown at
  the 19:00 wake; an app should flip at 19:00 to match the visible
  wall behavior. The full dark accent table (yellow-on-black special
  days, seal inversion, chip swaps, generate.py:287-301) must be
  copied, not just the background.
- Weather endpoints are keyless (NEA api-open.data.gov.sg v2 x3 +
  Open-Meteo, pages/weather.py:22-26). NEA 403s only the Python-urllib
  user agent; OkHttp's default UA works (verified live). Singapore
  hardcoded.
- Landscape is procedural (date-seeded value noise): re-generate at
  native aspect rather than reflow; note the same date then draws
  different mountains than the wall at other widths.
- Fonts: distributed APKs may ship only the OFL trio, ChironSungHK
  subset 3.0MB, Fraunces variable 360KB (no Reserved Font Name, so no
  renaming obligation), NotoSansSC subset 1.1MB. Canela requires a
  separate per-app-title App embedding license from Commercial Type
  (the owner's canelaweb-*.ttf are WEB license files, so even a
  personal sideload flavor is likely outside their scope: check the
  license text first). MTR Sung terms unknown; mtr-sung.ttf is 8.6MB
  unsubsetted.
- Pixel-parity mechanisms with no direct Compose equivalent (the
  reason the hour estimate has a fidelity caveat): thresholded
  non-antialiased masks (e-paper only, skip on LCD), DuoFont per-char
  fallback (generate.py:105-121; needs API 29 CustomFallbackBuilder or
  manual run-splitting), ink-bounds numeral flushing
  (generate.py:326-340; needs a getTextBounds equivalent).

## A.3 Adaptive layout scheme

- Measure content area AFTER window insets (edge-to-edge is enforced
  at targetSdk 35+; the Titan 2 still has a status bar).
- Branch on content aspect h/w, pinned: SQUARE < 1.4 (Titan 2 ~1.0,
  two-column layouts), STANDARD 1.4-1.9 (the native 2:3 stack; the
  e-paper's own 1.5 lives here), TALL >= 1.9 (surplus height to the
  numeral and leading). Lock portrait on non-square devices or a 20:9
  landscape window (h/w ~0.45) falls into SQUARE and collapses.
- Proportional 640-unit grid: scale unit u = contentWidth/640, margins
  52u, hairlines 1.5u, heavy rules 3u; display numerals auto-fit by
  binary-search sizing.
- 8-role type ramp (Fraunces opsz axis standing in for Canela's
  optical range, Chiron Sung HK for CJK), per-page reflow specs and
  hide-orders for all 7 pages, HorizontalPager across pages, vertical
  swipe tears days, long-press snaps to today, full Titan 2 keyboard
  navigation (focusable root + Modifier.onKeyEvent; HorizontalPager
  has no default hardware-key nav).
- Exact alarms for a 00:00/19:00 flip need USE_EXACT_ALARM or degrade
  to setWindow with drift; use device-local time.
- Glance cannot load custom fonts: widget cards render offscreen via
  the app's own renderer into an ImageProvider bitmap.
- Rear screen (410x502) card: no public API; stretch goal with the
  fallback of running the whole app via SubDisplayLauncher, or not at
  all.
- Accessibility tradeoff to decide: fixed-dp drawn compositions ignore
  user font scale; supply TalkBack semantics per page.

## A.4 Renderer phasing (if ever built)

1. Almanac (3 breakpoints, dark, ICS events variant) + widget +
   lunar-java parity check + keyboard skeleton, ~2 weekends.
2. Poem / character / month / year, pager, day-tear, s2hk table + font
   re-subset, ~2 weekends.
3. Weather + CalendarContract (READ_CALENDAR replaces the secret ICS
   URL entirely on a phone that already syncs the calendar) +
   landscape Canvas port, ~2 weekends; landscape is the hardest item.
4. Frame remote screen, ~1 weekend. (This phase is what became the
   whole app in the main plan above.)

# Appendix B: verification notes

11 agents: 5 research lenses (titan2, play-account, macos-toolchain,
architecture, design), 5 adversarial verifiers, 1 completeness critic;
724k tokens, 189 tool calls, 0 errors. Corrections the verifiers
caught, reflected above: Titan 2 is 60Hz not 120 (Elite is the high
refresh model) and has a 4-row not 3-row keyboard; Compose BOM
2026.08.00 needs AGP >= 9.2.0 (not 9.1.1); AGP 9.3 needs Gradle >=
9.5.0; the free Limited Distribution tier needs a 2SV Google Account +
payments profile (not "email only"); Fraunces has no Reserved Font
Name; NEA blocks only the Python-urllib UA; Chaquopy adds ~25-40MB not
60-100MB; the compileSdk 36-vs-37 and 1.2-vs-1.4 breakpoint conflicts
between agents were resolved by pinning (37, 1.4). Primary sources:
unihertz.com product pages, developer.android.com (edge-to-edge,
exact alarms, verification timeline), android.google.com
/developerconsole, play.google.com/console signup docs, Maven Central
(cn.6tail:lunar), GitHub (Fraunces, chiron-sung-hk, 6tail/lunar-java),
commercialtype.com (Canela licensing), chaquo.com, data.gov.sg.
