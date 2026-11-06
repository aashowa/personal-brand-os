# Writing spec.py (the beat plan)

A spec is `def make(s): ...` in `REEL_DIR/spec.py`. `reel.py new` copies in
[examples/starter/spec.py](../examples/starter/spec.py); rewrite the beats for the new script. Run
`reel.py words REEL_DIR` first: every time in the spec comes from a spoken word, never a hard number, so a re-render
re-times everything.

## Three layouts

| Layout | Call | Notes |
|---|---|---|
| Split (asset top 0–960, avatar bottom) | `s.beat(t0, t1, html)` | The kit's default. Footage cards, logos, rows, chat boxes. Caption chip on the seam |
| Graphics full screen | `bid = s.beat(t0, t1, html, full=True)` then `s.kick(bid, t0[, sfx])` | Covers the avatar. Captions drop to y 1260: keep 1240–1400 clear. Headlines start at y 230 or lower (format.md § Safe zone). Add `nocap=True` when a headline already says the words |
| Avatar full screen | `s.face(t0, t1, zooms=[(t, 1.12), ...])` | Snap zooms on emphasis words; pause cuts inside flip the framing on their own |

Beats must tile the timeline. The open is split (frame 0 filled: no entrance animation on the first hero), and the
end is `s.face(tCTA, D, ...)`.

## Helpers

From the episode-shorts kit (full table: `../episode-shorts/references/design.md`): `s.T(word, after)`, `s.foot`,
`s.logo`, `s.chip`, `s.head`, `s.photo`, `s.pop`, `s.slam`, `s.snap`, `s.card_in`, `s.typing`, `s.count`, `s.wipe`,
`s.draw`, `s.cam_punch`, `s.sfx.append((t, name))`, `s.nocap.append((t0, t1))`.

Added by `reel.py`:
- `s.face(t0, t1, zooms=())`: the avatar full screen, as above.
- `s.zap(t, hold=0.7, sc=1.12)`: a 0.06 s punch-in on the split-screen camera, with an air-whoosh. Pause cuts that
  land in split beats get one automatically.
- `s.kick(bid, t0, sfx="whoosh-thud")`: a full-screen graphic lands (1.12→1, 0.22 s). Pass `"air-whoosh"` when the
  logo pop already has an impact, so thuds don't stack.
- `s.card(t0, t1, v5, rect, box, push=1.05)`: a footage card cropped from `"footage"` at any `box` (x, y, w, h; even
  sizes), drawn above full-screen graphics and hidden after t1. Returns `(id, frame_html)`; put the frame in the beat.
- `s.cuts`: the pause-cut times.

The starter spec also shows two small local helpers worth copying: `W(*keys, after)` (first word starting with any key,
so "ten" and "10" both match) and `before(t)` (the word before t, for a beat that opens on "You").

SFX names: the media-use bank (`pop whoosh whoosh-short whoosh-cinematic riser impact-bass-1 impact-bass-2 glitch-1..3
ping chime sparkle click click-soft key-press typing notification error`), plus `assets/sfx/`: the shipped CC0 set
(`cc-click cc-ding cc-drama cc-glitch cc-hit cc-impact cc-pop cc-riser cc-swipe cc-tick cc-type cc-whoosh cc-woosh`)
and the six names the helpers use, which you supply (`air-whoosh whoosh-thud riser-short boom cash click-pop`;
[assets/README.md](../assets/README.md)). `glitch-*` is long static: `build` cuts it to 0.3 s. To cut any other sound
short, append `(t, name, t_end)` (the mixer trims it with 50 ms fades).

## Characters

A Reel is fun when a character acts the story out, not because text appears. On Claude topics, use the Claude
Code crab in **2–4 moments per Reel**, each on the noun or verb being spoken. The crab is Anthropic's mascot, so treat it
like a logo and keep it off topics that aren't about Claude. Character ids start with `k` (no kit id does).

| Helper | What it does |
|---|---|
| `s.crab(p, x, y, w, props="")` | Crab html for a beat. Widths: 220 peeking, 240–280 in a row, 420 for a hero. Parts: `#p` moves, `#p-s` squashes, `#p-l1..l3` legs, `#p-aL/aR` arms, `#p-eL/eR` eyes |
| `s.prop(pid, name, css)` | A prop riding on the crab: `cap` (grad cap), `chef`, `lens`, `receipt`, `coins`, or raw svg. The css places it in the crab's box |
| `s.drop(sel, t, frm=-1100, dur=0.22)` | Crab or prop falls in, hidden above until t. Follow it with `s.squash(p, t + dur)` |
| `s.squash(p, t)` | Landing: a 0.07 s squash with an elastic settle, plus a click-pop |
| `s.blink(p, t)` / `s.dance(p, t, n=5)` | Blink, or legs and arms alternating with a rock. n is odd, and the dance lasts 0.13 × (n + 2) s. Add one of these so nothing holds still for more than about 1 s |
| `s.peek(p, t, h)` | Rises h px from behind a card. Put the crab before the card in the html |
| `s.clone(p, dx, t)` | A copy slides dx out from behind the crab at the same x (earlier in the html) and lands. This is the "team" split |
| `s.sticker(sid, code, css, t)` | A Noto animated emoji (code `1f440` 👀, `1f525` 🔥, …) as a white-outlined sticker that pops in. Returns html. A code not yet in `assets/stickers/` is fetched once |

Moments that worked:
- The crab drops onto a headline and dances while a list pops in ("walks you through").
- It wears a grad cap on "teach".
- It peeks over a document card and reads it.
- One crab splits into a team, and each gets its prop as its job is named.

The first two, as spec code (a full-screen beat from `tA` to `tB`, `tWalk` and `tTeach` from `W()`):

```python
inner = head + s.crab("kw", 750, 150, 240)                        # B6 · FULL: the crab lands on the headline
s.drop("#kw", tA + 0.1); s.squash("kw", tA + 0.32); s.blink("kw", tA + 0.75)
s.dance("kw", tWalk - 0.25, n=7)                                  # dances while the list pops in
hat = s.prop("kt-hat", "cap", "left:105px;top:-118px;width:210px;height:158px")
inner2 = s.crab("kt", 330, 560, 420, hat)                         # B7 · FULL: a hero crab gets a grad cap
s.drop("#kt", tB + 0.04, sfx=None); s.squash("kt", tB + 0.26, sfx="impact-bass-1")
s.drop("#kt-hat", tTeach - 0.24, frm=-900, dur=0.2); s.squash("kt", tTeach - 0.04, sfx="pop")
```

If a Reel uses a sticker, the post caption credits "Animated emoji: Noto Emoji © Google LLC, CC BY 4.0".

## Timing traps

- **A word that appears twice.** `T("that's")` matched "this week **that's** still…" instead of the sentence start.
  Anchor it after a neighbour: `T("that's", T("receipt"))`, `T("and", T("cash", tSame))`, `T("the", T("save"))`.
  After `build`, list the beat starts (`grep -o 'data-start="[0-9.]*"' index.html`) and check that each sits where the
  sentence starts.
- whisper splits hyphen chains and changes contractions ("link's" came back as "links"). Find those words by prefix,
  and fix captions with `caption_fixes` in reel.json.
- Pop supporting items early enough to read (≥ 1 s). A chip that pops in a beat's last 0.4 s is never seen.

## Assets: real first

| Need | Source |
|---|---|
| A tool | Its real logo: the kit's `assets/logos/` if you added it there, else svgl.app / Simple Icons into `REEL_DIR/logos/` (a missing logo stops `build` with its filename) |
| A result or demo | Crops of a **privacy-blurred** episode export (`"footage"` in reel.json + `s.foot`). Find crops on a contact sheet; keep off the burned-in camera overlay |
| Text too small on footage | Rebuild it natively with the exact text (chat box, rows, flow boxes) |
| A life line | A free Unsplash photo: `python3 ../episode-shorts/scripts/shorts.py photos search "<q>" /tmp/p` |
| A website or app | `npx hyperframes capture <url>` (see `/hyperframes-cli`), or a headless-Chrome screenshot (`--headless=new --window-size=1080,1700 --screenshot=...`) into `REEL_DIR/photos/` |
| Online video (a tool's launch / showcase clips, YouTube) | Download into `REEL_DIR/src/video/`, list the moments at the top of the spec as `SEGS = [(name, clip, start, seconds), ...]` with a `stitch()` that trims each with ffmpeg (`-ss start -t seconds`, scale 1280x720, 30 fps, concat) into `src/web.mp4`, and run `python3 spec.py` to build it; set `"footage": "src/web.mp4"`. Crop with `s.foot` (split) or `s.card` (anywhere, above full-screen graphics). Note every source in `src/SOURCES.md` |
| A repo's walkthrough on YouTube | `yt-dlp --no-update --flat-playlist --print "%(id)s %(duration_string)s %(channel)s %(title)s" "ytsearch10:<repo> <what it does>"`, prefer the creator's own video. Download in 1080p with `--extractor-args "youtube:player_client=android_vr" -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]" --merge-output-format mp4`; on a 403, retry with `player_client=web_embedded` (`mweb` only gives 360p). Transcode any AV1 result to H.264 before stitching. Stitch at the source size (1920x1080; 640x360 for a 360p fallback), keep cards ≤ 960 wide, and crop out the creator's webcam corner (check a frame with `drawgrid`). Note the channel and times in `src/SOURCES.md` |
| A number | Kinetic headline with the marker underline; a boom or cash SFX on the payoff |

Footage must come from an already privacy-checked export. A new source runs the episode-shorts privacy step (OCR
against the terms) before render.

## Starter beat table (~28 s, the pattern to copy)

| Beat | Layout | What |
|---|---|---|
| B1 Hook | split | Native chat box typing the one-line ask → generic reply pops → "Generic" stamp, zap on "nothing" |
| B2 "So before you ask it anything," | face | zoom 1.12 on "anything" |
| B3 "give it three things." | full + kick + riser | "3 things first." + three numbered cards popping on "three" |
| B4 "First, who you are…" | full + kick | "The first" chip, headline, a tick row snapping on each spoken item |
| B5 "Plus, one example…" | split | Your doc in, an arrow draws, its doc out in your style; zap on "style" |
| B6 "And finally, the rules…" | full + kick | "The third" chip, headline, two cross rows on "making" and "sending" |
| B7 "You just put all three in one note…" | full + kick | The note card with its three lines, "Top of every chat" chip |
| B8 "It takes about ten minutes," then "write it once." | face, then full + kick | zoom on "ten"; two slams, boom on "once" |
| B9 CTA | face | zooms on "comment" and the word, chip "Comment WORD" at y 1250, captions hidden under it |
