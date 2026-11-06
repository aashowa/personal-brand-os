#!/usr/bin/env python3
"""Shorts kit: a beat spec (<shorts>/_build/<name>.py) -> a HyperFrames project (<shorts>/<name>/index.html + assets).

Layout 1080x1920: top half 0-960 = paper + grid with motion graphics, real footage cards (crops of the privacy-blurred
1x export), real logos and photos; bottom half 960-1920 = graded camera; captions as a yellow chip on the seam.
Times in specs are FINAL seconds (after the speed-up). s.T(word, after) finds a word's start in assets/words.json.
A spec is a module with make(s): it calls the block helpers below and s.beat(...) once per top-half beat.
Built by: shorts.py build SHORTS.json NAME
"""
import html, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = str(Path(__file__).resolve().parents[3])   # repo root (resolve follows the skills symlink)
ASSETS = os.path.join(os.path.dirname(KIT), "assets")
SFX_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(KIT)), "palmier-hyperframes-video", "scripts")   # sfx.py
TOP, W = 960, 1080
WIDE = (48, 236, 984, 554)          # x, y, w, h  (16:9 card)
SQUARE = (105, 110, 870, 768)        # aspect 1.133 card
# Whisper often hears "Claude" as "cloud" and ChatGPT as "chatgbt"; an episode adds or overrides fixes in
# shorts.json "caption_fixes": {"words": {...}, "phrases": [[heard, shown], ...]} (phrases merge several words).
FIX = {"chatgbt": "ChatGPT", "chatgbt,": "ChatGPT,", "cloud": "Claude", "cloud,": "Claude,", "Cloud": "Claude", "Cloud,": "Claude,"}


def esc(s): return html.escape(s, quote=True)


def output_dir(base):
    """Where deliver files the Shorts: config.json episode_shorts.output_dir ("<slug>" = the episode folder name,
    relative paths are from the repo root), default episodes/<slug>/shorts/."""
    p = os.path.join(ROOT, "config.json"); conf = json.load(open(p)) if os.path.exists(p) else {}
    out = conf.get("episode_shorts", {}).get("output_dir") or "episodes/<slug>/shorts/"
    out = os.path.expanduser(out.replace("<slug>", os.path.basename(os.path.dirname(base))))
    return os.path.normpath(os.path.join(ROOT, out))


def load(path):
    """shorts.json with paths resolved against its own folder (absolute and ~ paths kept)."""
    path = os.path.abspath(os.path.expanduser(path)); base = os.path.dirname(path); cfg = json.load(open(path))
    for k in ("timeline", "words", "voice", "camera", "repaired", "lut", "export", "terms", "output_dir"):
        if cfg.get(k): cfg[k] = os.path.normpath(os.path.join(base, os.path.expanduser(cfg[k])))
    cfg["output_dir"] = cfg.get("output_dir") or output_dir(base)   # shorts.json "output_dir" overrides config.json
    if cfg.get("longform", {}).get("file"):
        cfg["longform"]["file"] = os.path.normpath(os.path.join(base, os.path.expanduser(cfg["longform"]["file"])))
    cfg.setdefault("speed", 1.1); cfg.setdefault("fps", 30); cfg["dir"] = base
    return cfg


class Short:
    def __init__(self, cfg, name):
        self.cfg, self.name, self.dir = cfg, name, os.path.join(cfg["dir"], name)
        d = json.load(open(f"{self.dir}/assets/words.json"))
        self.D, self.words = d["duration"], d["words"]
        sh = cfg["shorts"][name]
        self.ghost, self.edl, self.speed = sh.get("ghost", ""), sh["edl"], cfg["speed"]
        fx = cfg.get("caption_fixes", {})
        self.fix, self.phrases = {**FIX, **fx.get("words", {})}, [tuple(p) for p in fx.get("phrases", [])]
        self.html, self.js, self.sfx, self.nocap, self.punch, self.footage, self.full = [], [], [], [], [], [], []
        self.n = 0

    def v5(self, t, end=False):
        """Final time -> long-form 1x time through the EDL. A start just before a cut belongs to the next piece;
        an end just after a cut belongs to the previous one (footage must not span a cut)."""
        o = t * self.speed
        for i, (a, b) in enumerate(self.edl):
            n = b - a; last = i == len(self.edl) - 1
            if last or (o <= n + 0.06 if end else o < n - 0.06): return a + max(0.0, min(o, n))
            o -= n
        return self.edl[-1][1]

    def sync(self, t0, t1):
        """Long-form range showing exactly what was on screen while these words were said."""
        return (self.v5(t0), self.v5(t1, end=True))

    # ---------- time helpers
    def T(self, word, after=0.0):
        key = re.sub(r"[^\w$.']", "", word.lower())
        for s, e, t in self.words:
            if s >= after - 1e-6 and re.sub(r"[^\w$.']", "", t.lower()).strip(".") == key.strip("."):
                return s
        raise KeyError(f"{self.name}: no word {word!r} after {after}")

    def uid(self, p="e"):
        self.n += 1; return f"{p}{self.n}"

    # ---------- motion vocabulary (fromTo only; seek-safe)
    def pop(self, sel, t, dur=0.45, sfx="pop"):
        self.js.append(f"tl.fromTo('{sel}',{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:{dur},ease:'power3.out'}},{t:.3f});")
        if sfx: self.sfx.append((t, sfx))

    def slam(self, sel, t, sfx="whoosh-short"):
        self.js.append(f"tl.fromTo('{sel}',{{scale:1.55,opacity:0,filter:'blur(14px)'}},{{scale:1,opacity:1,filter:'blur(0px)',duration:0.42,ease:'power4.out'}},{t:.3f});")
        if sfx: self.sfx.append((t, sfx))

    def snap(self, sel, t, x=-320, sfx="whoosh-short"):
        self.js.append(f"tl.fromTo('{sel}',{{x:{x},opacity:0}},{{x:0,opacity:1,duration:0.4,ease:'expo.out'}},{t:.3f});")
        if sfx: self.sfx.append((t, sfx))

    def rise(self, sel, t, sfx=None):
        self.js.append(f"tl.fromTo('{sel}',{{y:90,rotation:5,opacity:0}},{{y:0,rotation:0,opacity:1,duration:0.5,ease:'circ.out'}},{t:.3f});")
        if sfx: self.sfx.append((t, sfx))

    def card_in(self, sels, t, sfx="whoosh-short"):
        s = ",".join(f"'{x}'" for x in sels)
        self.js.append(f"tl.fromTo([{s}],{{y:80,rotation:-2.5,scale:0.93,opacity:0}},{{y:0,rotation:0,scale:1,opacity:1,duration:0.45,ease:'expo.out'}},{t:.3f});")
        if sfx: self.sfx.append((t, sfx))

    def push(self, sel, t0, t1, s=1.07):
        self.js.append(f"tl.fromTo('{sel}',{{scale:1}},{{scale:{s},duration:{t1 - t0:.3f},ease:'none'}},{t0:.3f});")

    def draw(self, sel, t, dur=0.4, sfx=None):            # scaleX 0 -> 1 from the left (marker, strike, arrow)
        self.js.append(f"tl.fromTo('{sel}',{{scaleX:0}},{{scaleX:1,duration:{dur},ease:'power2.out'}},{t:.3f});")
        if sfx: self.sfx.append((t, sfx))

    def fade_out(self, sel, t, dur=0.25):
        self.js.append(f"tl.fromTo('{sel}',{{opacity:1}},{{opacity:0,duration:{dur},ease:'power1.in',immediateRender:false}},{t:.3f});")

    def bob(self, sel, t0, t1, amp=8, cyc=1.6):
        n = max(0, int((t1 - t0) // cyc) * 2 - 1)
        self.js.append(f"tl.fromTo('{sel}',{{y:0}},{{y:-{amp},duration:{cyc / 2},ease:'sine.inOut',yoyo:true,repeat:{n},immediateRender:false}},{t0:.3f});")

    def wipe_full(self, t):
        self.js.append(f"tl.fromTo('#wipeF',{{x:-1080}},{{x:0,duration:0.16,ease:'power2.in',immediateRender:false}},{t - 0.16:.3f});")
        self.js.append(f"tl.fromTo('#wipeF',{{x:0}},{{x:1080,duration:0.2,ease:'power2.out',immediateRender:false}},{t:.3f});")
        self.sfx.append((t - 0.12, "whoosh"))

    def wipe(self, t):
        self.js.append(f"tl.fromTo('#wipe',{{x:-1080}},{{x:0,duration:0.16,ease:'power2.in',immediateRender:false}},{t - 0.16:.3f});")
        self.js.append(f"tl.fromTo('#wipe',{{x:0}},{{x:1080,duration:0.2,ease:'power2.out',immediateRender:false}},{t:.3f});")
        self.sfx.append((t - 0.12, "whoosh"))

    def typing(self, sel, text, t0, t1, cursor=True):
        """Deterministic typing: one driver tween; onUpdate writes the prefix (counting-dynamic-scale pattern)."""
        v = self.uid("ty")
        self.js.append(f"const {v}={{n:0}};const {v}el=document.querySelector('{sel}');"
                       f"tl.fromTo({v},{{n:0}},{{n:{len(text)},duration:{t1 - t0:.3f},ease:'none',onUpdate:()=>{{{v}el.textContent={json.dumps(text)}.slice(0,Math.round({v}.n));}}}},{t0:.3f});")
        self.sfx.append((t0, "typing", t1))

    def count(self, sel, t0, t1, a, b, fmt="int"):
        v = self.uid("ct"); f = "Math.round(%s.v)" % v if fmt == "int" else "%s.v.toFixed(2)" % v
        self.js.append(f"const {v}={{v:{a}}};const {v}el=document.querySelector('{sel}');"
                       f"tl.fromTo({v},{{v:{a}}},{{v:{b},duration:{t1 - t0:.3f},ease:'power2.out',onUpdate:()=>{{{v}el.textContent={f};}}}},{t0:.3f});")

    # ---------- building blocks (HTML strings)
    def beat(self, t0, t1, inner, nocap=False, full=False):
        """full=True: the graphic takes the whole 1080x1920 frame (a kick; also hides repaired camera frames)."""
        bid = self.uid("b")
        if full:
            inner = f'<div class="fullbg"><div class="fgrid" id="{bid}g"></div></div>' + inner; self.full.append((t0, t1))
            self.js.append(f"tl.fromTo('#{bid}g',{{backgroundPosition:'0px 0px'}},{{backgroundPosition:'0px -120px',duration:{t1 - t0:.3f},ease:'none'}},{t0:.3f});")
        self.html.append(f'<section id="{bid}" class="clip beat{" full" if full else ""}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{5 if full else 3}">{inner}</section>')
        if nocap: self.nocap.append((t0, t1))
        return bid

    def foot(self, t0, t1, v5, rect, mode="wide", label=None, push=1.06, enter=True):
        """Real footage card: crop of the 1x export [v5a, v5b] (normalised x0, y0, w), stretched to fill [t0, t1]."""
        x, y, w, h = WIDE if mode == "wide" else SQUARE
        fid = self.uid("f"); src = f"assets/{fid}.mp4"
        self.footage.append({"id": fid, "v5": v5, "rect": rect, "mode": mode, "size": (w, h), "dur": t1 - t0})
        self.html.append(f'<div class="fwrap" data-layout-allow-overflow id="{fid}w" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"><div class="fzoom" id="{fid}z">'
                         f'<video id="{fid}" class="clip" src="{src}" muted playsinline data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="1"></video></div></div>')
        frame = f'<div class="frame" id="{fid}fr" style="left:{x - 6}px;top:{y - 6}px;width:{w + 12}px;height:{h + 12}px"></div>'
        if label: frame += f'<div class="chip y lab" id="{fid}lab" style="left:{x + 22}px;top:{y - 30}px">{esc(label)}</div>'
        if enter: self.card_in([f"#{fid}w", f"#{fid}fr"], t0)
        if push: self.push(f"#{fid}z", t0, t1, push)
        if label: self.snap(f"#{fid}lab", t0 + 0.2, -120, sfx=None)
        return fid, frame, (x, y, w, h)

    def logo(self, name, size=180, label=None, style=""):
        lid = self.uid("lg"); lab = f'<div class="lglab">{esc(label)}</div>' if label else ""
        return lid, (f'<div class="logo" data-layout-allow-overflow id="{lid}" style="width:{size}px;height:{size}px;{style}">'
                     f'<img src="assets/logos/{name}" alt="" style="width:{int(size * 0.62)}px;height:{int(size * 0.62)}px">{lab}</div>')

    def chip(self, text, kind="", style=""):
        cid = self.uid("c")
        return cid, f'<div class="chip {kind}" id="{cid}" style="{style}">{esc(text)}</div>'

    def head(self, text_html, size=120, style=""):
        hid = self.uid("h")
        return hid, f'<div class="head" id="{hid}" style="font-size:{size}px;{style}">{text_html}</div>'

    def photo(self, name, rect=SQUARE, style=""):
        x, y, w, h = rect; pid = self.uid("p")
        return pid, (f'<div class="pcard" data-layout-allow-overflow id="{pid}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{style}">'
                     f'<img id="{pid}i" src="assets/photos/{name}" alt=""></div>')

    def cam_punch(self, t0, t1, s=1.12):
        self.punch.append((t0, t1, s))

    # ---------- captions
    def captions(self):
        ws = [[s, e, t] for s, e, t in self.words]
        for a, b in self.phrases:                               # merge mis-heard phrases into one word span
            n = len(a.split())
            for i in range(len(ws) - n + 1):
                if " ".join(w[2] for w in ws[i:i + n]) == a:
                    ws[i:i + n] = [[ws[i][0], ws[i + n - 1][1], b]]; break
        for w in ws: w[2] = self.fix.get(w[2], w[2])
        for i in range(len(ws) - 1):                             # "Claude code" -> "Claude Code"
            if ws[i][2] == "Claude" and ws[i + 1][2].lower().startswith("code"): ws[i + 1][2] = "Code" + ws[i + 1][2][4:]
        groups, cur = [], []
        for i, w in enumerate(ws):                               # 1-3 words, <= 20 characters, broken at punctuation and pauses
            cur.append(w)
            nxt = ws[i + 1] if i + 1 < len(ws) else None
            text = " ".join(x[2] for x in cur)
            if (not nxt or re.search(r"[.,?!]$", w[2]) or len(cur) >= 3 or len(text) >= 16
                    or (nxt and nxt[0] - w[1] > 0.3) or (nxt and len(text) + 1 + len(nxt[2]) > 20)):
                groups.append(cur); cur = []
        out = []
        for i, g in enumerate(groups):
            a = g[0][0]; b = groups[i + 1][0][0] if i + 1 < len(groups) else min(self.D, g[-1][1] + 0.4)
            b = min(b, g[-1][1] + 0.6)
            if any(x0 - 0.05 <= a < x1 for x0, x1 in self.nocap): continue
            nxt = groups[i + 1][0][0] if i + 1 < len(groups) else self.D
            out.append((a, min(max(b, a + 0.3), nxt), " ".join(x[2] for x in g).rstrip(",")))
        return out

    # ---------- assembly
    def build(self):
        D = self.D; os.makedirs(f"{self.dir}/assets/logos", exist_ok=True); os.makedirs(f"{self.dir}/assets/photos", exist_ok=True)
        shutil.copytree(f"{ASSETS}/fonts", f"{self.dir}/assets/fonts", dirs_exist_ok=True)
        used = " ".join(self.html)
        for src in (f"{ASSETS}/logos", f"{self.cfg['dir']}/logos"):        # episode logos override the kit's
            for f in (os.listdir(src) if os.path.isdir(src) else []):
                if f"assets/logos/{f}" in used: shutil.copy(f"{src}/{f}", f"{self.dir}/assets/logos/{f}")
        ph = f"{self.cfg['dir']}/photos"
        for f in (os.listdir(ph) if os.path.isdir(ph) else []):
            if f"assets/photos/{f}" in used: shutil.copy(f"{ph}/{f}", f"{self.dir}/assets/photos/{f}")
        missing = sorted(p for p in set(re.findall(r'src="(assets/(?:logos|photos)/[^"]+)"', used)) if not os.path.exists(f"{self.dir}/{p}"))
        if missing: raise FileNotFoundError(f"{self.name}: missing {missing} (add photos with: shorts.py photos get)")
        caps = self.captions(); cap_html = []
        for i, (a, b, t) in enumerate(caps):
            low = " low" if any(x0 - 0.01 <= a < x1 for x0, x1 in self.full) else ""
            cap_html.append(f'<div class="clip cap{low}" id="capw{i}" data-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="6"><div class="tilt"><div class="cchip" id="cap{i}">{esc(t)}</div></div></div>')
            self.js.append(f"tl.fromTo('#cap{i}',{{scale:0.7,opacity:0}},{{scale:1,opacity:1,duration:0.14,ease:'power3.out'}},{a:.3f});")
        for t0, t1, s in self.punch:
            self.js.append(f"tl.fromTo('#camz',{{scale:1}},{{scale:{s},duration:0.08,ease:'power2.out',immediateRender:false}},{t0:.3f});")
            self.js.append(f"tl.fromTo('#camz',{{scale:{s}}},{{scale:1,duration:0.12,ease:'power2.inOut',immediateRender:false}},{t1:.3f});")
        page = TEMPLATE.format(D=f"{D:.3f}", ghost=esc(self.ghost), beats="\n".join(self.html), caps="\n".join(cap_html),
                               js="\n".join(self.js))
        open(f"{self.dir}/index.html", "w").write(page)
        json.dump({"footage": self.footage, "sfx": self.sfx, "captions": caps}, open(f"{self.dir}/build.json", "w"), indent=1)
        return caps

    def cut_footage(self, only_missing=True):
        ex = self.cfg["export"]; fps = self.cfg["fps"]
        if any(not os.path.exists(f"{self.dir}/assets/{f['id']}.mp4") for f in self.footage) or not only_missing:
            EW, EH = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                              "-of", "csv=p=0", ex], capture_output=True, text=True, check=True).stdout.strip().split(","))
        for f in self.footage:
            out = f"{self.dir}/assets/{f['id']}.mp4"
            if only_missing and os.path.exists(out): continue
            (a, b), (x0, y0, w), (ow, oh) = f["v5"], f["rect"], f["size"]
            pw = round(w * EW / 2) * 2; ph = round(pw * oh / ow / 2) * 2
            px, py = round(x0 * EW / 2) * 2, round(y0 * EH / 2) * 2
            px, py = min(px, EW - pw), min(py, EH - ph)               # keep the crop inside the frame
            assert px >= 0 and py >= 0, (f, px, py, pw, ph)
            k = f["dur"] / (b - a)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", ex, "-t", f"{b - a:.3f}", "-an",
                            "-vf", f"crop={pw}:{ph}:{px}:{py},scale={ow}:{oh}:flags=lanczos,setpts=PTS*{k:.5f},fps={fps}",
                            "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-pix_fmt", "yuv420p", "-g", str(fps), "-bf", "0",
                            "-movflags", "+faststart", out], check=True)

    def mix_sfx(self, peak=-24):
        sys.path.insert(0, SFX_SCRIPTS); import sfx as S, numpy as np
        fps = self.cfg["fps"]
        hits = [(int(round(h[0] * fps)), h[1], int(round(h[2] * fps)) if len(h) > 2 else None) for h in self.sfx]
        y = S.mix(hits, fps, peak); n = int((self.D + 0.5) * S.SR); y = np.pad(y, ((0, max(0, n - len(y))), (0, 0)))[:n]
        raw = f"{self.dir}/assets/sfx.f32"; y.astype(np.float32).tofile(raw)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(S.SR), "-ac", "2", "-i", raw, "-c:a", "pcm_s16le", f"{self.dir}/assets/sfx.wav"], check=True)
        os.remove(raw)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face{{font-family:"Bricolage Grotesque";src:url("assets/fonts/bricolage-grotesque-latin-800-normal.woff2") format("woff2");font-weight:800}}
@font-face{{font-family:"Bricolage Grotesque";src:url("assets/fonts/bricolage-grotesque-latin-500-normal.woff2") format("woff2");font-weight:500}}
@font-face{{font-family:"JetBrains Mono";src:url("assets/fonts/jetbrains-mono-latin-700-normal.woff2") format("woff2");font-weight:700}}
@font-face{{font-family:"JetBrains Mono";src:url("assets/fonts/jetbrains-mono-latin-500-normal.woff2") format("woff2");font-weight:500}}
:root{{--paper:#F7F7F5;--ink:#141412;--pencil:#5E5E58;--marker:#FFD43B;--line:#DCDCD6;--agency:#2251D1;--rest:#C4501B}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:var(--ink)}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:"Bricolage Grotesque",sans-serif;color:var(--ink)}}
#top{{position:absolute;left:0;top:0;width:1080px;height:960px;overflow:hidden;background:var(--paper)}}
#grid{{position:absolute;inset:0;background-image:linear-gradient(var(--line) 2px,transparent 2px),linear-gradient(90deg,var(--line) 2px,transparent 2px);background-size:60px 60px}}
#ghost{{position:absolute;left:-20px;bottom:30px;font-weight:800;font-size:260px;letter-spacing:-.05em;line-height:1;color:var(--ink);opacity:.1;white-space:nowrap}}
.beat{{position:absolute;left:0;top:0;width:1080px;height:960px;overflow:hidden}}
.fwrap{{position:absolute;overflow:hidden;border-radius:22px;background:var(--paper)}}
.fzoom{{width:100%;height:100%}}
.fzoom video{{width:100%;height:100%;object-fit:cover;display:block}}
.frame{{position:absolute;border:6px solid var(--ink);border-radius:28px;box-shadow:0 14px 0 var(--ink)}}
.chip{{position:absolute;display:inline-block;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:30px;letter-spacing:.1em;text-transform:uppercase;padding:12px 22px;border-radius:12px;background:var(--ink);color:var(--paper);white-space:nowrap;border:4px solid var(--ink)}}
.chip.y{{background:var(--marker);color:var(--ink)}}
.chip.b{{background:var(--agency);color:#fff;border-color:var(--agency)}}
.chip.r{{background:var(--rest);color:#fff;border-color:var(--rest)}}
.chip.w{{background:#fff;color:var(--ink)}}
.head{{position:absolute;font-weight:800;line-height:.95;letter-spacing:-.045em;color:var(--ink)}}
.mk{{background:linear-gradient(transparent 56%,var(--marker) 56%);padding:0 .06em}}
.logo{{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#fff;border:5px solid var(--ink);border-radius:34px;box-shadow:0 12px 0 var(--ink)}}
.logo img{{object-fit:contain;display:block}}
.lglab{{position:absolute;bottom:-58px;left:50%;width:360px;margin-left:-180px;text-align:center;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:26px;letter-spacing:.08em;text-transform:uppercase}}
.pcard{{position:absolute;overflow:hidden;border:6px solid var(--ink);border-radius:28px;box-shadow:0 14px 0 var(--ink);background:#ddd}}
.pcard img{{width:100%;height:100%;object-fit:cover;display:block}}
.bar{{position:absolute;display:block;background:var(--marker);transform-origin:0 50%}}
.strike{{position:absolute;display:block;height:24px;background:var(--rest);border-radius:6px;transform-origin:0 50%}}
.bubble{{position:absolute;font-weight:500;font-size:44px;line-height:1.15;padding:26px 34px;border-radius:30px;border:5px solid var(--ink);background:#fff;box-shadow:0 10px 0 var(--ink)}}
.bubble.me{{background:var(--ink);color:var(--paper)}}
.row{{position:absolute;display:flex;align-items:center;gap:22px;font-weight:800;font-size:58px;letter-spacing:-.03em}}
.tick{{display:flex;align-items:center;justify-content:center;width:74px;height:74px;border-radius:50%;background:var(--ink);color:var(--marker);font-size:46px;font-weight:800;flex:none}}
.cross{{display:flex;align-items:center;justify-content:center;width:74px;height:74px;border-radius:50%;background:var(--rest);color:#fff;font-size:46px;font-weight:800;flex:none}}
.mono{{font-family:"JetBrains Mono",monospace;font-weight:700}}
#wipe,#wipeF{{position:absolute;left:0;top:0;width:1080px;height:960px;background:var(--marker);border-right:14px solid var(--ink);z-index:6}}
#wipeF{{height:1920px}}
#top{{z-index:0}} .fwrap{{z-index:1}} .beat{{z-index:2}} .beat.full{{height:1920px;z-index:5}}
.fullbg{{position:absolute;inset:0;background:var(--paper);overflow:hidden}}
.fgrid{{position:absolute;inset:0;background-image:linear-gradient(var(--line) 2px,transparent 2px),linear-gradient(90deg,var(--line) 2px,transparent 2px);background-size:60px 60px}}
.cap.low{{top:1260px}}  /* chip ~1290-1350: clear of Instagram's caption area below 1440 */
#cam{{position:absolute;left:0;top:960px;width:1080px;height:960px;overflow:hidden;background:#222;z-index:3}}
#camz{{width:100%;height:100%;transform-origin:50% 38%}}
#camz video{{width:100%;height:100%;object-fit:cover;display:block}}
#seam{{position:absolute;left:0;top:954px;width:1080px;height:12px;background:var(--ink);z-index:4}}
.cap{{position:absolute;left:0;top:900px;width:1080px;height:120px;display:flex;align-items:center;justify-content:center;z-index:8}}
.tilt{{transform:rotate(-2deg)}}
.cchip{{font-weight:800;font-size:64px;letter-spacing:-.02em;line-height:1;white-space:nowrap;background:var(--marker);color:var(--ink);border:5px solid var(--ink);border-radius:18px;padding:16px 30px;box-shadow:0 12px 0 var(--ink)}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{D}" data-width="1080" data-height="1920">
<div id="top"><div id="grid"></div><div id="ghost" data-layout-allow-occlusion data-layout-allow-overflow>{ghost}</div></div>
{beats}
<div id="wipe" data-layout-allow-overflow></div><div id="wipeF" data-layout-allow-overflow></div>
<div id="cam"><div id="camz"><video id="camv" class="clip" src="assets/camera.mp4" muted playsinline data-start="0" data-duration="{D}" data-track-index="0"></video></div></div>
<div id="seam"></div>
{caps}
<audio id="voice" src="assets/voice.wav" data-start="0" data-duration="{D}" data-track-index="8" data-volume="1"></audio>
<audio id="sfx" src="assets/sfx.wav" data-start="0" data-duration="{D}" data-track-index="9" data-volume="1"></audio>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
gsap.set(['#wipe','#wipeF'],{{x:-1080}});
tl.fromTo('#grid',{{backgroundPosition:'0px 0px'}},{{backgroundPosition:'0px -240px',duration:{D},ease:'none'}},0);
tl.fromTo('#ghost',{{x:0}},{{x:-260,duration:{D},ease:'none'}},0);
{js}
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""


def build(cfg, name):
    """Run <shorts>/_build/<name>.py make(s) -> index.html, footage clips, sfx.wav. Prints a one-line summary."""
    spec = os.path.join(cfg["dir"], "_build", f"{name}.py")
    sys.path.insert(0, KIT)
    m = importlib.util.spec_from_file_location(f"spec_{name.replace('-', '_')}", spec); mod = importlib.util.module_from_spec(m); m.loader.exec_module(mod)
    s = Short(cfg, name); mod.make(s)
    caps = s.build(); s.cut_footage(); s.mix_sfx()
    keep = {f"{f['id']}.mp4" for f in s.footage}
    for f in os.listdir(f"{s.dir}/assets"):
        if re.fullmatch(r"f\d+\.mp4", f) and f not in keep: os.remove(f"{s.dir}/assets/{f}")
    print(s.name, "duration", s.D, "beats", sum(1 for h in s.html if h.startswith("<section")), "footage", len(s.footage),
          "captions", len(caps), "full-screen", [(round(a, 2), round(b, 2)) for a, b in s.full], "sfx", len(s.sfx))
    return s
