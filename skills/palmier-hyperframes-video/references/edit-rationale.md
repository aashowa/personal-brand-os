# Case study 1: a short product-graphics tutorial

This is a decision record, not a timing preset. The source was a 97.867-second talking-head recording about turning a weak
social post into strong product graphics. The approved story remained **weak post → Pinterest reference → original product →
prompt → finished designs → follow/comment CTA**. Preserve the story and the user's actual examples when adapting this
workflow.

| Trigger / observation | Decision | Why / transferable lesson |
|---|---|---|
| Recording arrived before visual assets. | Review sampled frames and the full transcript; import and read back the media library before editing. | Identify missing evidence first. A successful import is not proof of a placed clip, finished edit, or continuous playback review. |
| Nine named reference files arrived. | Assign weak example, Pinterest page, selected pin, product photo, and four results distinct roles; use one duplicate bad example. | Filenames help inventory; visual inspection establishes meaning. Preserve exact images and do not describe the blurred product background as a white cutout. |
| Prompt retakes, repeated results intros, abandoned CTA and dead air. | Assemble one complete take per beat into a separate 50-second timeline while another agent builds the reveal. | Parallelize independent graphics and speech work; one agent owns timeline mutations. Keep original media and an uncut timeline. |
| Local source transcription and cloud timeline word timings disagreed. | Recheck full-source word timings against actual quiet spans; revise padded boundaries and add short audio fades. | ASR timestamps are evidence, not ground truth. Never cut merely at a rounded sentence timestamp. |
| User requested tighter delivery. | Remove 16 redundant/filler words and shorten eight measured gaps: 50 → 43.667 seconds. | Remove hesitations without changing meaning. Keep grammatical words such as “like”; do not manufacture replacement speech. |
| User approved that cut but identified the menu/photo pause. | Duplicate and remove only eight frames: 43.667 → 43.4 seconds. | Treat narrow approval as the new baseline. Fix the named problem without reopening accepted decisions. |
| Four results share nearly identical composition. | Matched color switches under continuous gentle movement, followed by a comparison grid. | The color change is the visual event. Align face/glass; generative movement could distort branding and is unnecessary. |
| Spoken edit was still moving; prompt text was unavailable. | Defer typing, then reconstruct the spoken prompt with permission and label its provenance. | Lock narrative before tightly timed graphics. Do not claim reconstructed text is the original generation prompt or invent an AI interface. |
| Long instruction sections needed visible evidence. | Show search page, selected reference, attachment cards, prompt, and results at corresponding speech cues. | Every graphic should explain or demonstrate something. Decorative motion alone does not repair weak coverage. |
| First finish needed captions and sound. | Use short captions except over the full prompt; mix original quiet music and licensed effects beneath speech. | Avoid competing text. Preserve audio provenance and intelligibility; no fabricated performance metrics or automatic DM promises. |
| User wanted their own brand identity and stronger motion. | Apply exact brand colors/logo, a thick outlined two-stroke X, square forms, and typing inside the real Pinterest query area. | Brand the framing system while preserving the product artwork's own colors. Native SVG/icons and code animation keep text and geometry exact. |
| User explicitly requested a Kie.ai experiment with US$5 ceiling. | One Grok I2V request used 27 credits, US$0.135; no retries. | Generation is conditional on a useful role and explicit budget. Research price first; record actual charge separately from estimate. |
| Generated reference-led output was horizontal, despite requested vertical ratio. | Use it as a moving footer beneath deterministic graphics. | Inspect actual output dimensions. Fit a useful result to its strengths instead of stretching it or spending automatically on retries. |
| User found 12–18 seconds visually static. | Alternate presenter → product/reference cards → presenter. | Human presence can provide better variation than new generated footage. Preserve speech and approved timing. |
| Presenter looked down before the prompt. | Cover the glance with existing graphics. | Use coverage to hide distraction without deleting good audio or changing the narrative. |
| That cover caused a reference-card flash after “type this prompt.” | Replace it with a brief hold on the opening prompt panel, then continue typing. | The next visual should fulfill the spoken promise directly. Evaluate seams, not just attractive standalone scenes. |
| User asked for slightly faster pace, better audio and grade. | Apply 1.06× to the assembled sequence, pitch-preserving audio tempo, restrained dialogue processing, and a mild presenter-only grade. | Speed captions/graphics together. Keep artwork unchanged. Values were scene-specific decisions, not universal presets. |
| Delivery/export settings suggested higher resolution than working media. | Treat the verified 1080 social master as the deliverable; do not call it native 4K. | Metadata and actual pixel content outrank preset names. Upscaling cannot recover missing detail. |

## Exact revision ledger

These are historical settings from this video, not defaults for future projects. Times below are in the 43.4-second layered edit unless marked as delivery time.

| Revision | Exact adjustment and reason |
|---|---|
| Initial cleanup | 97.867 → 50.000 seconds. Retain the strongest complete prompt take, one results introduction and final CTA; preserve the uncut source. |
| Filler pass | Remove 16 tokens across repeated “kind of,” “put up,” and similar restarts, a redundant “And,” “more” in “way more better,” and “And uh.” Word removals totaled 159 frames; eight waveform-verified pause cuts totaled another 31 frames. Result: 43.667 seconds. |
| Menu/photo seam | Quiet interval measured 12.874–13.248 seconds in that draft. Remove frames 388–396, leaving roughly 0.108 seconds of breathing space. Result: 43.400 seconds; keep both words. |
| Result insert | Build 8.5 seconds of matched green → mustard → red → blue artwork plus a grid. After speech changes, keep it continuous at 1.028× over frames 917–1165, instead of allowing word edits to chop its animation. |
| Caption/CTA polish | Full subtitle source has 34 cues. Use 25 visible captions, omitting nine prompt cues because the typing panel already displays those words. Native caption size 52 rendered too large; reduce to 28. CTA sizes 76/44 became 44/26; separate their tracks and remove the heavy outline. These are Palmier sizes from this run, not universal screen-pixel sizes. |
| Brand revision | Replace the initial thin strike with a thick cream-edged red X drawn in two strokes. Replace the default layout surfaces with the actual brand colors and supplied logo/font. Preserve the four product result colors. Type the exact search query inside the original screenshot’s search field; add quiet typing clicks during that action. |
| Kie integration | Requested 6 seconds at 720p/9:16; received 2128×416, 6.0417 seconds with audio. Mute that audio, preprocess a 30fps loop at 1.25× and use a full-width band at y=1740–1920 under the three graphic compositions. Do not stretch it into vertical footage or generate the exact UI/X. |
| Presenter variation, v3 | Reveal the face at 12.000–14.400; show product/reference cards at 14.400–16.600, including “attach it”; reveal the face again at 16.600–18.367. The existing footage solved the static section without another Kie charge. |
| Glance cover, v4 | Cover 17.667–18.367, frames 530–551, initially with the product cards, to conceal the glance reported near 18.01 seconds. Audio and total duration unchanged. |
| Speed/audio/grade, v5 | Apply 1.06× globally with pitch preservation, yielding about 41 seconds. Presenter grade: +0.08EV, contrast 1.035, highlights −0.15, shadows +0.05, whites −0.04, saturation 0.98, temperature 6600K, cyan saturation scale 0.82. Audio refinement: +1.2dB at 2.2kHz, 1.5:1 compression and loudness mastering. Leave graphic colors unchanged. |
| Continuity correction, v6 | The v4 cover briefly returned to old reference cards after “type this prompt.” Replace frames 530–551 with a hold on the upcoming prompt panel. Its original typing begins at frame 551. At 1.06×, the direct prompt entrance is about 16.67 seconds. |
| Hold-format correction | The first PNG hold changed blue/cream tones relative to the MP4. Replace it with a 21-frame video hold derived from the prompt video’s first frame, using matching color handling. Check the actual seam before declaring the flash fixed. |
| Social master | Render from the corrected layered-source export with the approved speed/audio chain, not by recompressing the v6 review. Actual deliverable: 1080×1920, 30fps, approximately 41 seconds, 32.7MB. The supplied camera file was only 1080×1980 despite the original 4K capture claim. |

No automatic prompt DM workflow was configured, no video was published, and the unused Kie budget was not spent. Skill creation was deferred until the user explicitly requested it after the edit. This preserves the difference between a suggested next step and authorized work.

## Operational lessons

- Snapshot/duplicate before each material revision; retain approved cuts and editable layers alongside flattened deliveries.
- Initialize MCP, bind the intended project, then select/read the timeline. Transport/session success does not establish editor availability.
- Re-read track indices after insertion/deletion. A replacement initially targeted the wrong lane; undo and verify the full transcript before proceeding.
- Native caption sizing produced oversized text in exported frames; inspect the actual export and correct it. Tool success is insufficient.
- Same-time CTA text entries on one auto-created track overwrote each other; create separate layers. After replacing a graphic with different dimensions, reset its inherited crop/transform and inspect for thin black borders.
- Silence-removal's “no dead air” response did not resolve the reported pauses; use the waveform and speech context. The recording's local and cloud transcripts disagreed, so neither provider's label established accuracy.
- MCP setup used `codex mcp add palmier-pro --url http://127.0.0.1:19789/mcp`, followed by registration readback and a real initialize/list-tools check. The endpoint is one machine's observed configuration, not a portable assumption.
- A PNG hold and encoded MP4 may differ in color interpretation. Compare the transition visually and use a matching video-derived hold when needed.
- Full decode, duration, waveform, loudness and true-peak checks establish technical properties. They do not establish natural speech, pleasing music, or full audiovisual playback quality; state what was actually reviewed.

Keep the same kind of record for your own runs: an asset brief, a trim report, each handoff, the sound provenance and any
generation receipt, in the episode's notes folder.

# Case study 2: a long-form screen-share episode

24:54 OBS screen recording with a baked webcam, plus a silent clean-camera file → 17:51 at 1×, about 16:29 after Final.

| Trigger | Decision | Lesson now built into the pipeline |
|---|---|---|
| Camera file had silent audio | Synced by motion correlation against the baked webcam crop (+2 frames, no drift) | Intake: `footage_health.py --sync` |
| Palmier showed random black stretches | H.264 GOP30, no-B intermediate, swapped in with `swap_clip_media` | Intake gate flags HEVC long-GOP before any clip is placed |
| User wanted the result first | Screen hook: recreated chat-bar typing (capture missed it), real result, highlighter tracking the zoom | the-look: hook rule + recreation labelling |
| User asked for more motion | 19 brand PNGs with keyframed pop/slide, logo tags on first tool mention; 3 removed for covering slide text | QA gate: never cover text that already says it |
| Nested timeline refused speed | Speed moved to a one-command Final (1.15 / 1.2 / 1.08) | `finish.py` |
| User found "um"s and long pauses | Acoustic filler detection + per-snippet check (15 removed), word-gap pauses (71 cuts) | Proof gate `speech_gaps.py --gate` before any review |
| User saw the camera lag | OBS dropped frames under load: interpolation for stutter (72 → 2 choppy seconds), speaker card over frozen stretches | Intake gate reads stutter/frozen; `smooth_camera.py` is frame-exact (one-graph ffmpeg drifted ±51/145 frames) |
| Intro felt slow | Measured pace (wpm) before choosing speeds; camera intro 1.2× only | the-look: pace targets |
| Music wanted under the intro | Generated bed (8 credits, approved), ducked, pre-slowed per speed section | finishing: music bed + pre-slow |
| v5: the user asked for no running captions | The 891-cue caption track was removed; callouts carry the important words | the-look: no long-form captions (Shorts only) |
| v5: "blur only the sensitive info" | 99 panel blurs were replaced with ~1,800 OCR-placed word boxes; clips were split where content scrolls; flick-scrolls blur only the moving area | `privacy_scan.py` (cache, motion-aware) + `masks_apply.mjs` + `--check` |
| v5 reviewer: API key fragments and the account email showed | Whole-line rule for key prefixes and hex IDs; email rule (public info@ kept) | `references/privacy-terms.txt` |
| v5 reviewer: two tags stacked, tiny intro tags, demo left at 1× | One tag at a time, tag ≥ 13% × 11%, 1% edge margin, a zoom on small UI text | `qa_timeline.py`, `zooms.py` |
| v5: Palmier stalled for 30 min | Swap was full and hundreds of short MCP sessions had run; the user closed apps, Palmier was force-quit after the autosave and reopened, and nothing was lost | Preflight swap; one long session per batch |

The first pass missed audio polish, camera grade, SFX and a fresh-eyes round; v5 added them.
