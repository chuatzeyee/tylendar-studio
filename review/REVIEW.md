# Tylendar Studio review

Scope: the web portal and native Android remote in the isolated `Tylendar-studio` copy. Original source and asset hashes are in `original-source-sha256.json`. Repository history, build caches, build outputs, and machine configuration were excluded from the copy.

## Findings in the original

1. The web portal is a 1,269-line HTML file mixing layout, settings, authentication, photo processing, and network requests. Android repeats the same concepts across a different interaction model.
2. Page browsing commits immediately on the web; Android gallery browsing and keyboard shortcuts have different commit semantics. Multiple option changes trigger multiple renders. Use a consistent draft, preview, apply, and discard flow.
3. Android settings writes launch independent coroutines. Concurrent saves can race, and a refresh can overwrite optimistic state. Serialize mutations and apply related options in a single settings commit.
4. Android stores a token before validating it, and both clients issue deliberately invalid write requests to probe permissions. Validate with read requests, persist only after successful connection, and explain actual write failures.
5. Android compares workflow creation timestamps and the web watches the first newer workflow. Neither reliably associates a settings write with its own render. Match the returned settings commit SHA against workflow head SHA; use numeric run IDs as baselines for manual dispatches.
6. Android can leave a preview override behind after a failed save or render. Distinguish illustration previews, generated output, and a scheduled frame wake. There is no device telemetry, so neither client can confirm what the physical frame currently displays.
7. Android catches cancellation in broad exception handlers and polls with weak error reporting. Use cancellable requests, bounded timeouts, explicit error messages, and cancel polling on disconnect.
8. The portal is constrained to 430px even on a desktop. Android uses fixed height calculations, clipped button labels, tiny carousel targets, and non-scrolling option sheets. Make layouts responsive, scrollable, keyboard accessible, and usable with larger text.
9. Both clients require credentials before any useful exploration. Bundle existing artwork and poems for an explicitly labelled local demo, with no automatic remote writes.
10. The portal has photo management; Android only selects the photo page. Preserve web photo controls and make the difference visible in the revised app and documentation.
11. Repository coordinates are hardcoded. Allow connecting to an explicit owner/repository while keeping GitHub as the fixed API origin; retain the renderer's main-branch contract.
12. Automatic dark almanac previews do not account for weekend red backgrounds. Centralize Singapore time, next-wake calculation, and thumbnail selection.

## Design direction

A quiet print collection: warm paper, a charcoal frame, restrained seal-red actions, botanical green accents, large serif artwork titles, and readable sans-serif controls. The artwork carries the interface. Browse first; one explicit apply action commits the complete draft. Demo state, render state, and scheduled wake are distinct.

## Validation

Recorded after implementation in `VALIDATION.md`. No live GitHub write, workflow dispatch, deployment, or device installation is part of this review.

## Implemented resolutions

| Area | Change in this copy | Evidence |
| --- | --- | --- |
| Web structure | HTML, styling, catalog, pure domain logic, GitHub client, and UI orchestration are separate files. | `portal/js/` and `portal/tests/core.test.js` |
| Interaction consistency | Both clients edit a draft and commit all changed keys with one explicit apply action. Hardware-key browsing follows the same rule. | `portal/js/app.js`, Android `AppViewModel.kt` |
| Save reliability | Fresh reads, SHA-based conflict retries with backoff, unknown-key preservation, disabled duplicate submissions, and serialized Android operations. Failed saves retain drafts. | API tests and mocked browser save/failure scenarios |
| Render association | Settings saves retain the commit SHA returned by GitHub; polling matches workflow head SHA and the main branch. | `core.js`, `StudioLogic.kt` tests |
| Credentials | No write probes. Tokens are persisted only after successful validation. Browser storage is session-scoped; Android uses Keystore AES-GCM. | `github.js`, `Github.kt`, `TokenStore.kt` |
| Cancellation | Android HTTP calls cancel with their coroutine. Disconnect cancels work and polling; operation identities keep cancelled jobs from overwriting current busy state. | `AppViewModel.kt`, cancellable OkHttp callback adapter |
| Preview semantics | Artwork is labelled illustrative. Latest generated images are a separate view, retrieved through authenticated Contents API requests. Scheduled wake is not represented as device telemetry. | Both interfaces; private-image API regression test |
| Responsive UI | Desktop collection/sidebar, mobile horizontal filters and print rail; Android adaptive columns and vertically scrollable content/dialogs. Native controls have at least 48dp target containers. | Browser viewport checks; native runtime limitation recorded separately |
| Content and controls | All ten pages, per-page options, label editing, English poems, saved-setting renders, and one-time almanac overrides remain available. | Catalog and UI regression checks |
| Photos | Portal retains upload/resize/remove, adds demo photos and in-dialog failure feedback. Android explicitly hands photo management to the web portal. | Browser add/remove/cancel/invalid-file scenarios |
| Isolation | No Git history or remote is copied. Studio has a separate Android application ID, local assets, private build cache, and original-source hashes. | `verify_original.py`, APK output metadata |

## Remaining limits and deliberate boundaries

- Firmware reports no acknowledgements or telemetry. A successful render does not prove that the physical frame fetched it. Closing either client cancels its local polling; reopening or refreshing can retrieve the latest run status.
- GitHub's workflow dispatch response does not return a run ID. Manual renders are identified by a newer numeric ID, the main branch, and the `workflow_dispatch` event; two simultaneous manual dispatches from different clients cannot be uniquely distinguished. Settings-triggered renders use an exact commit SHA.
- Fine-grained write permissions cannot be conclusively proven with the read-only connection check. The first real write may be denied; the UI reports that failure without discarding the draft.
- Layout thumbnails are bundled examples, not local re-renders of every option. Their illustrative label remains visible. Poem text uses the bundled 135-poem collection; a separately customized repository poem dataset is not mirrored automatically.
- Both clients retain the renderer's `main` branch contract and fixed Singapore wake schedule. A firmware schedule changed independently must also be reflected in these clients.
- Android photo uploads are not implemented natively. The explicit handoff assumes the connected repository publishes its portal at the conventional GitHub Pages URL.
- Android fetches generated previews through the Contents API's base64 response; files over that endpoint's inline-content limit produce a readable error. The bundled/rendered previews in this project are below the limit.
- Demo edits and Android unsaved drafts are not durable across app/process restarts. The portal warns before leaving with a draft; applying explicitly is the persistence boundary for connected settings.
- No renderer rewrite, frame firmware change, native home-screen widget, deployment, or interaction with a real frame was needed for this scope.
- Lint retains warnings about inherited SDK/dependency versions and launcher assets. Native runtime validation depends on a usable emulator or device; this environment has no KVM acceleration.
