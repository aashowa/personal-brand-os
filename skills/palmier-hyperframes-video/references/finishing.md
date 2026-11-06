# Finish from the approved cut

Pipeline steps covered here: 03 audio polish, 06 SFX, the opt-in music bed, 08 export and the one-command Final.
Targets live in [the-look.md](the-look.md).

## The short version
1. **03 Audio polish:** `scripts/audio_polish.py SRC.mp4 polished.mov` brings dialogue to ≈ −17 LUFS with peaks ≤ −6 dBFS
   (a worked episode: −17.3 LUFS, −6.0 dBFS, LRA 3.7), then import it and `swap_clip_media` the clips. If the music bed was already mixed,
   raise it by the same gain the dialogue got (for example +4.2 dB) to keep the approved balance. Denoise only if noise is real.
   Leave platform loudness to Final.
2. **06 SFX:** `scripts/sfx.py SPEC.json sfx.wav --cues cues.json` builds one stem from the placed graphics (+ typing/Enter cues).
   Import it, drop it at frame 0 on an `SFX` track.
3. **Music bed (opt-in, needs a licence or a paid-generation approval):** flat ~−20 dB under speech. If an export speed-up
   follows, pre-slow each section of the stem by 1/speed so the music keeps its tempo after Final (a worked episode: mixed in output time
   with sidechain ducking, then mapped back with `atempo` 1/1.15, 1/1.2, 1/1.08; round trip matched the approved preview within 1.3 dB).
4. **08 Export in the app at 1×**, locked specs from the-look (export only when the user asks).
4b. Palmier's H.264 export is the 1× master for Final (check its bitrate with ffprobe; text sharpness is set here).
5. **Final:** `scripts/finish.py export_1x.mp4 final.mp4 --speed "0:413:1.15,413:935:1.2,935:end:1.08"`: speed once
   (picture + audio, pitch preserved), −14 LUFS / −1 dBTP two-pass loudnorm, verification report, copy in ~/Downloads.
   A failed check exits non-zero; fix the cause, don't relabel the file.


## Audio

Measure before adding processors. Fix an identified issue: noise cleanup for real background noise, gentle presence EQ for dull speech, modest compression for uneven delivery, and final loudness/peak control. Leave natural breaths; word-timestamp cleanup is not an audio-quality check.

Keep speech, music and SFX separately editable until the final mix. A quiet bed must remain beneath speech; typing clicks and transitions should mark actual actions, not fire continuously. Retain stock licenses or document original synthesis. Do not claim a numerical waveform check proves the music sounds good.

In the worked video, the original assembled speech measured−17.86LUFS with a+0.14dB true peak. A quiet original96BPM bed and licensed bundled click/whoosh were mixed, then mastered. Later refinement used+1.2dB around2.2kHz and gentle1.5:1 compression; the resulting AAC measured−16.33LUFS/−1.43dBTP. These are evidence for that recording, not a filter preset to apply everywhere. Avoid overprocessing or repeated lossy/mastering passes.

A continuous mastered soundtrack can be imported into the final Palmier timeline while source dialogue is muted there. Preserve the source stems/previous timeline, and check that muted originals do not double the voice. When the speech edit changes, rebuild the master from the matching approved audio.

## Color and framing

Grade talking-head footage separately from designed assets. Use `inspect_color` plus visual frames; a bright cyan monitor can dominate a scope even when skin is reasonable. Lift only what needs it, recover highlights, and tame distracting hues selectively. Do not apply a cinematic LUT across brand colors or recolor a supplied result image without instruction.

In this run a small exposure/shadow lift, mild contrast and reduced cyan saturation improved the presenter while preserving the examples. Frame and compare both skin and highlights; scope improvement alone is insufficient.

Changing1920/1980-height canvases can alter auto-fit. Confirm the rendered edges and avoid stretch. If a crop exposes thin black borders, inspect crop and transform together. The run's1080×1980 footage needed a small centered vertical crop/size compensation for1080×1920; another source may need something entirely different.

## Global speed and exact revision mapping

For “a little faster,” offer/state a modest choice such as1.03–1.08× and judge the delivery; the approved example used1.06×. Apply it once to the entire composed picture and all audio with pitch-preserving `atempo`. Burned captions/type animation then stay aligned. If keeping captions separate, rescale their timings too.

When an already-sped version is approved, distinguish **new total speed** from an incremental multiplier. State, for example, “increase from1.06× to1.08× total,” and render that total once from the layered source. Do not accidentally multiply the two speeds.

For a constant speed `s` with no additional offset, `source_time = delivery_time × s`. Example:16.8s of a1.06× delivery maps to17.808s of its **edited layered source**, not necessarily the original camera file. Use the edit map for the latter. Never stack another1.06× pass on the sped review unless the user actually requested a second speed increase.

Compare stream durations. Fractional-frame rounding and audio-filter tails can produce a small difference; verify that the last spoken word survives and the last picture holds appropriately. Do not truncate audio merely to make a duration field look tidy.

## Export

Probe the supplied files. “Shot in4K” does not mean the handed-over recording is4K. In the example it was1080×1980. Exporting a4K upscale would not restore absent detail. For an actual4K source, preserve it through editing and choose delivery resolution according to the requested platform/use; verify current platform requirements when relevant.

A practical high-quality social delivery is H.264, vertical1080×1920, source-appropriate frame rate, yuv420p, correctly tagged color, AAC audio and fast-start MP4. Set quality from the source and intended delivery. The worked master used slow x264/CRF14, High Profile Level4.2, a25Mbps **ceiling** and50Mb buffer, requested AAC320kbps/48kHz. Its measured average video rate was about6.13Mbps; do not present a maximum/requested bitrate as the actual rate. Tag BT.709 only when the source/output is actually SDR BT.709; HDR needs proper conversion, not relabeling.

Keep a layered-source export so final quality does not depend on a chain of compressed review files. Example command pattern (replace paths/settings deliberately):

```bash
ffmpeg -i layered-source.mp4 \
  -vf 'setpts=(PTS-STARTPTS)/1.06,fps=30' \
  -af 'atempo=1.06' \
  -c:v libx264 -preset slow -crf 14 -profile:v high -level:v 4.2 \
  -pix_fmt yuv420p -maxrate 25M -bufsize 50M \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart social-master.mp4
```

Add any needed EQ/mastering once, based on measurements. The example deliberately does not prescribe processing an already mastered soundtrack again.

## Verification that catches real problems

- `ffprobe`: actual dimensions/fps/codecs, per-stream start/duration, file size and color metadata.
- Full `ffmpeg -v error -i FILE -f null -` decode.
- Loudness/true peak of the final encoded audio; ensure no added clipping or lost ending.
- Exported frames: opening mark, partial/completed search typing, product cards, last prompt line, result grid, CTA and user-reported patches. Inspect the boundaries around each patch and a phone-sized view.
- Playback/listening: syllables at speech joins, lip sync, pace, music/SFX balance, frozen or flashing frames and the last word. If unavailable, state the exact checks completed and do not claim continuous audiovisual review.

Technical passing checks do not force endless re-renders. Repeat only for an actual defect or changed material. If a render exposes oversized text, wrong layering, color flashes or black edges, repair that cause and verify the affected sequence again.
