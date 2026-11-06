# Workspace rules

This folder runs one creator's content: YouTube long-form, Shorts and Reels, LinkedIn, and a free-files site. The person using it is "you" below.

- Read `WORKFLOW.md` before episode, Reel or LinkedIn work. It owns the pipeline, the run sheet shape and the statuses.
- Read `brand-system/voice-guide.md` and `brand-system/voice/tone.md` before writing anything public (scripts, captions, titles, descriptions, posts). Keep the creator's cadence; don't turn it into agency copy or invent claims.
- One video, one system or one problem. Long-form runs up to about 20 minutes unless you change it.
- Media and production files go in `episodes/<slug>/`. Nothing generated goes at the repo root.
- Publishing, posting, external sends and public status changes need your explicit approval. Approved videos are scheduled with `system/schedule.py`: YouTube gets them private with a publish time, so they go public at the slot you approved. LinkedIn never posts without your OK.
- Secrets live in `.env` (template: `.env.example`) and personal settings in `config.json` (template: `config.example.json`). Never print, log or commit a key.
- Internal docs stay plain and precise; the voice guide is for audience-facing copy only.
