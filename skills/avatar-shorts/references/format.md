# The format: Nick Saraev's Reel structure, with your proof

Source: a frame-by-frame teardown of @nick_saraev's last 40 Reels. Faces were identified per frame at 5 fps
(his face, not faces inside assets), and Gemini wrote a shot list per Reel. Re-run it on any creator with
`scripts/teardown/` (§ Refreshing the format).

## Screen time (the number that matters)

| | Presenter full screen | Split (asset top, presenter bottom) | Graphics only |
|---|---|---|---|
| Nick, all 40 | 25% | 30% | 45% |
| Nick, top 10 by plays | 21% | 25% | 54% |
| **Target** | **~20%** | **~28%** | **~52%** |

Assets are on screen ~75% of the time. That is why an avatar works here: the face carries the hook, a couple of
beats and the CTA, and is covered the rest of the time. `reel.py build` prints the mix; fix the spec if face goes
over ~25% or graphics under ~45%.

**Bookends (40 of 40):** open on the split layout (hook over a real asset), end on the presenter full screen saying
the CTA. Layout changes about every 3 s; median runs: face 1.8 s, split 2.4 s, graphics 2.8 s.

## Structure

Nick Saraev's and adilet.fndr's flow, in your own words (a teardown of their top 26 Reels). It replaces Kallaway's
block order (lock-in zone, mid-video re-hooks); the four S's and the moves below still apply. Label each line's job in
the script you show for approval.

| Job | Lines (words) | What it does | Layout |
|---|---|---|---|
| Hook | 1 (12–18) | The whole promise in one breath: the result, who it's for, the price or effort. Shapes: "You can now…", "Don't … until you've…", "Someone just…", "Your … can …". Passes the four S's | Split, real asset on top. Frame 0 is the feed thumbnail: already filled, no entrance animation |
| Open loop (optional) | 1 (~10) | Promises the payoff for the end ("and at the end, I'll show you the one mistake to avoid"). Only when the Reel has a closing turn to pay it off | Split or face |
| Name it | 1 (15–20) | "It's called X, and it's basically [one plain phrase]", or where it came from (who built it and why). It can wait until after the body when the body paints the scene first | Face or a full-screen graphic |
| Body | 3–6 short lines (50–80) | Items chained with "So", "Plus", "And", "The first… And finally". Each item is a job or name, what it does for you, and one concrete detail. One "you just" line shows how little effort it takes | Mostly graphics; a split for real footage |
| Closing turn | 1–3 (15–30) | One reassurance, reframe or tip that sums it up, then your receipt: how you use it in your business. Pays off the open loop | Face, then real footage of your setup |
| CTA + aligned lead magnet | 1 (~12) | Follow me and comment "WORD", and I'll send it to you directly. Under 8% of the runtime. A value ramp: the free thing is the same topic as the Short, one level deeper, never a generic link | Face, CTA chip with the word, captions hidden under the chip |

Length: 30–50 s after pause cuts. Voice C runs about 240 words a minute (155 words in 38.4 s on a test Reel), so
that's about 120–200 words. Nick's median is 162 words in 37 s.

### Flow rules (Nick + adilet)

- Every sentence is a new fact. No signposts: "here's what's inside", "here's the thing", "but guys, here's the mistake". The next fact is the transition.
- Second person: their Claude, their app, their customers.
- Concrete over category: a job, a verb and an object ("preps your calls and writes your proposals"), never "helps with sales".
- How-to Reels go staccato: 8–12 words a sentence, numbered ("First… Next… Then… Now, the fun part").
- It's still your voice (`brand-system/voice/tone.md`): your usual sentence starters and filler words at most once each, no hype words.

### The hook: the four S's

- **Subject:** the subject is clear in the first sentence.
- **Stakes:** there's a reason your viewer has to keep watching.
- **Simple:** the simplest words that work.
- **Superclear:** a short, punchy sentence that's easy to follow.

### Writing rules

- Cut fluff. As short as possible.
- Clear logic: every sentence either follows from the one before or clearly starts a new thread. Jumping around makes it impossible to follow.
- Tease the value as early as possible, so they know why to keep watching.
- Simple words whose meaning is already obvious; clarity over everything.

### The name-it line or the closing turn: pick one move (Kallaway's lock-in moves)

From Kallaway's lock-in zone guide. Pick the one that fits the hook, and name the move next to the block when you show
the script. The examples are shapes: fill the brackets with your own receipts, true and in your voice (`tone.md`).

| Move | How it works | Use it when | Example shape |
|---|---|---|---|
| Teasing proof | One concrete, tactical proof point that backs the hook's claim; it makes what's coming feel qualified | You have a real number. The default: receipts are the channel | Hook: "AI does the books for my business now." Lock-in: "It's gone through [N] receipts in [three months], and I was paying [$X] a month for this." |
| Teasing the transformation | Frame the line around the result they want most | There's no stat, but the outcome is obvious | "Set it up once, and your weekly expense check is done before you even open your accounting app." |
| Clarifying contrast | State the common belief, then the alternative: A versus B | The hook goes against what people assume | "Most people think you need a media buyer to run ads. I run them for [N] clients with one person." |
| Magic box | Name the method, term or framework that solves it, before explaining it | You have a named thing (a framework, a skill, "the whole system in one line") | "It comes down to three foundations, and the first one is chatbot versus agent." |
| Objection handling | Knock down their number-one objection straight away | Beginners will think "this isn't for me" | "And no, you don't need to know how to code." |
| Double down | Say the hook's claim again a different way, stronger and clearer | The hook is new or uses a word they may not know | "It doesn't suggest the campaign. It builds it, paused, ready for me to check." |

## Angle

**Proof-based, not generic tool roundups.** Nick's topics are "free AI tool / plugin pack / leak / just launched".
Your version is the same shape with proof from your own business: "I use this to do X in my business". Every claim
must be one you have already made on camera, or one verified against a primary source before scripting. Read
`brand-system/voice-guide.md` before writing: receipt before theory, first person, honest boundary, no
"unlock / seamless / leverage".

**CTA (exact wording):** Follow me and comment "WORD", and I'll send it to you directly. A GHL workflow likes the
comment, replies "sent it to your DMs" and DMs your site link on Instagram and Facebook; the word must be in
`system/comment-words.md`. Point it at something real and free (a kit, an episode asset, a repo in the library),
because the CTA works when there is a thing to get. TikTok and YouTube have no auto-DM, so the caption also says
"Link's in my bio."

## Script rules

- About 120–200 words on voice C (TTS speed 1.2, about 240 wpm after pause cuts), so 30–50 s depending on the topic.
- Follow the flow in § Structure: hook → (open loop) → name it → body → closing turn with your receipt → CTA with the
  aligned lead magnet. No signpost sentences and no mid-video re-hook.
- Write it the way you talk: `brand-system/voice/tone.md` (your real phrasing, with snippets from your own transcripts).
- Write for the avatar: plain words, short sentences. Avoid "set-and-forget" style hyphen chains (spoken fine, but
  whisper splits them), and spell numbers the way you say them ("30", "$300"). Write acronyms and names plainly
  (MP4, API); the HeyGen glossary handles how they sound. Keep hard tool names (FFmpeg) on screen rather than in the voice.
- Every on-screen number must appear in the script or the proof.

## Topic research (step 1)

Present 3 options, each with title, hook line, items, the proof for each claim, and the free thing for the CTA. Sources:
1. Your own record: `episodes/*/` scripts, run sheets and packaging notes: claims already made on camera and the tools
   you actually run.
2. What's moving: `research/outliers/IDEAS.md` and the latest radar digest's Outliers section (`research/radar/`,
   the creators you track), or the `content-scout` skill.
3. Comments: a question under a Reel that many people share is its own Reel. Instagram attaches the comment to a
   Reel that replies to it, and the asker gets notified (idea from Jake Schincariol's `ig-reply`).
4. Never present a claim you could not trace to (1) or a primary source.

## Visual language (kit + additions)

- Paper-and-ink brand (Bricolage 800, JetBrains Mono chips, marker yellow, terracotta and cobalt accents).
  Yellow caption chip on the seam in split beats, low (y 1260) in face and graphics beats, 1–3 words.
- Every full-screen graphic **kicks** in (scale 1.12→1 in 0.22 s + whoosh). Logos pop with an impact; headlines slam.
- **A character on Claude topics:** the Claude Code crab acts out 2–4 moments (drops in, dances, peeks, wears a prop,
  splits into a team) and optionally one animated emoji sticker. See spec.md § Characters.
- **Snap zooms** (0.06 s) on emphasis words and on every pause cut; that also hides the jump in the avatar.
- **Graphics explain each line.** adilet.fndr's rule: one object per sentence that acts the sentence out and changes in
  place: an org chart that builds for "a whole agency", a call card whose questions tick off for "preps your calls", a
  page that writes itself and gets a stamp, posts dropping into a week calendar, a reply typing itself. The real screen
  stays as the receipt (the tool's own README row as a strip above its object, the repo, the app, your own folder),
  never the whole explanation. Add a 1/4 tally on list items, number rolls, stamps, and colour flips by section (red
  background for the mistake, ink for the fix) with `s.wipe_full` at the flips. A screenshot in a card plus a highlight
  box plus a chip, beat after beat, reads as a slideshow.
- **Fill the zone.** A full-screen graphic spreads over the whole safe zone, x 60-1020 and y 230 down to the caption
  line (about 1240; to 1440 when the beat hides captions), not a cluster at the top with empty paper below. Size objects
  up (org chart boxes 330 tall, tile wall to y 1340, a chat window 250-1150); decoration (tiles, piles, the crab) may
  run into the lower right. Split tops fill y 60-900. Check it on the snapshot sheet.
- **adilet's visual system on full-screen beats** (from adilet.fndr's own "how I make every reel" breakdown).
  The spoken phrase is the caption, big at the top left (96 px, y 290) with key words in red italic serif (Instrument
  Serif, in the kit fonts), no yellow chip; a small "// 03 · the build" chapter label above it; one hero object below
  (y 500 on). Objects are Microsoft Fluent 3D emoji (MIT, 1,500+), never system emoji:
  `reel.py props REEL_DIR "Money bag" ...`. 1-2-3-4 progress boxes on list items, halftone dot transitions at section
  changes. Write small helpers for these once in a spec (headline, chapter label, prop, tally, halftone) and copy them
  from Reel to Reel. More ready pieces: `npx hyperframes catalog --query "..."` (448 items: number-wheel,
  halftone-dissolve, hw-text-cloud, marker-checklist-card, lottie-character-walk, notification-pileup).
- **Safe zone (rule):** Instagram draws its interface over the top 230 px, everything below y 1440 (username,
  caption) and the lower right 230 px (like, comment, share). Headlines start at y 230 or lower; nothing that must be
  read goes below 1440 or in x > 850 under y 960; the CTA chip sits at y 1250. Decoration (crowds, the crab) may cross
  the edges. The kit's low captions sit at 1260 for this. `reel.py master` writes `<slug>-safe.jpg` (eight frames, the
  zones shaded red): read it before sending. Zones from Jake Schincariol's `ig-reel`.
- Sound effects at −19 dBFS peaks, dense, about 50 per 33 s. A riser into the title card, cash register on money,
  glitch on "break", boom on the payoff number. Music bed ducked under the voice.

## Refreshing the format (optional)

`scripts/teardown/screentime.py` (needs OpenCV with the YuNet + SFace ONNX models from github.com/opencv/opencv_zoo)
and `scripts/teardown/gemini_reel.py`, `gemini_motion.py`, `gemini_assets.py` (`GEMINI_API_KEY` in the environment)
re-run the teardown on any creator's downloaded Reels. Keep the outputs as your own notes; they describe someone
else's work.
