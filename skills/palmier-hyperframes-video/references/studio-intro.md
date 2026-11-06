# Studio intro: the opening of every long-form episode

The default for the first ~60-70 s of every long-form episode. One HyperFrames composition carries the hook, the camera
intro and the "in this video" map on the studio canvas. The body of the episode is unchanged: full-screen share, the
uncropped 25% corner camera, face cut-ins ([the-look.md](the-look.md)). Format inspiration: the studio-style intros of
creators such as Jack Roberts (a clean canvas, the camera as a card, real app windows floating beside it).

Build it in the episode's `edit/studio/` folder: `SPEC.md` (numbers and shot list), `REVIEW.md` (what was measured),
`index.html` (tokens, geometry, eases, the set+to pattern) and three small scripts (`plates.py`, `audio_studio.py`,
`finish_studio.py`, see Pipeline). Once one episode has a working intro, copy its folder as the starting point for the next
and write each episode's own SPEC.md and composition.

## When
- Every long-form episode, from frame 0 to the end of the overview (about 77 s at 1x, ~68 s after Final's speeds). The
  body starts on the old edit's framing, so the splice is invisible.
- Write `SPEC.md` first: goal, output, time, look, objects, motion, shots in 1x frames, banned, QA.

## Beat grammar
Each beat starts on a spoken word frame. Order follows the script; a typical order is below.

| Beat | On screen |
|---|---|
| Hero split | Camera card left (544x675), content card right (1200x675): the real app on the typed prompt. Frame 0 is a finished, thumbnail-safe frame. On the camera intro, a name plate at the card's foot over a dark scrim. |
| Proof push | The window grows into the real result (1728x972); the camera shrinks to a small card top-left (264x330). The screen dims and a rounded spotlight walks the details (for an ad: picture, ad copy, headline, picture), a white label chip following it, one marker chip on the payoff. |
| Callout | Camera full frame, face to one side; one white card beside the face (for example the chat with the prompt typing), one marker pill on the claim. |
| Hook line | Camera pushed in (about 1.4x), an ink scrim on the empty side, the hook sentence in white Instrument Serif Italic, word by word on its spoken frames. A struck phrase is allowed. |
| Paper wipe | The camera wipes up off the canvas (clip-path to the top, video drifts up 90 px) on a spoken word. |
| In this video | Canvas only: Pencil kicker "In this video", the episode title in serif word by word, one marker behind the key words; a carousel of cards at 0.6 scale (active at full opacity, neighbours at 0.42) sliding one card per agenda item. |
| Card beats | Back to a hero split (camera card left, one content card right) or full frame with one card beside the speaker, one per spoken point (for example a toggle switching on, three steps folding into "One step.", the free file). |
| Hand-off | The last ~3 s: camera full frame at the episode's own framing (about 1.4x), no graphics, so chapter 1 cuts in unchanged. |

## Numbers (authored 1920x1080)
| Item | Value |
|---|---|
| Canvas | Paper `#F7F7F5` + `radial-gradient(1150px 860px at -6% 106%, rgba(196,80,27,.36), rgba(196,80,27,0) 68%)` (terracotta accent, bottom-left) + the same at `106% 106%` with `rgba(34,81,209,.30)` (cobalt accent, bottom-right) + a faint white lift `1400px 900px at 50% -10%`, 65% white. Still, never drifting. |
| Cards | White, radius 28 px (22 px small camera), edge `0 0 0 1px rgba(17,17,17,.06)`, shadow `0 24px 60px rgba(17,17,17,.14), 0 2px 6px rgba(17,17,17,.06)`. Panels and rows inside a card are Paper 2. Canvas margin 72 px. |
| Geometry | Camera hero 72,162 544x675; small 128,86 264x330; full 0,0 1920x1080 radius 0. Content card 648,162 1200x675; push 96,54 at 1.44x. |
| Camera | A full-frame layer cut to the card with `clip-path: inset(... round r)`, drop-shadow on its parent so the shadow follows the cut. The video inside is scaled and placed so the face lands where the rect wants it while still covering the rect (a `camView(rect)` helper). |
| Type | Bricolage 800 titles 56-96 px (a hero word up to 132), 500 body 28-34 px; Instrument Serif Italic 400 for the hook line (92 px), the title (140 px) and CTA words only; JetBrains Mono 500 only for real strings (URLs, file names). |
| Colour | Ink, Pencil, Line; one Marker `#FFD43B` per frame; each accent colour only on its own side. |
| Arrive | `expo.out` 0.6-0.7 s from scale 0.975 and 24 px below (or 90 px from the side), opacity 0 to 1. |
| Leave | `power2.in` 0.3 s (0.15 s for chips). |
| Layout moves | Camera and window rects `power3.inOut` 0.6 s; spotlight `power3.inOut` 0.45 s. |
| Words | `blur(6px)` + opacity 0 to sharp in 0.13 s, `power2.out`, on each word's spoken frame. Landed titles hold still. |
| SFX | Short whoosh on layout moves, soft click on spotlight steps and list items, pop on marker landings and toggles, typing under typed text. |

## Rules
- Every word is timed from the transcript (the edit's word timeline in 1x frames); no cue by ear.
- Every camera jump cut lands on a layout or framing change (a rect move or a punch-in of ~0.1-0.15x), so no jump shows.
- Real assets only: the real app from the screen plate, real thumbnails, real ad images, real logos, real file names. Never
  invented UI, fake window chrome, or numbers the speaker didn't say. No spoken claim, no proof pill.
- The privacy blur is carried through the plates; the window only ever shows the blurred plate.
- Nothing over the face: cards and lines sit beside it, the scrim stays on the empty side.
- Banned: neon, mesh gradients, a dark void, everything centred, numbered 01/02 labels, mono caps labels, titles that drift
  after landing, a fade-and-slide-up on every element.

## Pipeline
1. **Plates** (`plates.py`, run from `edit/`): the screen plate (4K, privacy boxes blurred, no zoom: the window zooms) and the
   synced 1920x1080 camera plate for the intro frames, through the edit's own privacy and camera-sync code, so blur and lip
   sync match the episode.
2. **Compose** `index.html`: one composition, one paused GSAP timeline, times as `T(frame)` in 1x frames. `hyperframes check`
   passes (duplicate-image and file-length warnings are expected: the camera and window persist across beats).
3. **Render**: author 1920x1080, render with `--resolution landscape-4k --workers 1`. Multi-worker 4K needs ~19 GB of temp
   frames.
4. **Sound** (`audio_studio.py`): new SFX cues only before the splice point; every old cue from the splice on is kept.
   Null-test the new mix against the approved one after the splice: 0.0.
5. **Finish** (`finish_studio.py`): the intro + the 1x export from the splice frame, joined in one filter graph, then
   finish.py's own speed sections, loudnorm and encoder. Keep the export's 1/15360 timebase after the join: a 1/30 clock
   rounds the sped-up timestamps and drops frames (2 frames lost in a ~25k-frame final). Write a new file; the approved
   final stays.

## Gotchas
- Initial states go in `gsap.set` before the timeline: a `tl.set` at 0 never renders on frame 0.
- Mid-timeline, use `tl.set(from)` + `tl.to(to)` pairs instead of `fromTo`, so states hold when the renderer seeks backwards.
- Measure text (marker widths) after `document.fonts.ready`.

## QA
First frame (thumbnail-safe); each beat 0.6 s after it lands; every jump-cut frame +-1; the seam frame against the old
final; a phone-width read of every line; lip sync of the render vs the plate (target 0 frames); the final's frame count,
-14 LUFS, true peak and 0 decode errors against the approved final.
