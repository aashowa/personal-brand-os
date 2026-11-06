# HeyGen: the avatar render

## Setup (once per machine)

- CLI: `curl -fsSL https://static.heygen.ai/cli/install.sh | bash` (installs `~/.local/bin/heygen` and verifies its
  checksum).
- Auth: `heygen auth login --oauth`. **You run this yourself** (a browser approval). OAuth bills your plan's monthly
  credits. An API key in `.env` (`HEYGEN_API_KEY`) bills API credits, a separate balance that is often 0. The env var
  overrides the OAuth session, so `reel.py` strips it from the CLI's environment. Check:
  `env -u HEYGEN_API_KEY heygen auth status` → `"type": "oauth"`. The session refreshes on its own.
- Unattended runs (a server, a schedule) need API credits: HeyGen refuses device OAuth in non-interactive mode.
- Your IDs go in `config.json` `heygen`: the look IDs (`env -u HEYGEN_API_KEY heygen avatar list --human`, then
  `heygen avatar looks list --human`), your voice clone's ID (`heygen voice --help` lists the voice commands) and your
  glossary ID (`heygen brand glossaries --help`).

```json
"heygen": {
  "voice_id": "your-voice-clone-id",
  "brand_glossary_id": "your-glossary-id",
  "avatars": {
    "a": {"id": "look-id-1", "cam_y": "40%", "real_mouth": false, "still": "brand-system/avatars/a.jpg"},
    "b": {"id": "look-id-2", "cam_y": "36%", "real_mouth": true, "still": "brand-system/avatars/b.jpg"}
  },
  "legacy": {}, "paused": [], "pin": null,
  "caption_fixes": {"Whisperspelling": "YourBrand"}
}
```

## Recommended default

`reel.py` DEFAULTS["heygen"] plus your config:
- Your digital twin looks (video avatars, not photo looks), one slot per outfit.
- Engine `avatar_iv`: sharper real lips and teeth than V (the engine test in the table below). Your voice clone at
  video speed 1.0, with voice C on the speech (§ Expressive voice).
- 9:16, 1080p. No motion prompt: IV refuses one on a video avatar, so `new()` adds `MOTION` (+ the real-mouth line for a
  slot with `"real_mouth": true`) only to a Reel set back to `avatar_v`. Expect calmer movement and fewer hand gestures
  than V.
- Split crop `cam_y: "40%"` per slot (36% for a look framed higher; tune it on the snapshot).
- Your brand glossary, see § Pronunciation.

Rotation: `reel.py new` gives each Reel the least-used slot (`AVATARS`, from `heygen.avatars`). Put all your twin
footage as Motion training under one HeyGen avatar group and point every slot at a look in that group; when you move
to new looks, map the old IDs in `heygen.legacy` so rotation and covers still count those Reels. Photo looks only when
you ask for one.

Cost: about 0.83 credits per second (30 credits for 36 s, 33 for 39.6 s). Renders take 3–4 minutes. `reel.py heygen`
prints credits before and after.

## What was tested (so it isn't re-tested)

| Variant | Result |
|---|---|
| Photo look, Avatar V, voice 1.1x | "A bit robotic". The speed-up is the cause; keep 1.0 |
| Photo look, Avatar V, 1.0x | Lips blur: the regenerated mouth is smooth and waxy |
| Photo look, Avatar IV + expressiveness high | Sharpest lips, most animated, very even teeth |
| Video twin, Avatar IV (no motion prompt allowed) | Sharper lips, calmer movement. Liked |
| Video twin, Avatar III | Barely opens the mouth. Drop it |
| **Video twin, Avatar V + motion prompt** | **The first default: natural gestures, slightly softer lips** |
| A newer twin, Avatar IV, either voice | Bright even "veneer" teeth and pouting lips. Worst |
| That twin, Avatar V + its own voice clone | Teeth mostly covered, natural lip shapes |
| That twin, Avatar V + relaxed-lips motion prompt | Picked at first, then rejected: hiding the teeth looks really fake, it isn't the person's real mouth |
| **That twin, Avatar V + "keep the real mouth" prompt** | **Picked**: motion prompt + `MOUTH` in `reel.py` (keep the real mouth exactly as in the training footage: own teeth, lip shape and facial hair; natural, small mouth movements; never smooth, whiten or reshape the mouth). Teeth show; still a little whiter and more even than the real ones. Also tried: calm/minimal, the twin's own voice, "show the real teeth, don't whiten" (most teeth) |
| That twin, Avatar V + two stricter mouth prompts ("upper teeth only, lower teeth behind the lip", "small openings, never a full lower row") | No real change: same big upper row and jumbled lower teeth on some words. Prompts can't fix a twin's teeth; the twin itself is the limit (a 698x1280 portrait source, face small in frame; HeyGen asks for 1080p/4K, 16:9, face ~50% of the frame). Fix = new training footage |
| Photo look, Avatar V + real-mouth prompt vs Avatar IV + expressiveness high | Bad ("that was an image"). Photo looks stay out of Reels |
| **A twin as a look in the one group (all footage as Motion training) vs its old separate avatar**, same audio + real-mouth prompt | **Group look: teeth a little more natural.** Point every slot at the group's looks |
| Every group look on one hook, real-mouth prompt on all | Pick per look: one looked best, one still had bad teeth and went into `paused` |
| **Group look, Avatar IV (no motion prompt) vs Avatar V + real-mouth prompt**, same voice-C audio | On V "my mouth does not look like me". **Avatar IV was a lot better**: sharper lips and teeth; no hand gestures. Now the default |
| Video twin, Avatar V, default prompt | The mouth didn't look like the person |
| Video twin, Avatar V + "keep the real mouth" prompt, against two other looks with the same prompt | Picked on that look |

To test a change (avatar, engine, voice), render the first sentence only (~5 s, ~3–5 credits each), then compare
mouth crops side by side at the same moments, never a full Reel. Engine rules: `expressiveness` is photo-avatar,
Avatar IV only; `motion_prompt` works on photo avatars either engine and on video avatars only with `avatar_v`.
`heygen video create --request-schema` shows the current body.

## Expressive voice (default)

A plain clone sounds dull, with "no ups and downs". `video create` has no expression setting for a professional voice
clone, but `heygen model audio tts create` has `pitch_variance` (1.0 = the voice's default). DEFAULTS heygen has
`"tts": {...}`, so every new Reel gets its speech made that way first (`heygen/voice-tts.wav`), then the avatar lip-syncs
to it (`audio_url`). Speech costs ~0.2 credits/s. The glossary only works on scripts, so `reel.py` reads its terms and
puts the respellings into the speech text (`spoken()`); script.txt keeps normal spelling. Remove `tts` from a reel.json
for the old flat voice.
Pitch range on the same hook (5-95% range in semitones, Praat via parselmouth): the presenter on camera 7.9, the
avatar's flat voice 9.5, a high-energy creator's Reel 15.2, pitch_variance 1.5 13.2, 2.0 13.1 with faster wobble.

**Voice C (default).** At pitch_variance 1.5 and speed 1.0 the voice still had slow energy. After updating the clone
itself (same ID), take B (`speed` 1.1) and take C were compared on the avatar, and C won:
`"tts": {"pitch_variance": 1.8, "seed": 7, "speed": 1.2}`. On C, 155 words ran 38.4 s after pause cuts = 242 wpm
(Nick about 244, adilet about 212); the avatar test on the hook: B 221, C 242. On the same two lines, after pause cuts:
old voice at 1.0 = 171 wpm, updated voice at 1.0 = 189, B = 193, speed 1.2 = 207. The TTS speed is not the video
`voice_settings` speed that sounded robotic.

## Pronunciation (brand glossary)

Every render sends your `brand_glossary_id` (`config.json` `heygen.brand_glossary_id`), so scripts keep normal
spelling. On the tts path (the default) `reel.py` applies the same terms to the speech text itself.
Terms worth having from day one: MP4 → "em pee four", and your business, product and own names, each respelled the
way they should sound.
GITHUB → "GitHub": a CTA word written in capitals ("Comment GITHUB") came out as "gihub" while "GitHub" in normal
case was fine. A new capitals CTA word that isn't a plain English word gets a glossary term before the render; whisper
hearing it wrong ("gihub") is the tell. Fix a Reel that slipped by re-rendering only the CTA sentence (~5 credits) and
splicing it in at the pause before "Comment" (the CTA's zoom punch hides the cut).
plugin → "plug-in", plugins → "plug-ins": the avatar said "plugins" wrong while whisper still heard "plugins", so only
your ear catches this one.
HeyGen terms are case-insensitive (it rejects "plugins" + "PLUGINS" as duplicates), and `spoken()` matches the same way,
so one entry covers a capitals CTA word.
- Add a term: `env -u HEYGEN_API_KEY heygen brand glossaries update <id> -d '{"terms":[...]}'`. `terms` replaces
  the whole list, so read it first (`heygen brand glossaries get <id>`) and send every term.
- Write the respelling as one plain word. A hyphenated stress spelling (syllables in capitals) came out as slow,
  separate syllables; one plain respelled word was right. Test it with `heygen voice speech create` on the respelling
  (~1 credit) before a video.
- It changes the voice only. Whisper spells what it hears, so add those spellings to `caption_fixes`
  (`heygen.caption_fixes` in config.json for your names, or a reel.json for one Reel).
- `voice speech create` ignores the glossary: patch text uses the respelling.

## Patching one phrase (no re-render)

Say the avatar said "MP4" as "mezzo per four" (whisper and gpt-4o-transcribe both heard it). When the phrase sits
under a full-screen graphic, only the audio matters:
1. `env -u HEYGEN_API_KEY heygen voice speech create --text "Then they're stitched into an em pee four." --voice-id <voice> --speed 1`
   (~1 credit; same voice, Orca engine). Download `data.audio_url`, transcribe it to confirm.
2. Map the phrase's final times back to raw `heygen/avatar.mp4` time (the `keep_ranges` of prep), keep the original as
   `avatar-raw.mp4`, and splice: TTS speech (edges trimmed, level-matched with ebur128) replaces the raw audio range,
   and the picture for that range is stretched to the new length. Re-run `prep`.
If the phrase is on a face beat, re-render the whole Reel instead (lips must match).

## Pace

Voice C (TTS speed 1.2, above) is the limit; never speed the picture or the finished audio. Pace comes from
`reel.py prep`: every pause over 0.18 s is cut to ~0.1 s on frame boundaries shared by picture and sound (39.6 s →
32.9 s on a test Reel), and snap zooms hide the jumps.
