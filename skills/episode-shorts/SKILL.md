---
name: episode-shorts
description: "Cut 1-3 vertical Shorts / Reels / TikToks out of a finished long-form episode in the split format: the creator's camera on the bottom half, full motion graphics on the top half built from REAL material (screen footage from the long-form, real logos, real photos), yellow captions on the seam, full-screen graphic kicks, then render, master to -14 LUFS and file them into the Shorts output folder. Use whenever the user wants shorts, reels, clips, vertical cut-downs, 'repurpose this episode', 'make short form from the long form' or 'turn this video into shorts', even if they don't name the format. Built on palmier-hyperframes-video (the long-form) and HyperFrames (the build)."
---

# Episode Shorts (long-form → 9:16 split Shorts)

The long-form is already edited, privacy-blurred and approved in Palmier. A Short re-uses that work. Its voice, cuts,
grade and blurs come straight from the long-form edit, so a Short is mostly a story and design job: pick the moments,
then dress the top half with real evidence. The user's review stays taste-only, because the gates below catch the
technical defects first.

```
long-form edit (Palmier) ─ timeline dump · words · polished voice · clean camera · blurred 1x export · privacy terms
   └─ 1 pick → 2 cut list → 3 cut media → 4 spec beats → 5 build + check → 6 snapshots → 7 privacy → 8 preview ✋ → 9 render → 10 deliver
```

## Decided defaults: apply, don't re-ask
| Item | Default |
|---|---|
| Layout | 1080×1920. Top 0–960: paper grid + motion graphics. Bottom 960–1920: your camera, head and shoulders, graded like the long-form. Ink seam at 960. |
| Top half | **Real** material: crops of the long-form's blurred export (demos, slides, results), real brand logos, free real photos. Kinetic brand text (Bricolage 800, JetBrains Mono chips, marker yellow) ties them together. |
| Captions | Yellow chip on the seam, 1–3 words, ≤ 20 characters, popped per group. Skipped where a headline already shows the same words (`nocap`). In full-screen beats they drop to y 1260 (clear of Instagram's caption area below 1440). |
| Full-screen kicks | 2–3 per Short: the graphic takes the whole frame for a punchline or end card, and always over repaired-camera windows. |
| Speed / length | 1.1× (on top of the long-form's um/pause cuts). 30–65 s. End on a complete thought: extend the last piece to the sentence end. |
| Frame 0 | Already shows the beat's graphic (it is the feed thumbnail): no entrance animation on the first beat's hero. |
| Audio | Polished dialogue + SFX at −24 dBFS from the placed graphics. No music unless asked. Master −14 LUFS, ≤ −1 dBTP, picture stream-copied. |
| End card (CTA) | Full-screen, in your own wording from `config.json` `episode_shorts.cta` (example: Follow me and comment "WORD", and I'll send it to you directly). WORD must be listed in `system/comment-words.md`, so your comment-to-DM automation sends the free file from your site (`creator.site_url`). The example spec's last beat is this card. |
| Delivery | `<episode>/shorts/<file>.mp4`, cloned into `<output_dir>/Shorts/<title>.mp4`; the long-form into `<output_dir>/Long-form/`. `output_dir` is `config.json` `episode_shorts.output_dir` (default `episodes/<slug>/shorts/`). Posting happens only after the user's OK, through `content-autopilot` (`post.json` + `system/schedule.py`: YouTube private + publishAt; `"platforms": ["youtube"]` keeps a Short off Instagram, Facebook and TikTok). |

## Inputs: one `shorts.json` per episode (in `<episode>/shorts/`)
Start from [examples/shorts.json](examples/shorts.json). Paths are relative to the file.
- `timeline`: Palmier `get_timeline` dump of the FINAL 1× timeline (`palmier_mcp.mjs '[[…open…],["set_active_timeline",…],["get_timeline",{}]]'`). It must be the timeline that was exported. Pause cuts made after a caption file was written shift every later time (a single late pause cut can shift everything after it by 0.4 s).
- `words`: source-time word list `[[start, end, text], …]` (the long-form intake's whisper words). `voice`: the polished dialogue the Dialogue track uses.
- `camera` + `camera_offset` (camera frame = source frame + offset, e.g. −2) + `camera_crop` (x, y, w, h in camera pixels, 1.125 aspect). `repaired` (optional): the camera smoothing's `{"ranges": [[f0, f1], …]}`. `lut` (optional): see step 3.
- `export`: the privacy-blurred 1× export of the same timeline (all footage comes from here, so its blurs carry over). `terms`: the long-form privacy terms. `longform`: `{file, title}`. `output_dir` (optional): overrides `episode_shorts.output_dir` for this episode.
- `caption_fixes`: episode mis-hearings (`words`, `phrases`). The kit already fixes cloud→Claude and chatgbt→ChatGPT.
- `shorts`: `{name: {ghost, file, title, edl}}`, where `edl` is a list of `[start, end]` in 1× timeline seconds; `ghost` is the big faint word behind the top half.

Commands: `S=skills/episode-shorts/scripts/shorts.py` from the repo root (run `python3 $S --help`; `--selftest` must pass).

## Steps
**0 · Preflight.** Run `sysctl vm.swapusage` and `df -h`; if swap is nearly full, ask the user to close heavy apps. Desktop sources can be iCloud
placeholders: `ls -lO` shows `dataless`, and `brctl download <file>` fetches them (open() otherwise times out).

**1 · Pick 1–3 moments.** `python3 $S transcript shorts.json` prints the long-form as sentences with 1× times. A moment that
works on its own has a hook in the first 2 s, one idea, a payoff, and on-screen proof (a real result, demo or number). Prefer moments whose
long-form screen shows that proof. Reorder within a Short to open on the punchline when it helps (for example open on "30 minutes
→ 2 minutes"). Present the candidates (title idea, times, length, what's on screen) and let the user choose. A new look gets a
mock frame first; the split layout itself is decided.

**2 · Cut list.** For each piece, take `[start, end]` from the transcript times, on word boundaries. Drop false starts and
asides ("I'm just gonna blur this"). Extend the last piece to finish the sentence.

**3 · Cut media.** `npx hyperframes@0.8.174 init "<shorts>/<name>" --non-interactive --example=blank --skill=general-video`, then
`python3 $S cut shorts.json <name>` → `assets/voice.wav, camera.mp4, words.json`. It prints `cover_full_screen`: the
final-time windows where the camera was repaired by interpolation. Those frames smear at half-screen size, so a full-screen beat must
cover each window. Grade once per episode: grab the same moment from the raw camera and from the graded long-form export
(2–3 frames each, no overlays) and run `python3 $S grade <shorts>/_build/grade.cube raw1.png graded1.png …`. The error should
drop clearly (for example 8 → 3).

**4 · Spec the beats** in `<shorts>/_build/<name>.py` (`def make(s): …`). Start from [examples/s1-before-after.py](examples/s1-before-after.py),
which shows every pattern below on a made-up script. Beats tile the timeline. Each beat has one message, timed to a spoken word with `s.T("word", after)`.
Read [references/design.md](references/design.md) for the block helpers, zones and which element suits which line.
- **Footage:** use `s.foot(t0, t1, s.sync(t0, t1), rect, "wide"|"square", label)` for what was on screen while the words were said, or a fixed
  long-form range as B-roll. Find crops on a grid contact sheet of the export, and keep them off the long-form's baked camera
  overlay (for the 25% corner camera: x > 0.749 and y > 0.754).
- **When footage text is too small at phone size, rebuild it natively** with the exact on-screen text: a slide, a chat box, a flow.
- **Logos** come from `assets/logos` (the kit ships none: [assets/logos/README.md](assets/logos/README.md) lists the filenames the specs expect and where to get official files) or the episode's `<shorts>/logos/` (from svgl.app or Simple Icons); episode logos win.
- **Photos:** `python3 $S photos search "<query>" /tmp/p` shows a contact sheet, then `python3 $S photos get <id> <name> <shorts>/photos`.
  These are free Unsplash photos; Unsplash+ is refused, and credits.json is written for you.

**5 · Build + check.** Run `python3 $S build shorts.json <name>`, then `npx hyperframes@0.8.174 check` in the project. The gate is **0 errors**; the
remaining warnings are sub-composition suggestions. Treat layout errors as real, for example a headline overlapping the line under it.

**6 · Snapshots.** Snapshot every beat at 75–80 % of its length, plus t = 0:
`npx hyperframes@0.8.174 snapshot --at <times> --describe false --no-end` (`--describe false` keeps frames from going to Gemini).
Check what a viewer would see on a phone: footage that matches the words, readable text, nothing cut at the edges,
nothing colliding with the seam caption (keep headlines out of y 790–1030 in split beats), no smeared face, and a filled
first frame. Fix it, rebuild, and look again.

**7 · Privacy.** `python3 $S privacy shorts.json` OCRs every footage clip (3 fps, 2× upscale) against the terms, and must exit 0.
Look at the frames too: the export's own motion-area blurs can turn whole moments into mush (e.g. a PDF opening), so move
the range to a still moment.

**8 · Preview ✋.** Run `npx hyperframes@0.8.174 preview --background` in each project (ports print), and open one in the browser pane. The user watches
with sound and says "render" or asks for changes. Render only after that.

**9 · Render.** One Short at a time, 2 workers (memory): `npx hyperframes@0.8.174 render --quality delivery --workers 2 --output renders/<name>.mp4`.
Check 1080×1920, 30 fps, and a duration equal to `data-duration`.

**10 · Deliver.** `python3 $S deliver shorts.json` applies two-pass loudnorm to −14 LUFS with the video stream-copied, checks decode, loudness, true
peak and duration, then clones each Short into `<output_dir>/Shorts/<title>.mp4` and the long-form into `<output_dir>/Long-form/`
(`cp -c`, an APFS clone on macOS). Stop the previews (`npx hyperframes@0.8.174 preview --stop`) and add a "Shorts" section to the
episode notes (pick, sources, checks, delivery).

## Traps (symptom, cause, rule)
| Symptom | Cause | Rule |
|---|---|---|
| Every cut after one point started 0.4 s late | The cut list came from an SRT written before a later pause cut | Times come only from `shorts.py transcript` on the exported timeline |
| A beat showed the wrong slide or a 90 s blur | The footage range crossed a cut (start in one piece, end in the next) | `s.sync(t0, t1)`: starts snap forward, ends snap back at cuts |
| Smeared face at half-screen | Long-form interpolated repaired frames, invisible in the corner PiP | Cover `cover_full_screen` windows with `full=True` beats |
| A footage card showed a small copy of the speaker | The crop included the long-form's own camera overlay | Keep crops off the overlay corner |
| Footage frames were all blur | The export's motion-area privacy blur covers a page change or scroll | Pick a still range; look at the frames |
| Empty grid on frame 0 | Every first-beat element animated in from 0 | Hero elements static at t = 0 |
| Headline hidden under the caption | Text placed at y 800–930 in a split beat | Headlines at the top (y ≈ 96) or as paper-backed cards |
| A supporting card was on screen for 0.5 s | Popped on its own word, right before the beat cut | Pop supporting items early enough to read (≥ 1 s) |
| Render stalled risk | Swap full; one Chrome per worker | `--workers 2`, one Short at a time |
| `hyperframes snapshot` could send frames to Gemini | `GEMINI_API_KEY` set | Always `--describe false` |

## Hand-off message
Lead with where the files are, then one line per Short (title, length, what's in it). Give the checks as plain facts (−14 LUFS,
0 decode errors, OCR frames, 0 leaks), anything not reviewed (no full real-time playback by Claude), and the open decisions
(music bed, render, upload).
