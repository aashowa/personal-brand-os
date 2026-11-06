# episodes

One folder per video. This folder is gitignored (except this file), because it holds your recordings, renders and drafts.

- Long-form: `episodes/<slug>/` with `run-sheet.md` (or `notion.md` holding the Notion link), `hook-teleprompter.txt`, recordings, `packaging/`, `post.json`.
- Avatar Reels: `episodes/reel-<NN>-<slug>/`, created by `python3 skills/avatar-shorts/scripts/reel.py new <dir>`.
- Shorts cut from an episode land in that episode's folder.
