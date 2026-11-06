# Comment words (comment → DM)

Every Reel ends with one CTA: Comment "WORD" and I'll send it to you directly (or it's at the link in my bio).
This file is the list of WORDs. A comment on Instagram or Facebook that contains any word below gets a like, a public
"sent it to your DMs" reply and a DM with your site link (`creator.site_url` plus `?src=ig-comment` or `?src=fb-comment`,
so the email gate records where the visitor came from). One GHL workflow covers every video.

## The GHL workflow (set up once)

In your GHL location, Automation → Workflows, make one workflow, for example **Comment to DM | Free files**:

1. Triggers: "Instagram comment" and "Facebook comment" on your connected accounts, filtered to "comment contains"
   each word in the list below (with its forms and typos, see the rules).
2. Actions: like the comment, reply publicly ("Sent it to your DMs"), send the DM with the link.
3. Publish it, then test it live with a comment from a second account.

New word for a video: add it to the list, then add it to the same workflow's triggers before the video's slot. Update the
existing workflow; never make a new one per video. If you script that sync, have the script read this list.

## Rules

- 4+ letters, not hidden inside everyday words. "Contains" matches inside words: KIT fires on "kitchen", REPO on
  "report", ADS on "heads".
- Add UPPER, Title and lower forms of each word, since GHL's matching may be case-sensitive.
- Short words (AI, GPT) only in capitals, exactly as written. That works only if GHL's matching is case-sensitive: the
  live test checks it, and if it isn't, take them out (lowercase "ai" is inside "said", "again", "email"). A broad word
  fires on any comment that mentions it in passing; keep it only if you want that.
- Typos: add every one-slip typo of each word (a missed, swapped, doubled or next-key letter), minus any that sit inside
  a normal English word ("kill" from SKILL). If a real typo gets blocked by a rare dictionary word, list it by hand.
- Comments from private Instagram accounts never reach GHL (Instagram hides them from apps): answer those by hand.
- YouTube and TikTok comments are not covered; the "link in my bio" half of the CTA serves them.

## Format

One word per line, in capitals, as a `- WORD` list item under "Words". Hand-added typos go in the same list.

## Words

- WORD (placeholder: replace with your first video's word)
