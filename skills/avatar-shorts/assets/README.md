# Assets you add yourself

The code uses these files by name, but they aren't shipped (they came from a paid catalog, so they can't be
redistributed). Add your own under the same names.

## Sound effects: `sfx/<name>.mp3`

| File | Used by | What it should sound like |
|---|---|---|
| `air-whoosh.mp3` | `s.face` zooms, `s.zap` | A short, airy whoosh (~0.2 s) for snap zooms |
| `whoosh-thud.mp3` | `s.kick` (every full-screen graphic) | A whoosh that ends in a soft low thud (~0.5 s) |
| `riser-short.mp3` | title cards (`s.sfx.append((t, "riser-short"))`) | A ~1.6 s riser that peaks on the hit (`SFX_LEAD` starts it 1.6 s early) |
| `boom.mp3` | payoff numbers | A deep boom |
| `cash.mp3` | money lines | A cash-register ding |
| `click-pop.mp3` | `s.squash` (crab landings) | A short click or pop |

Where to get them:
- HeyGen's catalog, if your plan includes it: `env -u HEYGEN_API_KEY heygen audio --help` shows the sound-effects
  search; download one per name and convert it to mp3 (`ffmpeg -i in.wav -ar 48000 sfx/air-whoosh.mp3`).
- Any CC0 sound (freesound.org with the CC0 filter, kenney.nl). Credit it in CREDITS.md.
- Quick start from the shipped CC0 set (fine to begin with, tune later):
  ```
  cd skills/avatar-shorts/assets/sfx
  cp cc-whoosh.mp3 air-whoosh.mp3; cp cc-impact.mp3 whoosh-thud.mp3; cp cc-riser.mp3 riser-short.mp3
  cp cc-hit.mp3 boom.mp3; cp cc-ding.mp3 cash.mp3; cp cc-pop.mp3 click-pop.mp3
  ```

`reel.py build` stops with the list of missing names if a spec uses one that isn't there.

## Music bed: `music/tech-bed.mp3`

The default bed under every Reel: about 60 s of upbeat, clean background music, already faded in (`build` ducks it
under the voice and fades it out). Use any track you have the rights to (a royalty-free library, HeyGen's music
catalog on your plan, or your own). A Reel can point at another file with `"music": "path/to/bed.mp3"` in its
reel.json. `reel.py prep` stops with a clear message if neither exists.
