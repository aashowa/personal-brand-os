# Read 1 · The look (what), the same in every app

Numbers and specs every edit is held to. The brand (colours, fonts, logos) comes from the channel's own brand file. The
kit's default is `brand-system/brand-sheet.html` at the repo root: paper, ink, marker #FFD43B, two side accents (terracotta
#C4501B and cobalt #2251D1), Bricolage Grotesque + JetBrains Mono, and Instrument Serif Italic for the intro's hook line,
title and CTA words. Swap in your own brand there. These numbers are defaults: a user's call overrides them, and the
decision is written in the episode notes.

## Channel defaults (decided once; don't re-ask, apply)
| Item | Decision |
|---|---|
| Hook | Pre-roll of the screen: typing the real prompt into the AI app's chat bar, Enter on the spoken word, zoom to the result. Explained later in the video. It plays inside the studio intro: the app in a floating window beside the camera card, then the proof push. |
| Speed at Final | Hook 1.15×, camera intro 1.2×, everything after 1.08×, pitch preserved. |
| Music | Intro bed only, under the hook and camera intro, ducked under speech; plus a quiet bed (~-26 LUFS) under a silent screen stretch held at 1x (for example a result and a prompt typed while the recording's mic was paused). ElevenLabs Music (~8 credits per 40 s, dry run first, ask with the number); pre-slowed per speed section. |
| Camera intro | Studio intro: the first ~60-70 s as one HyperFrames composition on the paper canvas with two corner glows, the camera as a moving rounded card, white floating cards, the hook line and title in Instrument Serif Italic word by word, every word on its spoken frame, the last ~3 s back to the episode's framing; never over the speaker's face. Beats, numbers, pipeline: [studio-intro.md](studio-intro.md). |
| Graphics | Real logo tags above the corner camera on first tool mention (Claude, ChatGPT, Codex, Gmail, QuickBooks…), one at a time. Callout cards and a marker highlight on the word or number that matters. Brand paper/ink, Bricolage + JetBrains Mono. |
| Captions | None on long-form. Shorts only, burned in. |
| Privacy | Tight blur on client and business names, account IDs, phone numbers, addresses, private links (Maps, Drive), API keys and the account email. Your own brands, their public contact address and the report numbers you choose to show stay visible. |
| Camera | The clean camera file as the body's corner overlay and the intro's camera card (never the laggy baked-in webcam), smoothed where it stutters; a speaker card over frozen stretches. Whenever the speaker talks straight to the lens in the body, the camera goes full screen pushed in on the face with wall cards beside it, cued on the words; runs are found by gaze (face height + head pitch per frame, checked on face crops); runs under ~4 s stay on the screen. |
| Speech | Every um/uh out; pauses ≥ 0.45 s cut to ~0.26 s. |
| Cut density | Cut what is dead (waits on the agent, retakes, fumbles, OBS captures); keep complete thoughts: the why, the stakes, tips and how-to bridges. A cut that kept 31% of the recording felt too harsh; ~45% read well. |
| Review | The user reviews taste only: every gate runs first. Export only when they say "export"; the final lands in the episode folder plus ~/Downloads. |

## Story
| Item | Target |
|---|---|
| Hook | Open on the result, not a greeting: the system working on screen in the first 2 s. Pre-roll 10–15 s, explained later. |
| Recreated UI | Only when the capture missed the action (e.g. chat bar below the OBS crop). Exact real text, real result after it; label it a recreation in the notes. |
| Retakes | Keep one complete take per beat; drop false starts, repeated lines, OBS window captures, waits on the agent. |
| Length | Long-form ≤ ~20 min. |

## Speech and pace
| Item | Target |
|---|---|
| Fillers | Remove um / uh / ah / er / hmm, each verified on its own. Never remove meaningful words ("like", "so", "and"). |
| Pauses | Gaps ≥ 0.45 s between speech → ~0.26 s (0.13 s kept each side). Keyboard clicks and breaths count as pause, not speech. |
| Pace | Measure words per minute after cuts. Final ~190–205 wpm. Body speed 1.03–1.08×; a slow camera intro up to 1.2×; never past ~225 wpm. |
| Speed | Applied once, to picture + audio together, pitch preserved. |

## Picture
| Item | Target |
|---|---|
| Zoom / pan | 0.7 s eased moves, still holds, cued to the spoken line. ≤ 2.2× on a 4K source for 1080 delivery. |
| Corner camera | 25 % width, bottom-right (centre 0.875, 0.879). Must cover any baked-in webcam completely, at every zoom. |
| Camera health | ≥ 24 real fps. Stutter (copies while moving) → interpolate. Frozen ≥ 1 s → cover with a speaker card, never a frozen face. |
| Grade | Camera only (long-form, explainer). Skip for screen recordings and raw/TikTok style. Brand artwork is never graded. |
| Privacy | Blur only what identifies or exposes: client/business names, account IDs, phone numbers, addresses, links carrying IDs, keys/tokens. Tight boxes on those words (`privacy_scan.py`), never whole panels, sidebars or pages. The user's own businesses stay visible. Check every app screen, every frame range. |

## Graphics and captions
| Item | Target |
|---|---|
| Purpose | Every graphic explains or proves something said. Never cover slide text that already says it. |
| Motion | Entrance 9–10 frames with slight overshoot + blur-in; exit 7 frames; hold ≥ 2.4 s (80 frames at 30 fps, before speed-up). |
| Tool mentions | Logo tag above the corner camera on first mention; real logos only (recoloured brand glyphs). One tag on screen at a time, box ≥ 13% wide and ≥ 11% tall, its visible card ≥ 1.5% from every frame edge (`qa_timeline.py` checks all three). |
| App screens | Full screen by default: show the entire screen and zoom only when something important happens. Zoom 1.5–2.2× only on key moments, a few seconds each: the result or number, the exact field or button to use, the line to copy (`zooms.py`). As a guide, about 13 zooms and ~2 min zoomed in a 14 min episode. |
| Highlight | One marker highlight per moment, on the word/number that matters; it must follow any zoom. |
| Captions | Long-form: no running captions. Text appears only as animated callouts on the important word or number (highlight, card). Shorts: burned in, 1–5 words, ≤ 32 characters, broken at punctuation/pauses; skip spans where the picture shows the same words. |

## Sound
| Item | Target |
|---|---|
| Dialogue (in app) | ≈ −17 LUFS integrated, peaks ≤ −6 dBFS: headroom for music and SFX. |
| Music bed | Opt-in. Flat ~−20 dB under speech; an intro bed may sit higher if it ducks under the voice. Licensed or generated with receipt. |
| SFX | From placed graphics: pop on pop-ins, short whoosh on slide-ins, typing under on-screen typing, key press on Enter. Each hit peaks ≈ −24 dBFS. |
| Final master | YouTube / Shorts: −14 LUFS integrated, ≤ −1 dBTP. |

## Delivery specs (locked)
| Platform | Spec |
|---|---|
| YouTube long-form | 16:9, 3840×2160 if the source is 4K (else 1920×1080), source fps, H.264 High, yuv420p, BT.709, AAC 320 kbps 48 kHz, faststart. |
| Shorts / Reels / TikTok | 9:16, 1080×1920, source fps, same codecs. Captions burned in; keep text out of the bottom ~20 % and right ~15 % (platform UI). Check the platform's current maximum length before cutting. |
| Files | Final in the episode folder + a copy in ~/Downloads. Keep the 1x layered project; never edit from a compressed review file. |
