# 5c Converge · the fresh-eyes review, fast

A single reviewer once looked at 81 frames on 7 sheets and took 2 h 10 min and 440k tokens. Images kept dropping out of
its context, so it re-viewed them. Half of what it found was already decided: captions that were about to be removed,
and panel blurs that were about to be rebuilt. The faster shape:

1. **Run the automatic gates first** (`qa_timeline.py`, the privacy `--check`, the proof gate). The reviewer only gets
   what a script can't judge.
2. **Shard.** Sheets of 8 frames (4 per row, 512×288, frame number burned in), at most 2 sheets per reviewer, and 3–4
   reviewers in parallel (`Agent`, run in the background). Wall time is about 10–15 min instead of 2 h.
3. **Same brief for every shard** (below). It gets the sheets, the-look.md and the beat table, and none of the build
   reasoning.
4. **Merge** the findings by frame. Drop anything already decided in the-look's channel defaults. Fix, run the gates
   again, and re-sheet only the touched frames. Three rounds at most, then report what remains.

## Brief (paste per shard; fill the {…} parts)
```
You are a fresh-eyes video QA reviewer. Read {the-look.md path}. Then look at these contact sheets of an edit (frame
numbers are burned in top-left; the white grid is an inspection overlay, not a defect): {sheet paths}.
Beats for these frames: {beat table rows}.
Decided already, do NOT report: {channel defaults, e.g. no captions on long-form; blur covers only names/IDs/links/keys;
corner camera bottom-right covers a baked webcam, so slide content under it is unrecoverable}.
Report at most 10 defects, most severe first, one line each:
  frame | defect (what a viewer sees) | severity high/medium/low | concrete fix
Look for: a sensitive word readable (client/business name, account ID, key, email, address, private link); a graphic
covering text that matters; two logo tags at once; a graphic cut by the frame edge or unreadable at phone size;
zoom framing that cuts words or boxes mid-way; a long stretch of tiny unzoomed UI text; blank or near-blank frames
while the speaker talks; a frozen or stuttering face; anything that looks broken. Use zoomed crops only when a word must be
read. Finish within 15 minutes; if images drop from context, report what you have.
```
