---
name: content-pixel
description: "Design your YouTube thumbnails from a title and concept brief."
---

# Content Pixel: Thumbnail Designer

Used in the packaging step of `WORKFLOW.md`, after `content-slate`.

## The job
Turn `content-slate`'s thumbnail concepts into **production-ready thumbnail assets** that earn clicks at mobile size.

## Inputs
1. **The Click Package** from `content-slate`: thumbnail concept descriptions
2. **The brand sheet** (see below)
3. **Recording stills / screenshots** from the episode (when available)

## Primary outputs
1. **2-3 thumbnail variants** per episode (for A/B testing)
2. **Thumbnail rationale**: why each variant works
3. **Concept critique**: flag if a concept is visually unworkable before executing

## Brand and packaging rules (read first)
- **Brand:** `brand-system/brand-sheet.html`. Kit default: paper #F7F7F5, ink #141412, marker yellow #FFD43B, terracotta
  #C4501B, Bricolage Grotesque + JetBrains Mono. Use your own values if you changed the sheet.
- **Composition and words:** `research/packaging/PLAYBOOK.md`, learned from top channels and kept current. In short:
  calm closed-mouth face, no cut-out outline, one hero object, 2–5 words in sentence case, a proof line big enough for
  160x90, one arrow, lots of empty space.
- **References:** run `python3 research/packaging/pull.py` first; pick 2–3 outliers from
  `research/packaging/<channel>/sheets/` that fit the concept. Describe their composition in the prompt; don't feed other
  creators' thumbnails to the image model (it copies faces and designs).

## Workflow
1. Receive the concept brief; read PLAYBOOK.md and the latest reference sheet.
2. **Critique first**: is this visually workable at 160x90? Flag issues before executing.
3. Inputs: a real frame of the creator from this episode (same outfit; crop out the hands), the real logos and the one
   real screenshot line the concept needs.
4. Write a spec and run `scripts/thumbs.py SPEC.json` (Kie.ai GPT Image 2.5 Sunburst, 10 credits each). Work out the cost
   first (10 x variants) and ask with that number, unless thumbnails were already requested with a budget.
5. Check each at full size and 160x90; fix misspelled small text locally; deliver 3 variants for Test & Compare.

Example spec (`episodes/<slug>/packaging/thumbs-v1.json`, refs in `packaging/thumbnail-refs/`):

```json
{"refs_dir": "thumbnail-refs", "out_dir": ".", "prefix": "thumbnail-ep01", "cap": 30,
 "variants": {
  "v1-icon": {"refs": ["me-frame.jpg", "app-logo.png"],
              "prompt": "Create a 16:9 YouTube thumbnail on light grid paper (#F7F7F5) with ink (#141412) type. Left third: the person from image 1, calm, mouth closed, slight confident smile, eye contact, no outline, lit into the scene. Right: the app icon from image 2, large and glossy, the one hero object. Top right, three words in sentence case, Bricolage Grotesque bold: \"runs for free.\" with a marker-yellow (#FFD43B) highlight behind \"free\" only. One hand-drawn ink arrow from the words to the icon. Lots of empty space. No other text."},
  "v2-proof": {"refs": ["me-frame.jpg", "proof-line.png"],
               "prompt": "Create a 16:9 YouTube thumbnail on light grid paper (#F7F7F5) with ink (#141412) type. Left third: the person from image 1, calm, mouth closed, no outline. Right: the screenshot line from image 2 as the one hero object, cropped to that line and large enough to read at 160x90. Top right, three words in sentence case: \"$0 a month.\" with a marker-yellow (#FFD43B) highlight behind \"$0\" only. Lots of empty space. No other text."}}}
```

## Quality checks (non-negotiable)
- [ ] Readable at mobile size (160x90px)?
- [ ] One clear focal element?
- [ ] Real visual material (not stock/abstract)?
- [ ] Text overlay 2–5 words, sentence case (packaging playbook)?
- [ ] Brand colors used correctly?
- [ ] Would raise a question or signal a result to the viewer?

## Tools
- `scripts/thumbs.py`: Kie.ai thumbnail variants from a spec (receipt with task ids and credits). Needs `KIE_API_KEY` in
  the repo `.env`, `ffmpeg`, and the `avatar-shorts` skill beside this one (it reuses its Kie client, `cover.py`).
- Claude Vision: review and critique concepts and results

## Output format
Save in the episode folder, `episodes/<slug>/packaging/`:
- `thumbnail-{episode}-{variant}.jpg` (1920x1080, under 2 MB), `thumbnail-raw/`, the spec and its `-receipt.json`
- the rationale per variant goes in `youtube-upload.md` (Thumbnails section)
