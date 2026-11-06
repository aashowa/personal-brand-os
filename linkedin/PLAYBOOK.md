# LinkedIn playbook

LinkedIn is where the videos become personal. Each approved Reel gets one text post, and an episode one or more (a long episode can give five), each retelling it from your own work running your business. It's not a lead engine. The only link is your site (`creator.site_url` in `config.json`).

Research behind every rule: two research passes on 2025–2026 data, sources at the bottom. Most of it is vendor correlation, so treat it as a starting point and let your own numbers in the **Test log** overrule it.

## The anatomy

| # | Part | Length | Rule |
|---|---|---|---|
| 1 | **Hook** | line 1, under 40 characters if possible | A scene, an admission with a cost, or a plain claim with a number. It's the only line most people see. |
| 2 | **Re-hook** | line 2, one short sentence | Hints at the payoff. Lines 1+2 must work inside the ~140 characters mobile shows before "…see more". |
| 3 | **Scene** | 2–4 lines | Where, what broke or bugged you, one number, one tool name. |
| 4 | **What I did** | 4–6 short lines, a numbered list is fine | The receipts from the video, in your words. |
| 5 | **What happened** | 2–4 lines | The result, plus what still needs a human or what broke. |
| 6 | **Turn** | 1–2 lines | One lesson in plain, shop-floor language. No neat bow. |
| 7 | **Ending** | 1 line | One narrow question to people like your readers ("Shop owners, which one would you hand off first?"), or nothing. |
| 8 | **P.S.** | 1 line | `P.S. …free at <your domain>` as a bare domain, last line. |

Total **800–1,500 characters** (shorter than 300 underperforms; nothing gained past 1,500). Lines under 60 characters, paragraphs of 1–2 lines.

## Post types (rotate, don't repeat two in a row)

| Type | Shape | Best source |
|---|---|---|
| Story → lesson | moment → what it taught → what to do | personal Reels (a cost you cut, a job you handed off) |
| I did X, here's what happened | claim → setup → what it does → honest friction | episodes, kit Reels |
| Failure / what broke | admission + cost early → what happened → what changed | anything that broke on camera (the vulnerable post is the one that beats an account's own average) |
| How I do X | problem → why most attempts fail → numbered steps → one-line close | step-by-step Reels |
| Contrarian | claim → evidence by line 3 → why → what to do instead | Reels that argue with a common belief |
| Surprise from the floor | what happened in your business that you didn't expect | real moments from your work (write them down when they happen) |

## Hooks

Use: a time-stamped scene ("Saturday, 6:40 pm. The till froze."), an admission with a cost ("I paid a freelancer $900 for this."), very short (4–7 words), a named audience ("Shop owners:"), a number with the reason.

Don't use: "Here's how/what…" handoffs (measured reach loss), "Stop…/Don't…" openers, yes/no question hooks, engagement gates ("comment STACK"), "thrilled", "game-changer", "unlock", 4+ hashtags.

## Voice

Plain, first person, your words from the video script (`brand-system/voice/voice-rules.md`). Readers are business owners, not techies: explain any tech word with an everyday comparison or cut it. Keep the honest limits from the video ("it never sends anything without my OK"). Never invent a scene, a number or a feeling; if a post needs a real moment, use one you lived. LinkedIn says it limits the spread of generic, AI-sounding posts, so specifics are the safety, not decoration.

## Format and settings

- **Every post gets one educational graphic:** something useful to look at. No photos, screenshots or YouTube covers. Infographics and guides earn the most saves; each one teaches one thing.
  - **Step-by-step video** (a kit, an episode) → **carousel**: 8 slides at 1080×1350, one idea per slide, big type. The cover is the promise plus a small diagram; the last slide is a checklist plus your domain. At most one a week. GHL sends it as a swipeable PDF document.
  - **One idea** (a stat, a framework, how something works) → **one 1080×1350 graphic**, a diagram rather than paragraphs.
  - **Every slide = a short title (8 words max) + one real Excalidraw diagram + at most one line.** Visual, not overwhelming. Carousels are 8 slides.
  - **How it's made:** add the diagram to `linkedin/creative/diagrams.mjs` (real Excalidraw 0.18.1, Excalifont, brand colours; writes `<name>.excalidraw` + `<name>.png` into the post folder; `node linkedin/creative/diagrams.mjs <name>`). Then `<dir>/linkedin.html` with `linkedin/creative/brand.css` (title in Bricolage, `<div class="fig"><img src="<name>.png"></div>`), then `python3 linkedin/creative/render.py <dir>` → `linkedin-NN.png`. Built in HTML, not an AI image model, so every word is exact; fully AI-designed infographics underperform (0.6–1.1x). Check the PNGs by eye for overflow before approving.
  - Every fact on a graphic comes from the video, its deck or its kit.
- **Not yet:** the Reel as native video (video is the only format below a profile's own median, ~0.86x). Test it once before relying on it.
- **Link:** your domain bare, in the P.S. on the last line. Link penalties are small or disputed (−7% against the author's own median in the most careful study), and a link in the first comment scores the same, so keep it simple.
- **Hashtags:** none. **Tagging:** GHL can't @mention on a personal profile; tag by hand after it posts, if ever.
- **One theme:** pick one (for example, how you use AI in your business). Your headline and About must say the same thing, because the feed matches post text to profile text.

## Cadence and approval

- **Tue / Wed / Thu 12:00** in your timezone by default (the LinkedIn slots in `config.json`, used by `system/schedule.py`), at least 20 hours apart. Timing is a weak lever, so the slots stay fixed.
- You approve the exact text, then `python3 system/schedule.py linkedin <dir> --go`. Nothing posts without that approval. It refuses a post with em dashes, curly quotes, hidden characters or stock AI words (`linkedin/human/slop.json`, editable) and prints sentence shapes to judge by eye.
- After it posts, reply to comments in the first hour when you can. Half of a post's impressions land in its first 48 hours. To draft the replies, paste the comments into your agent and ask for drafts; post them yourself.

## Improve as you go

GHL has no analytics for personal profiles. Every Friday, read each post's numbers at 48 hours from LinkedIn (in your browser, or from a screenshot) into the log, with your follower count that day. After every 6 posts, change **one** thing (hook type, format, length, time) and keep what wins.

Rank posts by these, not raw impressions, which mostly track follower count (method from Jake Schincariol's `li-audit`):

| Metric | How | Tells you |
|---|---|---|
| **Eng. rate** | (reactions + comments + reposts) / impressions | whether the post earned its reach |
| **Comment ratio** | comments / reactions | whether it started a conversation or just got a nod |
| **Reach ×** | impressions / followers | whether it travelled past people who already follow you |
| **Saves + sends** | from the post's analytics, when shown | the strongest sign of future reach |

Compare the top and bottom posts on hook type, format, length and theme first; day and time last, and only if nothing else explains it. Under about 6 posts there is no pattern yet; say so rather than inventing one. Read every post at the same age (48 hours or more): newer posts look smaller than they will end.

**Running a test:** change one thing for the next 6 posts and nothing else. Write down the change, why (the cleanest split in the last six), the read date (when all six are past 48 hours), and the bar to keep it, set from your baseline median before the test starts (for example, median reach × at least half again above baseline with eng. rate around 1%+). If it misses, write down what that rules out and what Test 2 changes.

### Test log

Baseline ({{date}}): {{followers}} followers. Your last posts before this playbook got {{range}} impressions.

| Posted | Post (folder) | Type | Hook | Format | Chars | Followers | Impressions | Reactions | Comments | Reposts | Saves + sends | Eng. rate | Comment ratio | Reach × | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | | | |

## Traps

- The LinkedIn connection in GHL expires about every 60 days. `schedule.py linkedin` stops with "reconnect" when it does: Social Planner → reconnect LinkedIn.
- GHL can't mix images and video in one post. Images: JPG/PNG, 8 MB max. **Carousels go through GHL the way its own composer does it** (`schedule.py`): upload the PDF → `document-to-image` on GHL's app backend splits it into page JPGs → create the post from those pages with `mediaOptimization: true` + `postAsPdf` + title. GHL then keeps every page in the post's scheduled-media folder (`…/<postId>/1.jpg`…) and lists only page 1 on the post, so its "Post details" preview says "1 page" for its own carousels too; that is normal. Plain API posts with your own image URLs get no page folder (only slide 1 would go out). After your first GHL carousel posts, check LinkedIn shows every page. Fallback: schedule on LinkedIn itself (`linkedin.com/preload/sharebox/` → More → Add a document). The app backend needs `token-id` + `version: 2021-07-28`.

## Sources (2025–2026)

AuthoredUp hook study, 309k posts (2026-08) · AuthoredUp video and repurposing (2026-04/08) · NBK "What works on LinkedIn", 74k posts (2026-10-09) · MyFeedIn, 40k posts (2026-09-22) · Metricool, 673k posts (2026-04-16) · LinkPost, 516k posts (2026-06/07) · Shield Index (2026-04-17) · Buffer algorithm guide (2025-12-19) · Sprout best times (2026-03-31) · MagicPost "Here's how" study, 287k posts (2026-06-16) · Sonar founder hooks (2026-09-22) · LinkedIn "Keeping conversations real" (2026-06-04) · VentureBeat on the LinkedIn feed LLM rebuild (2026-03-16) · GHL Social Planner help docs. Creators to study for format: Dan Peguine, Altan Khendup, Ruben Hassid (plain how-tos), Lara Acosta (story → lesson).
