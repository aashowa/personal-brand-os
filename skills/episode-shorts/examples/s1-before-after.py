"""Example spec (~45 s, made-up script): the weekly report went from 30 minutes to 2.

Shows the patterns a Short needs: a filled frame 0, a full-screen kick, synced footage, logo pops, checklist rows, a fixed
B-roll range, a camera punch, a photo beat and the comment-CTA end card. Every s.T("word", after) keys on a word in this
Short's assets/words.json, so it only builds against a transcript that says these lines:

  Writing the weekly report used to take me thirty minutes. Now it takes two. So every Monday I open Claude and give it
  one prompt. It reads the sheet, writes the summary and drafts the email. Here's the real one from today. All I gave it
  was the sheet and last week's email. And this is the result. If it looks right, I approve and it sends. That's thirty
  minutes back, every week. Comment REPORT and I'll send you the prompt.

Copy it to <shorts>/_build/<name>.py and replace the words, crops, ranges and files with your own; keep the shape.
Logos: assets/logos/README.md. Photos: shorts.py photos get <id> stopwatch|desk <shorts>/photos.
"""

KEYWORD = "REPORT"   # must be listed in system/comment-words.md


def make(s):
    T = s.T; D = s.D
    tNow, tSo, tIt, tHere = T("now"), T("so"), T("it", T("prompt")), T("here's")
    tAll = T("all"); tAnd = T("and", T("email", tAll)); tIf, tThat, tCom = T("if"), T("that's"), T("comment")

    # B1 · the old way: 30 minutes. Everything is on screen at t = 0 (frame 0 is the feed thumbnail)
    p1, ph1 = s.photo("stopwatch.jpg", (680, 140, 330, 380))
    c1, chip1 = s.chip("Weekly report", "b", "left:70px;top:118px")
    h1, head1 = s.head('<span id="n30">0</span> min', 190, "left:64px;top:280px;font-variant-numeric:tabular-nums")
    c1b, chip1b = s.chip("The old way", "w", "left:76px;top:540px;font-size:36px")
    l1, logo1 = s.logo("googlesheets_c.png", 150, style="left:80px;top:690px")
    s.push(f"#{p1}i", 0, tNow, 1.12)
    s.count("#n30", 0.2, tNow - 0.1, 0, 30)
    s.pop(f"#{c1b}", T("used")); s.pop(f"#{l1}", 0.4)
    s.beat(0, tNow, ph1 + chip1 + head1 + chip1b + logo1)

    # B2 · FULL-SCREEN kick: 30 min struck, 2 min slams in (also covers repaired camera frames here)
    s.wipe_full(tNow)
    l2a, lg2a = s.logo("claude_c.png", 170, style="left:90px;top:1240px")
    l2b, lg2b = s.logo("gmail_c.png", 170, style="left:500px;top:1240px")
    inner = lg2a + lg2b + ('<div class="head" id="old" style="left:72px;top:380px;font-size:220px;color:var(--pencil)">30 min</div>'
                           '<div style="position:absolute;left:56px;top:490px;transform:rotate(-6deg)"><div class="strike" id="stk" style="position:relative;width:650px;height:30px"></div></div>'
                           '<div class="head" id="new" style="left:60px;top:630px;font-size:350px"><span class="mk">2 min</span></div>'
                           '<div class="bar" id="arw2" style="left:300px;top:1312px;width:180px;height:26px;background:var(--ink);border-radius:13px"></div>'
                           '<div class="mono" id="sub2" style="position:absolute;left:80px;top:1150px;font-size:32px;letter-spacing:.12em;color:var(--pencil)">ONE PROMPT &#183; CLAUDE WRITES IT &#183; I APPROVE</div>')
    s.pop("#old", tNow, sfx=None); s.draw("#stk", T("takes", tNow), 0.3, sfx="whoosh-short")
    s.slam("#new", T("two"), sfx="impact-bass-1"); s.rise("#sub2", T("two") + 0.35)
    s.pop(f"#{l2a}", T("two") + 0.5, sfx=None); s.draw("#arw2", T("two") + 0.7, 0.3, sfx=None); s.pop(f"#{l2b}", T("two") + 0.9)
    s.beat(tNow, tSo, inner, full=True)

    # B3 · what was on screen while it was said (synced footage) + the tool's logo
    fid, frame, _ = s.foot(tSo, tIt, s.sync(tSo, tIt), (0.1, 0.0, 0.75), "wide", "My setup")
    l3, logo3 = s.logo("claude_c.png", 150, style="left:860px;top:690px")
    h3, head3 = s.head('One <span class="mk">prompt.</span>', 100, "left:60px;top:92px")
    s.pop(f"#{l3}", T("claude")); s.slam(f"#{h3}", T("prompt"))
    s.beat(tSo, tIt, frame + logo3 + head3)

    # B4 · a list: rows snap in on each spoken item, camera punch on the last
    h4, head4 = s.head("Claude:", 110, "left:90px;top:110px")
    inner = head4 + ''.join(f'<div class="row" id="r4{i}" style="left:90px;top:{300 + 170 * i}px"><span class="tick">&#10003;</span><span>{t}</span></div>'
                            for i, t in enumerate(("Reads the sheet", "Writes the summary", "Drafts the email")))
    s.slam(f"#{h4}", tIt, sfx=None)
    for i, w in enumerate(("reads", "writes", "drafts")): s.snap(f"#r4{i}", T(w), 300, sfx="pop")
    s.beat(tIt, tHere, inner)
    s.cam_punch(T("drafts"), T("drafts") + 1.0, 1.1)

    # B5 · the real thing, today (synced footage; the export's privacy blur carries over)
    fid, frame, _ = s.foot(tHere, tAll, s.sync(tHere, tAll), (0.1, 0.1, 0.62), "wide", "Real one · today")
    c5, chip5 = s.chip("Details blurred", "w", "left:690px;top:830px;font-size:30px")
    h5, head5 = s.head('From <span class="mk">today.</span>', 96, "left:60px;top:96px")
    s.slam(f"#{h5}", T("today")); s.pop(f"#{c5}", tHere + 0.6, sfx=None)
    s.beat(tHere, tAll, frame + head5 + chip5)

    # B6 · all I gave it (logos with labels)
    h6, head6 = s.head("All I gave it:", 110, "left:70px;top:110px")
    la, lga = s.logo("googlesheets_c.png", 220, "The sheet", "left:150px;top:330px")
    lb, lgb = s.logo("gmail_c.png", 220, "Last week's email", "left:620px;top:330px")
    s.slam(f"#{h6}", tAll, sfx=None); s.pop(f"#{la}", T("sheet", tAll)); s.pop(f"#{lb}", T("email", tAll))
    s.beat(tAll, tAnd, head6 + lga + lgb)

    # B7 · the result: a FIXED 1x range of the long-form as B-roll (not synced), square card with a slower push
    fa, fra, _ = s.foot(tAnd, tIf, (600.0, 604.5), (0.3, 0.1, 0.4), "square", "The result", push=1.1)
    s.beat(tAnd, tIf, fra)

    # B8 · approve -> sent (bubble, arrow, logo, chip)
    c8, chip8 = s.chip("You approve", "y", "left:90px;top:120px;font-size:40px")
    l8, logo8 = s.logo("gmail_c.png", 240, "Gmail", "left:760px;top:330px")
    inner = chip8 + logo8 + ('<div class="bubble me" id="ap" style="left:90px;top:370px;font-size:64px;font-weight:800">approve</div>'
                             '<div class="bar" id="arw8" style="left:420px;top:436px;width:300px;height:26px;background:var(--ink);border-radius:13px"></div>')
    c8b, chip8b = s.chip("Sent", "b", "left:90px;top:720px;font-size:40px")
    s.pop(f"#{c8}", tIf); s.pop("#ap", T("approve")); s.draw("#arw8", T("approve") + 0.4, 0.4, sfx="whoosh-short")
    s.pop(f"#{l8}", T("approve") + 0.7); s.slam(f"#{c8b}", T("sends"), sfx="ping")
    s.beat(tIf, tThat, inner + chip8b)

    # B9 · the payoff on a free real photo with two chips
    p9, ph9 = s.photo("desk.jpg")
    c9, chip9 = s.chip("30 min back", "y", "left:140px;top:780px;font-size:48px")
    c9b, chip9b = s.chip("Every week", "b", "left:520px;top:780px;font-size:48px")
    s.card_in([f"#{p9}"], tThat); s.push(f"#{p9}i", tThat, tCom, 1.08)
    s.slam(f"#{c9}", T("thirty", tThat)); s.slam(f"#{c9b}", T("week", tThat))
    s.beat(tThat, tCom, ph9 + chip9 + chip9b)
    s.cam_punch(T("week", tThat), T("week", tThat) + 0.9, 1.08)

    # B10 · FULL-SCREEN end card: the comment CTA (wording from config.json episode_shorts.cta)
    s.wipe_full(tCom)
    c10, chip10 = s.chip("Free prompt", "y", "left:80px;top:250px;font-size:44px")
    inner = chip10 + ('<div class="head" id="cm10" style="left:70px;top:390px;font-size:160px">Comment</div>'
                      f'<div class="head" id="kw10" style="left:60px;top:580px;font-size:250px"><span class="mk">{KEYWORD}</span></div>'
                      '<div class="mono" id="sub10" style="position:absolute;left:80px;top:880px;font-size:40px;letter-spacing:.1em;color:var(--pencil)">AND I&#8217;LL SEND IT RIGHT TO YOU</div>'
                      f'<div class="bubble" id="cb10" style="left:80px;top:1010px;font-size:58px;font-weight:800">{KEYWORD}</div>'
                      '<div class="bubble me" id="rp10" style="left:330px;top:1170px;font-size:46px">Sent it to you &#10003;</div>')
    s.pop(f"#{c10}", tCom, sfx=None); s.slam("#cm10", tCom + 0.05, sfx=None)
    s.slam("#kw10", tCom + 0.35, sfx="impact-bass-1"); s.rise("#sub10", tCom + 0.8)
    s.pop("#cb10", tCom + 1.3); s.pop("#rp10", tCom + 2.1, sfx="ping")
    s.beat(tCom, D, inner, full=True)
