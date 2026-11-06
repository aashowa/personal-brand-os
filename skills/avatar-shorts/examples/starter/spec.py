"""Starter spec: "give your AI three things first" (~28 s after pause cuts). `reel.py new` copies it into every new Reel:
rewrite every beat for your script. Every time comes from a spoken word (`reel.py words REEL_DIR`), never a hard number,
so a re-render re-times everything. Mix target ~20% face / ~28% split / ~52% graphics: split open (frame 0 filled),
short face beats, full-screen kicks, face CTA. It uses no logos and no footage, so it builds on a fresh install once
the sound effects in assets/README.md are in place."""
import re


def make(s):
    D = s.D

    def W(*keys, after=0.0):
        """First word at/after `after` starting with any key (punctuation ignored; whisper may write "ten" as "10")."""
        for a, e, t in s.words:
            if a >= after - 1e-6 and any(re.sub(r"[^\w$']", "", t.lower()).startswith(k) for k in keys): return a
        raise KeyError(f"{s.name}: no {keys} after {after:.2f}")

    def before(t):
        """Start of the word just before t (for a beat that opens on a short word like "You")."""
        return max(a for a, e, w in s.words if a < t - 1e-6)

    tGeneric = W("generic"); tNothing = W("nothing", after=tGeneric)
    tSo = W("so", after=tNothing); tGive = W("give", after=tSo); tThree = W("three", "3", after=tGive)
    tFirst = W("first", after=tThree); tJob = W("job", after=tFirst); tCust = W("customer", after=tJob); tWork = W("work", after=tCust)
    tPlus = W("plus", after=tWork); tPaste = W("paste", after=tPlus); tCopies = W("copies", after=tPaste); tStyle = W("style", after=tCopies)
    tAnd = W("and", after=tStyle); tRules = W("rules", after=tAnd); tMaking = W("making", after=tRules); tSending = W("sending", after=tMaking)
    tYou = before(W("just", after=tSending)); tTop = W("top", after=tYou); tEvery = W("every", after=tTop)
    tIt = W("it", after=W("chat", after=tEvery)); tTen = W("ten", "10", after=tIt); tAnd8 = W("and", after=tTen)
    tWrite = W("write", after=tAnd8); tOnce = W("once", after=tWrite)
    tFollow = W("follow", after=tOnce); tComment = W("comment", after=tFollow); tWord = W("note", after=tComment)

    # B1 · SPLIT hook: a one-line ask and the generic reply it gets (on screen from frame 0: it is the feed thumbnail)
    c1, chip1 = s.chip("Your AI · today", "y", "left:80px;top:96px")
    inner = chip1 + (
        '<div style="position:absolute;left:80px;top:190px;width:920px;height:250px;background:#fff;border:5px solid var(--ink);border-radius:36px;box-shadow:0 14px 0 var(--ink)">'
        '<div style="position:absolute;left:44px;top:40px;width:740px;font-size:58px;font-weight:500;line-height:1.18;letter-spacing:-.02em">'
        '<span id="typed"></span><span id="caret" style="display:inline-block;width:5px;height:60px;background:var(--ink);vertical-align:-8px;margin-left:4px"></span></div>'
        '<div id="send" style="position:absolute;right:34px;bottom:28px;width:84px;height:84px;border-radius:22px;background:var(--ink);color:var(--marker);'
        'font-size:52px;font-weight:800;display:flex;align-items:center;justify-content:center">&#8593;</div></div>'
        '<div class="bubble" id="reply" style="left:80px;top:500px;width:920px;font-size:50px;color:var(--pencil)">'
        'Here are 10 tips to grow your business! 1. Post every day&#8230;</div>')
    st, stamp = s.chip("Generic", "", "left:600px;top:700px;font-size:60px")
    s.typing("#typed", "Write a post for my business.", 0.15, tGeneric - 0.2)
    s.js.append("tl.fromTo('#caret',{opacity:1},{opacity:0,duration:0.25,yoyo:true,repeat:5,ease:'steps(1)'},0.15);")
    s.js.append(f"tl.fromTo('#send',{{scale:1}},{{scale:0.8,duration:0.08,ease:'power2.in'}},{tGeneric - 0.2:.3f});")
    s.sfx.append((tGeneric - 0.2, "key-press"))
    s.pop("#reply", tGeneric - 0.05)
    s.slam(f"#{st}", tGeneric + 0.25, sfx="impact-bass-1")
    s.beat(0, tSo, inner + stamp)
    s.zap(tNothing, 0.6)

    # B2 · FACE: "So before you ask it anything,"
    s.face(tSo, tGive, zooms=[(W("any", after=tSo), 1.12)])

    # B3 · FULL title card: three things, numbered (kick + a riser into it)
    h3, head3 = s.head('3 things<br><span class="mk">first.</span>', 170, "left:90px;top:230px")
    inner = head3
    for i, (a, b) in enumerate([("Who you are", "job, customers, this week"), ("One example", "something you liked"),
                                ("The rules", "what it never does")]):
        inner += (f'<div id="n3{i}" style="position:absolute;left:90px;top:{600 + i * 220}px;width:900px;height:190px;'
                  f'background:{"var(--marker)" if i == 2 else "#fff"};border:6px solid var(--ink);border-radius:28px;box-shadow:0 12px 0 var(--ink);'
                  'display:flex;align-items:center;gap:40px;padding:0 48px">'
                  f'<span class="mono" style="font-size:80px">{i + 1}</span><div>'
                  f'<div style="font-weight:800;font-size:76px;letter-spacing:-.03em;line-height:1">{a}</div>'
                  f'<div class="mono" style="font-size:34px;color:var(--pencil);margin-top:10px">{b}</div></div></div>')
    s.slam(f"#{h3}", tGive + 0.05)
    for i in range(3): s.pop(f"#n3{i}", tThree + 0.15 * i, sfx="pop" if i < 2 else "impact-bass-1")
    s.kick(s.beat(tGive, tFirst, inner, nocap=True, full=True), tGive); s.sfx.append((tGive, "riser-short"))

    # B4 · FULL kick: the first thing, ticked off on each spoken word
    c4, chip4 = s.chip("The first", "y", "left:90px;top:240px;font-size:44px")
    h4, head4 = s.head('Who <span class="mk">you</span> are.', 130, "left:90px;top:340px")
    rows = [(tJob, "Your job"), (tCust, "Your customers"), (tWork, "This week&#8217;s work")]
    inner = chip4 + head4
    for i, (_, txt) in enumerate(rows):
        inner += (f'<div class="row" id="w4{i}" style="left:90px;top:{620 + i * 190}px;width:900px;font-size:70px">'
                  f'<span class="tick">&#10003;</span><span>{txt}</span></div>')
    s.snap(f"#{c4}", tFirst, sfx=None); s.slam(f"#{h4}", W("who", after=tFirst) - 0.05, sfx="impact-bass-1")
    for i, (t, _) in enumerate(rows): s.snap(f"#w4{i}", t - 0.1, 260, sfx="pop")
    s.kick(s.beat(tFirst, tPlus, inner, full=True), tFirst, "air-whoosh")

    # B5 · SPLIT: your own example goes in, the same style comes out
    c5, chip5 = s.chip("The second · one example", "w", "left:80px;top:96px")

    def doc(did, x, title, bg):
        lines = "".join(f'<div style="height:22px;width:{w}px;background:var(--pencil);opacity:.35;border-radius:11px;margin-top:26px"></div>'
                        for w in (300, 340, 260, 320))
        return (f'<div id="{did}" style="position:absolute;left:{x}px;top:200px;width:420px;height:560px;background:{bg};border:6px solid var(--ink);'
                f'border-radius:30px;box-shadow:0 14px 0 var(--ink);padding:40px 44px"><div class="mono" style="font-size:40px">{title}</div>{lines}</div>')
    inner = chip5 + doc("d5a", 80, "You wrote", "#fff") + doc("d5b", 580, "It writes", "var(--marker)")
    inner += '<div class="bar" id="a5" style="left:506px;top:470px;width:68px;height:20px;background:var(--ink)"></div>'
    s.snap(f"#{c5}", tPlus, sfx=None)
    s.card_in(["#d5a"], tPaste - 0.1)
    s.draw("#a5", tCopies - 0.25, 0.25)
    s.card_in(["#d5b"], tCopies, sfx="impact-bass-2")
    s.beat(tPlus, tAnd, inner)
    s.zap(tStyle, 0.5)

    # B6 · FULL kick: the third thing, what it must never do
    c6, chip6 = s.chip("The third", "y", "left:90px;top:240px;font-size:44px")
    h6, head6 = s.head('The <span class="mk">rules.</span>', 150, "left:90px;top:340px")
    rules = [(tMaking, "Make up numbers"), (tSending, "Send without your OK")]
    inner = chip6 + head6
    for i, (_, txt) in enumerate(rules):
        inner += (f'<div class="row" id="r6{i}" style="left:90px;top:{640 + i * 210}px;width:900px;font-size:70px">'
                  f'<span class="cross">&#10005;</span><span>{txt}</span></div>')
    s.snap(f"#{c6}", tAnd, sfx=None); s.slam(f"#{h6}", tRules - 0.05, sfx="impact-bass-1")
    for i, (t, _) in enumerate(rules): s.snap(f"#r6{i}", t - 0.1, 260, sfx="impact-bass-2")
    s.kick(s.beat(tAnd, tYou, inner, full=True), tAnd, "air-whoosh")

    # B7 · FULL: all three in one note, pasted at the top of every chat
    inner = ('<div id="note7" style="position:absolute;left:150px;top:260px;width:780px;height:600px;background:#fff;border:6px solid var(--ink);'
             'border-radius:30px;box-shadow:0 14px 0 var(--ink);padding:44px 50px">'
             '<div class="mono" style="font-size:52px">my-ai-note.md</div>'
             '<div style="margin-top:40px;font-size:60px;font-weight:500;line-height:1.6">'
             + "".join(f'<div id="l7{i}">&#8212; {t}</div>' for i, t in enumerate(("Who I am", "One example", "The rules"))) + '</div></div>')
    c7, chip7 = s.chip("Top of every chat", "y", "left:90px;top:1000px;font-size:48px")
    s.pop("#note7", tYou + 0.05, sfx="impact-bass-1")
    for i in range(3): s.pop(f"#l7{i}", tYou + 0.3 + 0.15 * i, sfx="pop" if i == 0 else None)
    s.snap(f"#{c7}", tTop - 0.1, sfx="impact-bass-2")
    s.kick(s.beat(tYou, tIt, inner + chip7, full=True), tYou)

    # B8 · FACE "It takes about ten minutes," then FULL kick "write it once" (boom on the payoff)
    s.face(tIt, tAnd8, zooms=[(tTen, 1.12)])
    h8a, a8 = s.head("Write it", 180, "left:90px;top:380px")
    h8b, b8 = s.head('<span class="mk">once.</span>', 260, "left:90px;top:620px")
    s.slam(f"#{h8a}", tWrite - 0.05); s.slam(f"#{h8b}", tOnce - 0.05, sfx="boom")
    s.kick(s.beat(tAnd8, tFollow, a8 + b8, nocap=True, full=True), tAnd8)

    # B9 · FACE CTA: zooms on "comment" and the word; the chip shows the word at y 1250, captions hidden under it
    s.face(tFollow, D, zooms=[(tComment, 1.1), (tWord, 1.18)])
    s.html.append(f'<div class="clip" id="cta" data-start="{tComment - 0.05:.3f}" data-duration="{D - tComment + 0.05:.3f}" data-track-index="7" '
                  'style="position:absolute;left:0;top:1250px;width:1080px;display:flex;justify-content:center;z-index:9">'
                  f'<div class="chip y" id="ctac" style="position:relative;font-size:56px">Comment {s.ghost or "NOTE"}</div></div>')
    s.pop("#ctac", tComment, sfx="sparkle"); s.nocap.append((tComment - 0.05, D))
