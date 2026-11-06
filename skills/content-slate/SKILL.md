---
name: content-slate
description: "Develop titles, hooks, and thumbnail concepts for your YouTube episodes."
---

# Content Slate: Titles & Concepts

Used in the packaging step of `WORKFLOW.md`, after the episode is recorded and before `content-pixel`.

## The job
Produce **titles that earn clicks** and **thumbnail concepts that `content-pixel` can execute**. Everything grounded in real audience language from your niche, not generic AI-sounding copy.

## Inputs
1. **The episode run sheet** (from `content-blueprint`)
2. **Audience language samples**: direct quotes from X, Reddit or comments showing how your viewers talk about this topic (the radar digests in `research/radar/` are one source)
3. A weekly niche brief, if you keep one

## Primary output: Click Package

```
# Click Package: [Episode Topic]

## TITLE OPTIONS (5-7)
Rank by recommended order. For each:
- Title text
- Why it works (1 line)
- Specificity test: could this title belong to any AI creator? (must be NO)

## THUMBNAIL CONCEPTS (3)
For each concept:
- Layout description (what goes where)
- Text overlay (2–5 words, sentence case, per the packaging playbook)
- Primary visual element (face, screenshot, result, before/after)
- Emotional trigger (curiosity, proof, tension, surprise)
- Why this concept pairs with the recommended title

## HOOK VARIATIONS (3)
- Opening line options to choose from
- Each must be deliverable in <5 seconds straight to camera
```

## Learn from what works (read first)
`research/packaging/PLAYBOOK.md` holds the title, thumbnail and description rules learned from top channels,
kept current with `research/packaging/pull.py` (run it before packaging). Search first: run `research/packaging/keywords.py`
on the episode's seed phrases and put the chosen "target" phrase in the first ~50 characters of every title option
(playbook § Search first). Titles: one plain benefit, a true bracket
qualifier ("(Free Kit)", "(2026)"), first person + a real receipt + "Here's How" for business videos. Descriptions: the free
kit link on line 1, a two-line "If this is your first video" intro, a 2–3 sentence summary, then chapters.

## Brand voice for titles
Defaults; your voice files in `brand-system/voice/` win where they differ.
- **Use:** "Real," "Honest," "Actually," "Here's What Happened," numbers, specific results
- **Never use:** "Insane," "Mind-Blowing," "You Won't Believe," "Game-Changer," "Ultimate Guide"
- **The positioning is anti-hype.** Titles should feel like a smart friend sharing what they learned, not a clickbait farm

## Specificity rules
Every title must pass this test:
1. Could this title belong to any other AI creator? → If YES, revise
2. Does it reference something specific (tool name, number, timeframe, result)? → If NO, revise
3. Does it use language the target audience actually uses? → Pull from the audience language samples

**Good:** "I Run My Business With 5 AI Agents. Here's the Honest Truth."
**Bad:** "How AI Agents Are Changing Business Forever"

## Thumbnail concept rules (for content-pixel to execute)
- Must reference **real visual material**: screenshots, terminal windows, real faces, real output files
- **No stock imagery, no glowing brains, no robot illustrations, no circuit boards**
- One clear focal element: the eye lands on one thing immediately
- Text overlay is optional; if used, 3 words max, adds tension or specificity
- Must be readable at mobile thumbnail size

## Tools
- Claude (title + concept generation)
- Read access to the run sheet
- Read access to the audience language samples

## Output format
Save in the episode folder, `episodes/<slug>/packaging/youtube-upload.md`:
- titles (ranked, with the thumbnail each pairs with), description, tags, pinned comment, upload settings
