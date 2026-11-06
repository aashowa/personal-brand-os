# personal-brand-os

A working content system for one creator, run by an AI agent (Claude Code or Codex): YouTube long-form, AI-avatar Reels and Shorts, Shorts cut from your episodes, LinkedIn posts, a free-files page that grows your email list, and a scheduler that posts everything at fixed slots.

You pick topics and approve. The agent does the rest: research, scripts, the edit, thumbnails and covers, captions, scheduling, and checking that each post went live.

```
idea -> you approve -> run sheet / script -> you approve -> record or render -> edit -> you approve
     -> free file on your site -> captions -> scheduled (YouTube, Instagram, Facebook, TikTok, LinkedIn)
     -> checked live -> measured on Friday -> rules updated
```

## What's inside

| Part | What it does |
|---|---|
| `skills/avatar-shorts` | A 30 to 50 second vertical Reel spoken by your HeyGen avatar: script, HeyGen render, pause cuts, snap zooms, motion graphics, sound effects, music, -14 LUFS master, cover |
| `skills/episode-shorts` | 1 to 3 vertical Shorts cut from a finished episode: your camera on the bottom, motion graphics on top, captions on the seam |
| `skills/palmier-hyperframes-video` | Edit recorded long-form footage with automatic checks (footage health, pauses, audio polish, grade, zooms, privacy blur, captions) so your review is taste only |
| `skills/content-blueprint` | Turn an approved idea into a run sheet (chapters, talking points, what's on screen, numbers to verify) |
| `skills/content-slate`, `skills/content-pixel` | Titles, hooks, description and thumbnail concepts, then the thumbnails themselves |
| `skills/content-autopilot` | After approval: library entry, captions in your voice, scheduling, live checks |
| `skills/linkedin-batch` | Retell each approved video as a LinkedIn post with a teaching graphic |
| `system/schedule.py` | The scheduler: fixed slots, YouTube upload (private + publish time), one GHL post for Instagram, Facebook and TikTok, LinkedIn through GHL, `check`, `list`, `reels` numbers |
| `system/youtube_upload.py` | YouTube OAuth and upload |
| `research/` | Daily radar (what's new), outliers (videos beating their creator's normal, their hooks), retention rules from your own curves, packaging playbook, growth trials |
| `site/` | An email-gated free-files page (link in bio) and a subscribe endpoint that tags the contact in GHL |
| `brand-system/` | Voice guide templates, a paper-and-ink visual identity, thumbnail and cover templates, a diagram renderer |
| `linkedin/` | LinkedIn playbook, the AI-tell checker, graphic renderer |

`WORKFLOW.md` is the pipeline in one page. `AGENTS.md` (read by Codex; `CLAUDE.md` imports it) holds the workspace rules the agent follows.

## Requirements

Built and run on macOS (Apple Silicon). Most of it works anywhere; a few steps use macOS tools (VideoToolbox, `cp -c`, Apple Reminders).

**Everywhere:** an AI coding agent (Claude Code or Codex), Python 3.10+ (`numpy`, `requests`, `feedparser`, `pillow`, `playwright`, `google-api-python-client`, `google-auth-oauthlib`), Node 20+ (global `playwright`), ffmpeg/ffprobe, Google Chrome, `yt-dlp`, `gh`.

**Per part:**

| Part | Needs |
|---|---|
| Avatar Reels | [HeyGen](https://heygen.com) account + `heygen` CLI (OAuth login), [HyperFrames](https://github.com/heygen-com/hyperframes) (`npx hyperframes@0.8.174`) and its `media-use` skill (sound-effect bank), OpenAI key (whisper-1 word timings), [Kie.ai](https://kie.ai) key (covers) |
| Long-form edit | [Palmier Pro](https://palmier.io) with its MCP server, tesseract (privacy OCR), `mlx_whisper` (transcripts on Apple Silicon) |
| Shorts from episodes | HyperFrames, the long-form edit skill |
| Scheduling | YouTube Data API OAuth app, a GoHighLevel location with Social Planner (Instagram, Facebook, TikTok, LinkedIn connected), a Meta Graph API token for Instagram numbers |
| Free-files site | Vercel (`vercel link` once in `site/`), a GHL workflow that sends the welcome email on the library tag |
| Research | Apify (Instagram outliers), a YouTube API key, Gemini key (transcripts), [Agent Reach](https://github.com/Panniantong/Agent-Reach) for the radar, `twitter-cli` (optional, X) |

**Optional:** `gws` CLI (push approved masters to Google Drive), `remctl` (pin-comment reminders in Apple Reminders), ImageMagick and `rsvg-convert` (cover logo tiles, LinkedIn carousels), a GHL internal-API client at `plugins/gohighlevel-cli/` for LinkedIn PDF carousels (the scheduler says so when it's missing).

Keys go in `.env` (see `.env.example`); everything personal goes in `config.json` (see `config.example.json`): your name and handle, timezone, posting slots, YouTube footer and tags, HeyGen avatar looks and voice, Drive folder, site copy and socials, radar search terms.

## Setup

1. Use this repo as a template (or clone it) into a private repo of your own. Your `episodes/`, `config.json` and `.env` stay out of git.
2. Copy the templates and fill them in:
   ```bash
   cp config.example.json config.json
   cp .env.example .env
   ```
3. Link the skills so your agent can load them:
   ```bash
   mkdir -p ~/.claude/skills && ln -s "$PWD"/skills/* ~/.claude/skills/
   ```
   For Codex, link them into `.agents/skills/` instead.
4. Fill in your voice: `brand-system/voice-guide.md`, `brand-system/voice/tone.md` and `brand-system/voice/voice-rules.md` are templates. The fastest way is to give the agent a few of your own video transcripts and ask it to fill them.
5. Run the self-tests (no keys or network needed):
   ```bash
   python3 system/schedule.py selftest
   python3 skills/avatar-shorts/scripts/reel.py --selftest
   python3 skills/episode-shorts/scripts/shorts.py --selftest
   python3 research/radar/radar.py selftest
   for f in skills/palmier-hyperframes-video/scripts/*.py; do grep -q selftest "$f" && python3 "$f" --selftest; done
   ```
   Each prints `selftest ok`. `research/outliers/outliers.py`, `research/packaging/pull.py`, `research/packaging/keywords.py` and `system/youtube_upload.py` have one too.
6. Sign in once: `heygen auth login --oauth`, `python3 system/youtube_upload.py auth` (picks your channel and saves the refresh token to `.env`).
7. Open the folder in Claude Code and say "make a reel about <something you actually use>".

Not shipped, because they're licensed or personal: your photos and avatar stills, the HeyGen-catalog music bed and six sound effects (`skills/avatar-shorts/assets/README.md` says how to supply them), and third-party logos (`skills/episode-shorts/assets/logos/README.md`).

## Safety rails

- Nothing is posted without your approval. YouTube uploads go up private with a publish time; LinkedIn never posts without your OK.
- Keys live only in `.env`. Scripts read them by name and never print them.
- `schedule.py` refuses captions with AI tells, and the edit runs a privacy scan for keys, emails and the terms in `privacy-terms.txt` before you see it.

## Credits

- Code and docs: MIT (`LICENSE`).
- `linkedin/human/`: MIT, Jake Schincariol (`linkedin/human/LICENSE`).
- Fonts: Inter, Bricolage Grotesque, Instrument Serif, JetBrains Mono under the SIL Open Font License (`OFL.txt` next to each).
- Sound effects `skills/avatar-shorts/assets/sfx/cc-*.mp3`: CC0, sources listed in `skills/avatar-shorts/assets/CREDITS.md`.
- Animated stickers: Noto Emoji, © Google LLC, CC BY 4.0 (credit it in the caption when a Reel uses one).
- The Claude Code crab drawn in `reel.py` is Anthropic's mascot; use it like a logo, on Claude topics only.
- The Reel format is modelled on Nick Saraev's Shorts structure; the edit runs on HeyGen's HyperFrames and Palmier Pro.
