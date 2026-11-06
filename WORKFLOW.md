# Workflow

Your only job is to approve. Everything after an approval runs itself, and the `content-autopilot` skill runs it.

## The whole pipeline

| Thing | Made by | On approval | Goes out |
|---|---|---|---|
| Long-form episode | run sheet, record, edit (`palmier-hyperframes-video`), package (`content-slate`, `content-pixel`) | free file to the library, then `system/schedule.py add <ep_dir> --go` | YouTube, next free episode slot (default Tuesday 10:00). Uploaded private with a publish time, so it goes public on its own |
| Reel / Short | `avatar-shorts` (or `episode-shorts`, cut from an episode) | cover, library, `post.json`, then `system/schedule.py add <reel_dir> --go` | The earliest open Reel slot (default every day 12:00): YouTube Shorts through the API, plus Instagram, Facebook and TikTok as one GHL Social Planner post |
| LinkedIn post | the video above, retold per `linkedin/PLAYBOOK.md` (`linkedin-batch`) | you OK `linkedin.txt`, then `system/schedule.py linkedin <dir> --go` | Your LinkedIn profile through GHL, next free Tuesday, Wednesday or Thursday 12:00, text plus one teaching graphic or carousel |
| Free file or repo | the video above | `site/library.json`, then `python3 site/publish.py --deploy` | Your site, behind an email box |
| Welcome email | a GHL workflow triggered by the library tag | nothing to do, it's evergreen | every new sign-up |

Slots and the timezone live in `config.json` (`schedule`, `creator.timezone`).

- `post.json` in the video folder holds the YouTube title, one caption in your voice (`brand-system/voice/voice-rules.md`) ending with the CTA, an optional cover, and `"ai"` (set `true` to flag YouTube's altered-content setting). The schema is in the `content-autopilot` skill.
- `python3 system/schedule.py list` shows what's coming up. `add` without `--go` is a dry run. The ledger is `system/schedule-ledger.json` (created on first run, gitignored).
- Every copy that stays up (site, welcome email, YouTube footer) is evergreen: no dates, counts or episode numbers.
- Slots are fixed so the queue fills ahead: approve six Reels on a Monday and they cover most of the week.
- `schedule.py add` and `schedule.py linkedin` refuse copy with AI tells (em dashes, curly quotes, hidden characters, stock AI words from `linkedin/human/slop.json`).

## Daily and weekly loops

| When | What | Where |
|---|---|---|
| Daily | What's new and worth a video: `research/radar/radar.py collect`, ranked by `RUBRIC.md` | `research/radar/` |
| Daily | Videos that beat their creator's normal, their hooks, remake ideas: `research/outliers/outliers.py collect` | `research/outliers/` (`HOOKS.md`, `IDEAS.md`) |
| Daily | Did the due posts go out: `system/schedule.py check` | prints `FAIL` lines and exits 1 otherwise |
| Daily (optional) | One trial Reel with a new opening, posted to non-followers | `research/growth/test.md`, `avatar-shorts` § Trial Reels |
| Friday | Reel numbers (`schedule.py reels`), retention curves (`research/retention/retention.py`), then keep, retire or add rules in `research/retention/RULES.md` | `research/` |
| Friday | LinkedIn numbers into the playbook's test log | `linkedin/PLAYBOOK.md` |

Run them by hand, or schedule them with your agent's scheduled tasks or cron.

## From idea to run sheet

**What your audience needs to learn, then an idea, then you approve it, then a run sheet, then you adjust it, then you record, edit and publish.**

1. Start from what your viewer needs to learn at their level (beginner, intermediate or expert; see `brand-system/personal-brand-strategy.md`). Then pull the real example from your own work: the system, what it does for the business, and the proof on screen (numbers, logs, before and after). Agree which ideas deserve a video. A request to outline a named idea counts as approval; a request to suggest topics does not.
2. After approval, write the run sheet (`content-blueprint`) into the episode's page: your Notion database if you set `notion.pipeline_url` in `config.json`, otherwise `episodes/<slug>/run-sheet.md`.
3. Read, edit or comment. On a revision, the agent re-reads the page and your comments, edits only the requested parts, and keeps the rest.
4. You decide when it's ready to record. Diagrams, slides, editing, thumbnails and distribution are prepared only for the next step you ask for.

## Run sheet shape

- Open on a hook to camera, fully scripted for the teleprompter (`hook-teleprompter.txt` in the episode folder, plain lines you read, about 25 to 40 seconds). Write it from how strong creators in your niche open (`research/outliers/HOOKS.md`) in your voice (`brand-system/voice/tone.md`). No live demo or typing as the opener. The hook is the only part written word for word; the rest stays talking points.
- A numbered map: one chapter per layer, step or lesson, with chapter times.
- Per chapter: 2 to 3 talking points, what is on screen, one plain analogy for any technical idea, one hand-drawn diagram where it helps (`brand-system/diagrams/`).
- 1 to 3 foundations per video, taught just in time: a "Foundation" card the moment a concept first shows up (a one-line definition, a plain analogy, and how it works in each tool you cover).
- Every section ends with a "what's involved / what you need / skill to do it" strip (Beginner, Intermediate or Expert), and the video ends with a "Do this yourself" checklist before the recap.
- Tool-neutral where you can: if the viewer might use ChatGPT or Claude, name both where they differ (Codex reads `AGENTS.md`, Claude Code reads `CLAUDE.md`; skills are the same `SKILL.md`; both connect tools through MCP).
- Close on a one-sentence recap of the system and the next episode.
- Title options from the patterns that win in your research (`research/packaging/PLAYBOOK.md`): result or system first, real numbers. Don't label the audience in the title.

**Proof rules.** Every number is verified at writing time and dated on the page. List what's still needed from you instead of inventing it. Blur keys, tokens, client data and revenue totals (`skills/palmier-hyperframes-video/references/privacy-terms.txt`).

**Length.** Long-form runs up to about 20 minutes. Shorts come two ways: cut from an episode (`episode-shorts`) or made on their own as avatar Reels (`avatar-shorts`).

## Status and approval

Episode statuses: `idea`, `approved` (you want it made), `outlined` (run sheet written), `recording`, `recorded`, `editing`, `scheduled` (booked by `schedule.py`, with the publish date), `published`, `retired`. Set `published` only after the post is verified live: `schedule.py check` prints the episodes it saw go live. Reels, Shorts and LinkedIn posts live in the ledger, not in Notion.

## Skills

| Need | Use |
|---|---|
| Write or revise a run sheet | `content-blueprint` |
| Diagrams | `brand-system/diagrams/render.mjs` (episodes), `linkedin/creative/diagrams.mjs` (LinkedIn) |
| Edit recorded footage | `palmier-hyperframes-video` |
| Titles, description, thumbnails | `content-slate`, then `content-pixel` (`skills/content-pixel/scripts/thumbs.py`), by `research/packaging/PLAYBOOK.md` |
| Shorts cut from an episode | `episode-shorts` |
| Avatar Reels | `avatar-shorts` |
| LinkedIn posts | `linkedin-batch`, by `linkedin/PLAYBOOK.md` |
| After approval: free file, captions, scheduling | `content-autopilot` (`system/schedule.py`, `site/publish.py`) |
