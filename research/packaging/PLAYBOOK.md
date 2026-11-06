# Packaging playbook: titles, thumbnails, descriptions

What to learn from the channels in `creators.json`, kept current. Read it before packaging any long-form episode
(`content-slate` for titles, `content-pixel` for thumbnails). Brand colours and type stay yours
(`../../brand-system/brand-sheet.html`); these rules are about composition and words.

**Keep up:** run `python3 research/packaging/pull.py` before packaging an episode (at least monthly). It adds new uploads and outliers
(2x a channel's median), their thumbnails and descriptions, and contact sheets in `research/packaging/<slug>/sheets/`. Read the new sheet;
when a pattern shows up in several new outliers, add it here with the date and an example.

Where the starting rules came from: a teardown of one large AI-automation channel (Nick Saraev: 12 months of uploads,
the top 24 thumbnails and a handful of descriptions). Your own pulls replace and extend them.

## Thumbnails
| Rule | Why (evidence) |
|---|---|
| Face calm, **mouth closed**, eye contact or a slight smile. No hand in front of the face; at most hand on chin or presenting the object. | Every face in the teardown's top 24. Pick a frame between words or ask the model for "mouth closed, slight confident smile". |
| **No cut-out outline** around the person; light them into the scene. | None in the top 24; the outline only showed up on the channel's weaker videos. |
| **One hero object**: one big app icon, or one real window with its key words huge (a command, a repo name, "$0"). | Over half of the top 24 use one glossy app icon; the rest one window with a few huge words. |
| **2–5 words, sentence case**, often ending with a period. The words add a twist the title doesn't say. ALL CAPS rarely. | Short sentence-case phrases (in the shape of "runs for free.") win; caps in only a few of the top 24. |
| Proof screenshots: crop to the one line that matters and make it big enough to read at 160x90. | The proof shots show one line or one number. |
| One hand-drawn arrow to the key thing. | Seen in about a third of the top 24. |
| Face + one object + a few words; lots of empty space. | Every top-24 thumbnail. |
| Keep your own brand (the kit default is paper grid, ink and marker). Marker highlight on one word only. | Light grid paper also appears in the top 24. |
| Check at 160x90 before delivering; make 3 variants for YouTube Test & Compare. | Standard practice. |

Avoid: shouty generic text ("AVOID THIS", "STOP DOING THIS"), a row of logo tiles, dense cards, mid-word faces.

## Search first
With no subscribers there is no Home feed audience, so search is the traffic you can steer: the title carries a phrase
people type, and the thumbnail carries the curiosity. A title with no searched phrase in it (for example "AI stack", which
autocompletes to "AI stocks") can sit at single-digit views for days.
1. **Find the phrase.** `python3 research/packaging/keywords.py "seed" …` with 3–6 seeds from the episode, then again with the autocomplete
   suggestions that fit. Save the table to `episodes/<slug>/packaging/keywords-<date>.md`.
2. **Pick one "target" phrase whose top results match your viewer** (your audience, not a neighbouring one). Read its
   best small-channel result: that's the title to beat. Example of a strong target: a top-10 median of 41k views where a
   3,940-subscriber channel ranks with 84k.
3. **Put the exact phrase in the first ~50 characters** (YouTube shows no fixed cut-off; mobile shows roughly 50–70).
   Say it in the description's first summary line and on camera in the first 30 seconds. Tags play a "minimal role"
   (YouTube Help), so 5–8 is plenty.
4. **Cross-check in Studio → Research (Trends tab)**: search volume level and content gaps. It's manual, in your own Studio login.
5. **Launch with Studio A/B Testing**: up to 3 titles (each with the phrase up front) or thumbnails. The winner is picked
   by watch-time share and the test finishes within 2 weeks. Desktop Studio only, needs Advanced Features. Editing the
   title or thumbnail stops the test.
6. **Day 7:** read the video's YouTube-search terms and CTR. If impressions and CTR are both low, change the title.
   YouTube says a change doesn't penalize the video. Search terms: YouTube Analytics API (`insightTrafficSourceDetail`
   filtered to `YT_SEARCH`). Impressions and CTR aren't in that API. They come from the YouTube Reporting API: create a
   `channel_reach_combined_a1` job once (`jobs.create`), then read its daily CSVs via `jobs.reports.list`.

## Titles
- The angle carries the clicks; style alone barely separates a channel's top 30 from its bottom 30. Setup tutorials that
  break out promise **one plain benefit**: "How to Use [tool] for Free (2026)", "How To Set Up [tool] In 3 Minutes".
- End with a **bracket qualifier** when it's true: "(Free Kit)", "(2026)", "(Full Course)", "(+ Results)". About a third of
  the teardown's titles do. It's style, not a ranking lever: two large studies found no bracket effect (a year tag maybe +9%),
  so cut the bracket before you cut the search phrase.
- Business videos: first person + a real receipt + "Here's How" ("I Built [result] with [tool], Here's How").
- Your voice still rules: no hype words ("insane", "kills", "terrifies"), only claims you made on camera.

## Descriptions
1. Line 1: the **free resource link** (kit), above YouTube's "…more" fold.
2. Two lines: "If this is your first video: I'm [your name]…" who you are and why to trust you.
3. A 2–3 sentence summary of what they'll learn.
4. Chapters (each ≥ 10 s; labels are fine for setup tutorials, lessons for list videos).
5. Tool links, the honest limits, next episode, socials.

## Make the thumbnails
`skills/content-pixel/scripts/thumbs.py SPEC.json` (Kie.ai GPT Image 2.5 Sunburst, 10 credits each, cap per spec). The spec lists
each variant's reference images (a real frame of you from the episode, the real logos or screenshot, 1–2 reference
thumbnails from `<slug>/thumbs/` for composition) and its prompt. Example spec: `skills/content-pixel/SKILL.md`.
