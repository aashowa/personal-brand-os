---
name: content-blueprint
description: "Draft or revise your video scripts (run sheets) in Notion or the episode folder for your review and rewriting."
---

# Content Blueprint

Turn an idea and supporting evidence into a script you can read, adjust, and record.

## Context

Read `WORKFLOW.md` (repo root) and your voice files in `brand-system/voice/`. They own the current workflow and voice. Use the tools available in this session; this skill works with both Claude and Codex.

Use the supplied idea and evidence. Fetch the episode's run sheet (the Notion page and its comments, or the local file) before revising. Research only missing facts that affect the script; a research brief, weekly niche report, or audience quote is not a prerequisite.

## Draft

- Default to a run sheet: chapters, talking points, what's on screen, numbers to verify (`WORKFLOW.md` § Run sheet shape), with one recommended hook. Write full spoken prose only when you ask for it.
- Long-form runs up to about 20 minutes unless you say otherwise; use the requested duration for Reels or Shorts.
- Let the story explain what happened, what you tried, what the evidence supports, and what the viewer can take away. Preserve uncertainty and identify missing proof.
- Preserve your own wording and edits. Revise the requested passages rather than regenerating the whole page.
- Include a short visual note only when it helps. Decks, alternating camera modes, downloads, and extra versions are optional.
- If `--hooks N` is requested, provide that many alternatives. The default is one; no fixed archetypes are required.

## Deliver

Save it as editable text in the episode's page in your Notion database (set `notion.pipeline_url` in `config.json`), or in `episodes/<slug>/run-sheet.md` if you don't use Notion, following WORKFLOW.md. In Notion: search before creating a page, fetch immediately before updates, preserve concurrent edits, and verify the saved content; keep only the Notion link in the local episode folder, and create production snapshots from Notion when needed.

Return the link (or file path) and any specific question or missing evidence you need to review. A saved draft is not approval to record or publish. If `notion.pipeline_url` is set but Notion is unavailable, report `Notion sync pending` and do not silently create a competing file draft.
