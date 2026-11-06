---
name: palmier-hyperframes-video
description: "Edit recorded footage (screen recordings, talking heads, long-form and shorts) into a finished video in Palmier Pro, in a fixed order with background lanes: intake health and OCR, transcript rough cut, pause/um removal, camera repair, audio polish, grade, zooms, brand graphics, tight privacy blur, SFX, music, speed and a one-command final. Automatic gates run before the user reviews, so their review is taste only."
---

# Palmier + HyperFrames video pipeline

Raw footage in, finished video out, in a known order. The user's review is about taste only, because the gates catch the
technical defects first. The speaker carries the explanation; graphics show the evidence. Defaults that are already decided
(hook, speeds, music, captions, privacy, camera) live in [the-look.md](references/the-look.md) under **Channel defaults**:
apply them, don't re-ask.

```
SOURCE → 01 Intake ──→ 02 Rough cut ─┐   Read 1 The look (what, every app) · Read 2 App playbook (how, per app)
  bg lanes: health · transcript · OCR cache · camera smoothing
                                     ▼
 in the app: proof gate → 03 Audio polish → 04 Grade* → 05 Graphics + zooms + privacy (5a plan → 5b build → QA gate → 5c converge)
             → 06 SFX → Music bed (opt-in) → 07 Review (user, taste only) → 08 Export → Final (one command)
 second entry: Clipper (long-form → 9:16) = episode-shorts skill               * camera only; skip screen-rec/raw
```

## Before anything (1 minute)
- Identify the sources, the latest approved version and the owning project and timeline. Every meaningful revision goes on a
  **copy** (`create_timeline` with `from`). Approvals, budgets and answers already given stay in force within their scope.
- Never export, publish or spend credits without an explicit yes. For credits: dry run first, then ask with the number.
- **Preflight:** `sysctl vm.swapusage` and `df -h`. If swap is nearly full, ask the user to close heavy apps before long
  batches: Palmier has stalled for 30 min with swap full. Keep 25 GB free for an export plus the final.
- Talk to Palmier through scripts: `palmier_mcp.mjs` for a batch, `masks_apply.mjs` for long loops. Every new session
  adds a line to Palmier's chat panel, so prefer fewer, longer sessions.
- A narrow fix changes only what was named. Check both boundaries of every patch. Don't silently install runtimes.

References, only when the step needs them:
- the-look.md: numbers, channel defaults, delivery.
- [studio-intro.md](references/studio-intro.md): the long-form intro (first ~60-70 s): studio canvas, camera card, beats, numbers, pipeline.
- [palmier.md](references/palmier.md): Palmier operations and verified quirks.
- [graphics-and-kie.md](references/graphics-and-kie.md) and [motion-library.md](references/motion-library.md): graphics and motion.
- [finishing.md](references/finishing.md): audio, music, Final.
- [review.md](references/review.md): the sharded fresh-eyes review.
- [edit-rationale.md](references/edit-rationale.md): worked decisions.

## The fast path: order, commands, gates
Scripts are in `scripts/`; the Python ones have `--selftest`. Start every background job at the step that names it, then
make decisions while it runs.

| Step | Do | Background while you work | Gate (must pass) |
|---|---|---|---|
| **01 Intake** | Copy/reference the originals (read-only). Write `terms.txt` from `references/privacy-terms.txt` plus the client names. | `footage_health.py SRC --out health.json` per source. H.264 intermediate if not edit-friendly (palmier.md). `mlx_whisper` → `words.json`, once. `privacy_scan.py SCREEN - terms.txt warm.json --cache ocr.json` (whole source). `smooth_camera.py` if the camera stutters. | Intake: edit-friendly codec, sync offset known (`--sync REF --ref-crop`), stutter/frozen ranges read. |
| **02 Rough cut** | Edit decision list from the transcript: one take per beat, the hook (channel default), cut retakes, waits and OBS window captures. Build real clips in Palmier. | Graphics HTML/PNG renders (`graphics.py render`) can start once beats are known. | - |
| **Proof gate** | `speech_gaps.py AUDIO words.json --timeline tl.json --verify --out cuts.json` → one `ripple_delete_ranges` (Dialogue track). | - | `speech_gaps.py … --gate` exits 0. Frames before and after match at zooms, blurs and the camera. |
| **03 Audio** | `audio_polish.py SCREEN.mp4 polished.mov` (highpass, 2.5:1 compression, gain, limiter; video stream-copied) → import → `swap_clip_media` on every Dialogue/Screen clip. | - | ≈ −17 LUFS, peaks ≤ −6 dBFS. |
| **04 Grade** | `inspect_color` → `apply_color` on one camera clip → copy its `color` to every clip of that camera. | - | Camera clips only. |
| **05a Plan** | Beat table: cue frame → what the viewer must understand → element → hold. Zoom shot list (`shots.json`). | - | Full screen by default; zooms only on key moments (the-look.md); one tag at a time. |
| **05b Build** | `graphics.py place/keys`. `zooms.py tl.json shots.json` → calls. Privacy: `privacy_scan.py SCREEN tl.json terms.txt plan.json --cache ocr.json --media REF` → `--splits` → `split_clips` → re-read → `--ops` → `masks_apply.mjs`. | Contact sheets render while the gate runs. | - |
| **QA gate** | `qa_timeline.py tl.json --ocr ocr.json`. Privacy: `privacy_scan.py --cover tl.json terms.txt ocr.json REF` (every clip, seconds) → `masks_apply.mjs` until `[]`; then `privacy_scan.py --sweep SCREEN tl.json terms.txt REF` → `masks_apply.mjs` until it returns `[]`, then `capture_frame` a few frames → `--check`. Inspect motion as sequences (entry, hold, exit). | - | QA exits 0; sweep returns `[]`; no readable sensitive word in captures or the exported file; no blank first frames. |
| **5c Converge** | Sharded fresh-eyes review (review.md): 3–4 parallel reviewers, ≤ 2 sheets each. Fix, then run the gates again. **3 rounds max.** | - | No high-severity findings left. |
| **06 SFX** | `sfx.py SPEC.json sfx.wav --cues cues.json` from the placed graphics → import at frame 0 on an `SFX` track. | - | Each hit ≈ −24 dBFS. |
| **Music (opt-in)** | Channel default: intro bed only (finishing.md). | Generation runs in the background once approved. | Licence or receipt kept. |
| **07 Review** | The user watches. Taste only: pace, music, graphics density, hook. | - | If the user finds a technical defect: fix it **and** add the check that would have caught it. |
| **08 Export** | Only on "export": `export_project` (H.264, Match Timeline, timeline id) to scratch; poll `manage_exports` once a minute. | Write the production note. | The file exists and its duration equals the timeline's. |
| **Final** | `finish.py export_1x.mp4 EPISODE/final.mp4 --speed "0:HOOK_END:1.15,HOOK_END:INTRO_END:1.2,INTRO_END:end:1.08"` | - | Exits 0: duration, decode, −14 LUFS, ≤ −1 dBTP; the ~/Downloads copy is an APFS clone. |

## Traps that cost real episodes time (symptom, cause, rule)
Some rules name a per-episode helper (a sweep, scroll bands, a filler pass, a gaze finder). Those are short scripts you
write in the episode's `edit/` folder when the episode needs them; the rule says what each must do.

| Symptom | Cause | Rule now |
|---|---|---|
| ~1.5 h lost building running captions and panel-wide blurs, then removing both | The channel defaults were not applied first | Channel defaults first: no long-form captions; tight OCR blur only. |
| A 37 min privacy scan | Every clip was decoded separately and re-OCR'd after every edit | Warm `--cache` at intake; decode per contiguous source run; re-plans read the cache (seconds). |
| Palmier stalled for 30 min | Swap full, hundreds of short MCP sessions | Preflight swap; long loops in one session; quit Palmier after an autosave if it stalls. |
| One review took 2 h 10 min | A single reviewer re-viewed 81 frames after images dropped from its context | Gates first, then 3–4 sharded reviewers with the review.md brief. |
| A whole review round spent on layout | Stacked tags, small intro tags, an unzoomed demo | `qa_timeline.py` checks these in seconds. |
| A leak found on the final | After a recut, old masks were reused by source and only restored clips were swept; an app card showed a truncated "AppID: …" (truncated IDs match no ID regex) | `--cover` gate on every clip from the OCR cache; labelled-ID `line:` rule in privacy-terms.txt; `--check` frames of the final before calling it done. |
| Leaks found after export | OCR samples every 0.5 s missed fast scrolls; grayscale OCR missed red text on dark; a PDF opening changed every frame | OCR gray + red plane; flick-scrolls blur the moving area; `--sweep` (every 3rd frame, spreads hits to neighbours) before export; `--check` on frames of the exported file. |
| Leaks found in review | Word boxes on an open account switcher left client-name fragments, and a misspelled client name matched no term; an account ID under a dimmed settings drawer never OCR'd | A client list on screen gets one panel box for the frames it is open; fixed boxes on an ad platform's header IDs for every frame of that app; review crops of every list or dropdown of accounts. |
| Lip sync off and repeated words, found in review | A separate camera with silent audio was synced on 533-sample audio frames (16000//30) instead of 533.33: a fake 0.06% drift slid the corner camera up to 18 frames late. Whisper smoothed self-corrections away, and its word times clipped word edges | Sync silent cameras by Vision lip openness vs voice at syllable scale on exact 1/30 s frames, then audit the edit's own frame mapping (≈0 everywhere). Verbatim pass for repeats; snap cuts to silence; re-transcribe each piece alone to prove no word is clipped; A/B every extra filler cut. |
| Explainer card landed early, and card text overflowed | The card landed on the topic word, so the speaker's reason played under it; a card set SVG `<text>` in fixed rects and the text ran outside them. Also: iCloud Desktop sources go `dataless` again when the disk is ~98% full, and a re-download crawled at ~10 MB/min | Keep the "why" sentence on the slide (push in on what is being pointed at) and cue the card on the bridge line. Lay cards out as HTML boxes that size to their text; render each card's last frame and look for overflow. Before a final, `ls -lO` the sources and keep ≥ 20 GB free. |
| A 3 h 40 min sweep, and a leak caught on the final | The sweep seeked once per frame and ran 8 tesseracts at 4 threads each on 12 cores: 21 frames/min. A pause the gate missed: Whisper stretched one word over a 4 s silence. An ID flick-scrolled through 7 frames, faster than the sweep's ±10-frame boxes follow | Sweep: one in-order decode per piece, `OMP_THREAD_LIMIT=1`, reuse words on unchanged frames, append results as they land (~1 h). Pauses: `silencedetect` on the hook and close too, not only word gaps. Scrolls: `--check` every 0.2 s across settings/account pages of the final; a moving ID gets a band over its column for the scroll frames. |
| Three trashed 4K finals | A notes app flicked client names past between the sweep's every-3rd-frame samples, and the render sits 2-4 frames off the sweep's labels; OCR split long sign-in URLs in the address bar so few samples matched; machine names carried the computer's username | Dense `--check` (every frame) of each scroll stretch of the final, `ffmpeg -nostdin` in any loop. Scroll bands per word over its path on f-4..f+8; fixed address-bar boxes on sign-in/auth pages; if words still read during a flick, blur the whole pane for it. |
| 8 fillers and a readable ID found in QA of the review file | Whisper stretched "than" and "for" over two uhs, so every filler pass passed them. OCR read a monospace UUID's hyphens as em dashes, so the UUID rule missed a site ID | A third filler pass on the rendered review audio (medium model, map back, re-hear alone, A/B) before the user watches. UUID rules take any dash (`references/privacy-terms.txt`). |
| A whole extra version round | A result and the next prompt, typed with OBS paused (no voice), flashed past inside a 2x wait; and the speaker talked to the lens for minutes while the body kept them in the corner | Silent screen beats typed off-mic play at 1x as a `HOLD` (no pause cuts, corner out, a quiet bed) with pans between the result, the page and the prompt, and the next spoken line J-cuts in over them. Every talk-to-lens run ≥ 4 s goes full face with wall cards (find runs by gaze; the-look.md Camera row). Wait loops on a process name must not match their own command line (`pgrep -x`, not `ps \| grep -c`). |
| A client name in the review file | A stutter fix stretched one piece by 0.4 s after the privacy plan was made; the stale plan never OCR'd those frames. Also: two wait loops used `pgrep -f NAME` and matched their own command line, so the render never started | The review render re-plans privacy on the current cut first (the cache makes it seconds), and the sweep runs before the review render, not only before the final. Wait on a background task's own notification instead of a `pgrep -f` loop. |
| A client name readable in a 4K final, with the every-15th-frame check at 0 | Scroll bands were run by hand once, so the copied final script never called them; the sweep's boxes trailed a scrolling answer by a line for 4 frames | Scroll bands are a line in the final script, after the privacy re-plan; the dense `--check` runs on every scroll and sped-up stretch of every final (map the sweep and burst segments to final seconds). |
| An email, an ID, card digits and balances readable in a review file, with the sweep at 0 | 4K OCR read a dim sidebar email on some frames only, so its blur flickered and the sweep counted it covered; a fixed box covered one visit of three; the ID's misread spelling matched no term; a pay button and a scrolling chat outran the word boxes. Also: Whisper hallucinated "Okay." over 2.5 min of real speech | Run the frame `--check` on the 1080p review file as well as the final: tesseract reads small dim text better there. A label that stays on a page gets one fixed box for every visit (find all visits in the OCR cache first). Moving items are tracked per frame (by colour, or OCR on every frame of the stretch). Compare a long Whisper pass with an energy gap check. |

## Notes per step
- **01 Intake:** OBS HEVC long-GOP goes black in Palmier; make the H.264 intermediate *before* placing clips. For silent
  audio, sync by picture (no baked webcam: Vision lip openness vs the voice on exact 1/30 s frames, syllable-scale high-pass).
  Observed offsets were constant, +2 to +5 frames (camera vs baked webcam, r = 0.89). Stutter → `smooth_camera.py`
  (frame-exact). Frozen ≥ 1 s → plan a speaker card, never a frozen face.
- **02 Rough cut:** transcribe once with word timestamps; everything later maps through the clips. The edit decision list
  and the finished script go in the episode notes. A recreated UI (e.g. the hook's chat bar) uses the exact real text, is
  followed by the real result, and is labelled in the notes.
- **Proof gate:** Whisper drops "um"s, so fillers are found acoustically and each one is confirmed. After any ripple cut,
  rejoin and re-key the graphics it split (`qa_timeline.py` flags them).
- **05 Graphics:** brand HTML → transparent PNG → clips per overlap slot → keyframes. A highlighter follows a zoom (playbook).
  Zooms are capped at 2.2× on a 4K source, and the baked webcam always stays under the overlay (`zooms.py` enforces it).
  Content that sat under the OBS webcam in the recording can't be recovered by any zoom; don't chase it.
- **Privacy:** masks are static, in source coordinates; scrolls need splits (the script plans them). Only touch masks named
  "privacy blur". Keep the user's own brands and public contact details visible.
- **Final:** the production note covers source mapping, decisions, generated-asset receipts, which checks ran, and what was
  not reviewed (sampled frames are not continuous playback).

## Second entry · Clipper (long-form → 9:16)
Use the **episode-shorts** skill. It re-uses this edit's timeline, words, polished voice, camera, blurred 1× export and
privacy terms: the split layout (camera bottom, real-footage motion graphics top, seam captions), HyperFrames build,
−14 LUFS delivery into the Shorts output folder (`config.json` `episode_shorts.output_dir`).
