---
name: content-autopilot
description: "Run the publishing pipeline after you approve a video: put its free file on your site's library, write the captions in your voice, and schedule it (YouTube through the API; Instagram, Facebook and TikTok through GHL). Use for 'schedule this', 'post this Reel', 'what's scheduled', 'queue', 'autopilot', 'add it to the library', 'everything in Drive is good to go', or right after an avatar-shorts / episode approval."
---

# Content autopilot

You approve. Everything after the approval is this skill. Nothing gets posted by hand.

Run every command from the repo root. Settings come from `config.json` (`creator`, `schedule`, `youtube`, `site`, `drive`, `ghl`), secrets from `.env` (`GHL_API_KEY`, `GHL_LOCATION_ID`, `META_ACCESS_TOKEN`, `YOUTUBE_OAUTH_*`).

## What goes where

Default slots (`schedule` in config.json, times in `creator.timezone`):

| Video | Slot | Platforms |
|---|---|---|
| Reel / Short | the earliest open day at **12:00, every day** (any open day gets the next Reel) | YouTube Shorts (direct API, private + publishAt) + Instagram (Reel), your Facebook page (Reel), TikTok (one GHL Social Planner post, `status: scheduled`) |
| Long-form episode | next free **Tue 10:00** | YouTube only (its Shorts go through the Reel row) |
| LinkedIn post (text + educational graphic or carousel) | next free **Tue / Wed / Thu 12:00**, after you approve the text | your personal profile (GHL Social Planner) |
| Free file / repo | on approval | your site's library (`site/`), behind the email box |
| Welcome email | set up once | your GHL welcome workflow for the library tag (`LIBRARY_TAG`, default `free-library`, which `site/api/subscribe.js` adds). Evergreen, never edit per video |

Approved means: you said so in chat, or the master is in your Drive Shorts folder (`drive.shorts_folder_id` in config.json): anything there is good to go. When a Reel has several versions in Drive (v2, v3, v4), schedule only the one you picked; never post near-duplicates. Masters reach that folder only after your OK (the avatar-shorts skill's `reel.py drive` step runs at approval), so a file there is never an unreviewed render.

## On approval

1. **Library (if it gives something away).** Add to the top of `kits` or `tools` in `site/library.json`, then `python3 site/publish.py --deploy` (renders, asserts every link is behind the email box, ships). Do this before the video's slot, because the comment DM and "link in bio" both point here.
2. **`post.json` in the video folder.**
   ```json
   {"kind": "reel", "video": "<master>.mp4", "cover": "<slug>-cover.jpg",
    "title": "<YouTube title from the hook>",
    "caption": "<from the approved script, your words>\n\nComment \"WORD\" and I'll send it to you directly (or it's at the link in my bio).\n\n#tag #tag #tag",
    "comment": "Here's the repo: <url>\nEvery file from my videos: <creator.site_url>",
    "description": "<caption without hashtags + comment>", "topic": "<books | chatbot | google-ads | ...>", "ai": false}
   ```
   - Voice: build the caption from the approved script and `brand-system/voice/voice-rules.md`. Keep your own phrases; no corporate words, no "unlock".
   - Evergreen: no dates, counts that will change, "new", or episode numbers.
   - First line: 125 characters or fewer, ending on a full stop or a cliff. Instagram shows about 125 before "… more", so a longer line gets cut mid-thought.
   - Search words: one or two phrases people would type ("Claude plugins", "free AI tools") as plain words in the body. Instagram search reads captions; hashtags are only labels. Instagram caps them at 5; use 3 at most.
   - `schedule.py add` refuses a Reel caption with em dashes, curly quotes, hidden characters or stock AI words (same checker as LinkedIn, `linkedin/human/slop.json`) and warns on a long first line.
   - `topic`: one short slug, reusing an existing one when it's the same subject (`schedule.py list` shows them). The scheduler keeps the same topic at least 7 days apart within the Shorts/Reels feed and within LinkedIn (episodes are exempt), so a new video can land a slot or two later than the next free one.
   - CTA: one exact wording on every video: Comment "WORD" and I'll send it to you directly. WORD must be in `system/comment-words.md` (your GHL comment → DM workflow sends your site link on Instagram and Facebook); add a new word there and to the workflow's triggers before the slot. The "link in my bio" half keeps TikTok and YouTube working, since they have no auto-DM.
   - `comment` only when the video says "link in the comments". GHL can't comment on TikTok, so the scheduler splits it into an IG+FB post with the comment and a TikTok post without; the caption must say "Link's in my bio" so TikTok still works.
   - `"ai"`: `true` turns on YouTube's altered or synthetic content setting. Platform rules don't exempt an AI avatar of yourself, so check them before you choose `false`. Keep one choice across videos and never change it without your OK.
   - Episodes: `"kind": "episode"`, `"thumbnail": "<file>"`, title/description from `packaging/`.
3. **Schedule.** `python3 system/schedule.py add <video_dir>` (dry run: slot, channel, GHL accounts), then the same with `--go`. Report the slot. One video at a time; stop at the first error. Off-cadence times you pick: `--at "YYYY-MM-DD HH:MM"`. A Short that stays off Instagram, Facebook and TikTok gets `"platforms": ["youtube"]` in post.json. For an episode you track in a run-sheet page (its link in `<video_dir>/notion.md`), set that row to `scheduled` with the publish date, as the script's `Tracker:` line says. If the video has a `pin` (episodes, from `packaging/youtube-upload.md`) or a `comment`, `add` puts a pin reminder in your Apple Reminders list (`schedule.reminder_list`, through remctl) for 5 minutes after the slot (YouTube's API can't pin). Without remctl it prints the text to post and pin instead.
4. **LinkedIn.** Write `<video_dir>/linkedin.txt` (one post that retells the video, per `linkedin/PLAYBOOK.md`) and one educational graphic: `linkedin.html` (a carousel for step-by-step videos, one image otherwise) rendered with `python3 linkedin/creative/render.py <video_dir>`. Show the text for approval; on OK, `schedule.py linkedin <video_dir> --topic <slug> --go` (the topic defaults to the folder's post.json). LinkedIn never posts without that OK.
5. **Check.** `python3 system/schedule.py list`. Every row should be clean (no `[socials not scheduled]` / `[YouTube time not set]` flags). After the slot, `schedule.py check` (set it up as a daily scheduled task, about 30 minutes after the Reel slot) confirms YouTube is public and every GHL platform post published, marks the ledger `published`, and exits 1 with `FAIL` lines otherwise; for an episode it prints the `Tracker:` row to set `published`.
6. **Once a week: measure.** `schedule.py reels`, plus each Reel's Instagram Insights, into `research/reels-log.md` (method and rules at its top). Then `python3 research/retention/retention.py` (every Short's YouTube retention curve + Instagram watch time, drops lined up with the words and layout → `REPORT.md`) and update `research/retention/RULES.md`: keep, retire or add rules, and fill in what the week's Reels tested. The aim is to get better every time.

## Commands

| Command | Does |
|---|---|
| `schedule.py add <dir> [--go]` | Next free slot → YouTube upload (private + publishAt) → GHL post(s). Re-running a half-done video keeps its slot and YouTube video and finishes GHL |
| `schedule.py linkedin <dir> [--go]` | `linkedin.txt` + `linkedin-NN.png` → next free LinkedIn slot (several slides = PDF carousel, which needs the GHL internal client) |
| `schedule.py facebook <dir> [--go]` | `facebook.txt` + `facebook-01.png` (+ `facebook-comment.txt`) → your Facebook page on the Reel's day at `schedule.facebook_time` |
| `schedule.py list` | Upcoming queue with flags |
| `schedule.py check` | Due posts: YouTube public? GHL platform posts published? → ledger `published`; `FAIL` lines + exit 1 otherwise |
| `schedule.py remind` | Pin-comment reminders for upcoming videos that lack one (`add` sets them itself) |
| `schedule.py reslot` | Pushes ledger slots to YouTube publishAt for rows marked `youtube_slot_ok: false`, and to GHL for rows marked `ghl_slot_ok: false` |
| `schedule.py reels` | Published Reels' YouTube numbers (× median, stayed, avg %, shares and subs per 100 views) for `research/reels-log.md` |
| `schedule.py growth` | Followers and subscribers against `growth.goals` → `research/growth/daily.csv`, every post's numbers → `posts.csv` |
| `schedule.py trial <dir\|today> [--go]` | post.json `trial` → Instagram Trial Reels (non-followers first) to test hooks |
| `schedule.py dashboard` | Runway data (slots, when each feed runs dry, radar picks) → `.tmp/dashboard/` |
| `schedule.py selftest` | Slot maths |
| `site/publish.py [--deploy]` | `library.json` + config.json → `site/index.html` → your site |

All of them are `python3 system/schedule.py ...` from the repo root. Ledger: `system/schedule-ledger.json` (statuses `youtube_only` → `scheduled` → `published`). GHL accounts and your GHL user (`ghl.user_email`, default `creator.email`) are looked up at runtime with `GHL_API_KEY` and `GHL_LOCATION_ID`; never hardcode IDs.

Needs: Python with `requests`, `google-api-python-client`, `google-auth-oauthlib`; `ffmpeg`/`ffprobe` (GHL-sized copies); ImageMagick (LinkedIn carousels); the Vercel CLI (site). Optional: `remctl` (pin reminders) and the GHL internal client from the gohighlevel-cli plugin at `plugins/gohighlevel-cli/cli_anything/gohighlevel/utils/ghl_internal_client.py` (LinkedIn carousels; single-image posts work without it).

## Traps already paid for

| Symptom | Cause | Rule |
|---|---|---|
| Several Shorts all set to the same slot | The ledger was written only after GHL succeeded, so each failed run reused the slot | Fixed: the slot is saved the moment YouTube has the video. If it ever happens, mark rows `youtube_slot_ok: false` and run `reslot` |
| `403 insufficient scopes` editing a YouTube video | Token had upload + readonly only | `youtube_upload.py auth` asks for `youtube`, `youtube.force-ssl` (comments) and `yt-analytics.readonly` too. If it happens: `python3 system/youtube_upload.py auth`, approve in the browser with the Google account that owns the channel and pick the channel, then store the new refresh token wherever your `.env` is synced from (a stale copy that wins over `.env` undoes the re-auth) |
| Need to move a post | (none) | Set the ledger `slot`, `youtube_slot_ok: false` and `ghl_slot_ok: false` (a Reel's Facebook post at `schedule.facebook_time` moves to the same day), then `schedule.py reslot`: GHL gets the whole post back with the new time (cover and first comment kept, checked on read-back), YouTube gets publishAt (needs the full `youtube` scope; it waits out YouTube's few-second read-back lag). Fallback without the scope: Claude in Chrome → `studio.youtube.com/video/<id>/edit` → Visibility → date picker → click the day → Done → Save (click Save by position; it often needs a second click before it greys out). Verify with the API (`videos.list part=status`, readonly is enough), then set `youtube_slot_ok` |
| GHL `413 ... maximum allowed size (25MB)` / 502 | Cap on the **API** media upload (the GHL app itself takes bigger files) | `schedule.py` sends GHL a ≤24 MB copy (`<master>.ghl.mp4`, ~5 Mbps 1080x1920); YouTube gets the master. Swap to the app's upload path if you want originals on GHL |
| Shorts had no YouTube thumbnail | The scheduler only sent thumbnails for episodes | Fixed: a Reel's `cover` is also its YouTube thumbnail (`thumbnails.set` works with the upload scope; Studio shows it 9:16 after a few minutes of processing) |
| Cover "missing" on a GHL post | GHL moves the cover to the post-level `thumbnail` | Check `post.thumbnail`, not `media[].thumbnail` |
| Instagram shows the Reel's first frame, not the cover | `upload_media` sent no file type, so GHL stored and served every upload as `text/plain`; Instagram ignores a cover that isn't an image, and GHL's composer can't open such a video ("!" on the tile) | Fixed: `upload_media` sends the real MIME type (`image/jpeg`, `video/mp4`). Facebook Reels and TikTok can't take a custom cover through GHL; Instagram, YouTube and LinkedIn can |
| LinkedIn carousel posted as 1 slide | Plain API posts get no page folder; GHL's composer converts the PDF to pages first | `schedule.py linkedin` copies the composer through GHL's internal backend: `document-to-image`, then the post with `mediaOptimization`. GHL's preview says "1 page" even for its own carousels; the pages live in the post's folder. Check the first one live on LinkedIn |
| `no connected LinkedIn profile` | GHL's LinkedIn token lasts ~60 days | Reconnect LinkedIn in Social Planner |
| `403 1010` from GHL | Cloudflare blocks Python's default User-Agent | `ghl()` sends a browser UA |
| A Reel's GHL post still says `scheduled` (and `deleted: true`) after its slot | When it publishes, GHL retires the parent post and makes one post per platform carrying `parentPostId` | Never read the parent; `schedule.py check` reads the children |

## Don't

- Don't post or schedule anything that isn't approved, outside the slots, or public without a slot (YouTube stays private until publishAt).
- Don't edit the welcome email or site copy per video; both are evergreen.
- Don't delete posts, videos or contacts; say what to remove and let the creator do it.

The full pipeline lives in `WORKFLOW.md`; keep it and this skill in step.
