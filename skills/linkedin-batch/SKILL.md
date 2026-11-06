---
name: linkedin-batch
description: "Draft LinkedIn posts by retelling the creator's approved videos (Reels and episodes) as personal posts, then schedule the ones they approve. Use for 'linkedin posts', 'this week's linkedin', 'repurpose for linkedin', 'linkedin batch'."
---

# LinkedIn batch

LinkedIn retells each approved video as a personal post from the creator's own work. It is not a lead engine: the only link is the creator's site (`creator.site_url` in `config.json`).

Read first: `linkedin/PLAYBOOK.md` (anatomy, hooks, format, cadence, test log) and `brand-system/voice/voice-rules.md`. All paths below are from the repo root.

## Steps

1. **Find what to retell.** `python3 system/schedule.py list` shows the queue. Every approved video folder in `episodes/` that has a `post.json` but no `linkedin.txt` is a candidate, in publish order. Check the playbook's Test log for what's working.
2. **Draft** `<video_dir>/linkedin.txt` from that video's `script.txt` / `script.md` and `post.json`, following the playbook anatomy. Use the user's facts and words only. If a post needs a real moment (a busy day at their business, a customer call), ask the user for it rather than inventing one. Rotate post types, and don't give two posts in a row the same cadence.
3. **Graphic.** Each slide is a short title plus one real Excalidraw diagram: add a scene to `linkedin/creative/diagrams.mjs` (and its folder to `WHERE`) and run `node linkedin/creative/diagrams.mjs <name>`. Write `<video_dir>/linkedin.html`, one `<section class="slide">` per image:

   ```html
   <!doctype html>
   <html><head><meta charset="utf-8"><meta name="style" content="diagram"><title>Post title (the carousel PDF title)</title>
   <link rel="stylesheet" href="../../linkedin/creative/brand.css"></head>
   <body>
   <section class="slide">
   <div class="label">Short kicker</div>
   <h2>Title in eight words, <span class="hl">one highlight.</span></h2>
   <div class="fig"><img src="example-steps.png" alt=""></div>
   </section>
   </body></html>
   ```

   The `style` meta is one of `diagram`, `prompts`, `screenshot` or `statement`; `schedule.py linkedin` refuses two posts in a row with the same style. It must teach something: a step-by-step video becomes an 8-slide carousel, anything else one diagram. Render with `python3 linkedin/creative/render.py <video_dir>` and look at every PNG for overflow.
4. **Stop and show the user** the exact texts and the slot each will get (dry run: `python3 system/schedule.py linkedin <dir>`). Nothing is scheduled without their OK.
5. **On their OK**, run `python3 system/schedule.py linkedin <dir> --topic <slug> --go` for each post (same topic stays a week apart on LinkedIn), in the order they want them. Then `schedule.py list`.
6. **Friday:** fill in the playbook's Test log, raw numbers plus eng. rate, comment ratio and reach ×, from each post's analytics (the user's LinkedIn profile → Activity → each post → View analytics, read-only in their browser, or a screenshot from them; GHL has no analytics for personal profiles). After every 6 posts, change one thing.

## Hard rules

- Readers are business owners, not techies. Every tech word gets an everyday comparison or is cut.
- No AI tells: no "Here's how/what…", no "Stop…", no stacked one-line zingers, no "game-changer", "unlock" or "thrilled", no engagement gates.
- Never use client names (unless there's a public case study), client revenue, secrets, or invented numbers.
