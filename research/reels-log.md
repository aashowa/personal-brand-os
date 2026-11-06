# Reels log

What each Reel did, so the next ones are built on your numbers instead of guesses. Method adapted from Jake Schincariol's `ig-audit` (MIT, github.com/Jakeschincariol/instagram-agent-skill).

**Every Friday:** `python3 system/schedule.py reels` prints the YouTube columns for every published Reel. Instagram numbers come from each Reel's Insights (read-only): views, % from non-followers, shares, follows. Add new rows, update rows younger than a week.

| Metric | How | Tells you |
|---|---|---|
| **× median** | views / the median of your Reels | a real hit or a normal day; raw views mostly track followers |
| **Stayed** | YouTube engaged views / views (the share who didn't swipe away); on Instagram, the 3-second hold on the retention graph | how good the hook was |
| **Avg %** | average share of the Reel watched | whether the middle held |
| **Shares / 100** | shares per 100 views | the strongest signal a Reel can earn |
| **Follows / 100** | subscribers or follows per 100 views | whether the profile turned attention into followers |
| **Non-follower %** | Instagram only | whether it travelled past people who already follow |

Two rules before changing anything:
- **Views but no follows is a profile problem** (bio, pinned Reels), not a hook problem. **No views is a hook problem**: compare Stayed.
- Under about 6 Reels there is no pattern. Check day and time last.

## Log

| Posted | Reel | Hook (first line) | YT views | × med | Stayed | Avg % | Shares / 100 | Subs / 100 | IG views | IG non-follower % | IG shares | IG follows | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
