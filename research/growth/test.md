# One test at a time

The growth loop's memory. Your daily growth review (a scheduled task, mornings) reads this file, judges, and writes the
next change. Numbers come from `posts.csv` and `daily.csv` (`python3 system/schedule.py growth`). What a test keeps becomes
a rule in `../retention/RULES.md`, the script rules every new Reel is checked against (avatar-shorts step 2); the Friday
retention report (`../retention/retention.py`) is the deeper weekly read of where people leave.

## Running

<!-- One test at a time. Copy this block for each new test.
**T1 · Test name** (started YYYY-MM-DD)
- Problem: the leak this test targets (Rules § 6 order) and the number that shows it.
- Change: the one thing that changes (for example only the first sentence, spoken and the caption's first line).
- Tests RULES.md rule N on the platform where it hasn't been measured.
- Why: the numbers from your own posts that point at it.
- Measure: trial skip % against its main Reel's after 48 h; then average watch seconds; views last (trials only reach
  non-followers, mains reach followers too).
- Trials so far: 0 made, 0 of 3 judged.
-->

A good first test is **Open with a stake** (RULES.md rule 1): most Reels lose most of their viewers in the first 3 seconds,
and in the first batch this kit was built on, `stake` openings had the lowest skip rate of any opening type.

## Rules

1. One running test. A trial is the day's main Reel with one thing changed (rule 6), posted a few minutes after the main
   to non-followers only (Instagram Trial Reels).
2. Make a trial only when today's main Reel doesn't already do what the test changes. If it does, skip the trial (no credits) and
   note it; the main still counts against the typical Reel.
3. The new line must be true: built from the Reel's own script and verified claims, in your voice
   (`brand-system/voice/voice-rules.md`), no em dashes, no invented numbers or stories.
4. Verdict per trial, 48 h after posting: **win** if the trial's skip % is at least 5 points under its main's, **loss** if 5 or
   more over, otherwise **tie**.
5. After 3 trials: **keep** on 2 or more wins and fewer losses than wins; **drop** on 2 or more losses; otherwise run 2 more.
   Kept: add or confirm the rule in `../retention/RULES.md` as `keep` with the numbers; dropped: mark it `retire` there with
   the date. Then start the next test.
6. Next test = the biggest leak on the path to a follow, in this order: skip % (first 3 s) → the second YouTube viewers leave
   (posts.csv `drop_at_s`) → shares and saves per 100 views → profile visits per 100 reached → follows per profile visit
   (daily.csv `ig28_*`). Prefer a RULES.md `testing` rule aimed at that leak. A trial changes one thing: the first sentence
   (`skills/avatar-shorts/scripts/reel.py rehook`, HeyGen credits) or, for an edit rule, only the copy's spec.py (no credits).
   Profile and bio changes are yours to make: the review recommends them, never makes them.
7. Budget: one trial a day, about 4 HeyGen credits each. No trial when premium credits are under 40 (main Reels need them).
8. Under 6 Reels of a type there is no pattern: say so instead of inventing one.

## Opening types

Used in post.json `vars.opening`, a trial's `opening` and the posts.csv `opening` column.

| Type | What it does | Example shapes |
|---|---|---|
| `stake` | names a concrete cost, risk or limit: a dollar figure, a mistake to avoid ("Don't… until"), something AI can't do or gets wrong, a specific result tied to people | "Claude can't watch videos", "Someone got quoted $N to build an app", "Don't let Claude build your website until" |
| `news` | something just launched | "X just landed inside ChatGPT" |
| `demo` | "I typed one…", "This video was made with…" | "I typed one line and…" |
| `count` | a big count of things | "Six billion people…", "over a million AI skills" |
| `claim` | "You can now…", "I use…", "Claude can…" | "You can now…" |
| `problem` | "X usually comes out looking bad" | "AI video usually comes out looking bad" |
| `you-think` | "Most people…", "You see X and think…" | "Most people still think…" |

## Trials

| Posted | Reel | Main opening | Trial opening | Main skip % | Trial skip % | Main / trial views | Verdict |
|---|---|---|---|---|---|---|---|
