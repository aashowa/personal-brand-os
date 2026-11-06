// Excalidraw diagrams for LinkedIn graphics: real Excalidraw (0.18.1, Excalifont), brand colours, portrait-friendly.
// Builds each scene, saves episodes/<WHERE[name]>/<name>.excalidraw (open at excalidraw.com to tweak) and exports <name>.png (2x).
//   node linkedin/creative/diagrams.mjs [name ...]     (default: all)
// New scene: add a function to `build` and its post folder (under episodes/) to WHERE. The two example scenes show the
// usual shapes: a numbered chain with a sticky note, and a two-column comparison.
// Style rules: brand-system/diagrams/README.md. Scenes are ~1000 units wide so 44-unit labels read at phone size.
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";

const EP = path.resolve(import.meta.dirname, "../../episodes");
const WHERE = {
  "example-steps": "_examples/linkedin",
  "example-compare": "_examples/linkedin",
};
const want = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(WHERE);

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync("npm root -g").toString().trim(), "playwright"));
const browser = await chromium.launch({ channel: "chrome" }); // the installed Chrome; no Playwright browser download needed
const page = await browser.newPage();
page.on("pageerror", (e) => console.error("page error:", e.message));
await page.setContent("<!doctype html><html><body></body></html>");

const out = await page.evaluate(async (want) => {
  const X = await import("https://esm.sh/@excalidraw/excalidraw@0.18.1");
  const C = { paper: "#F7F7F5", ink: "#111111", pencil: "#6B6B6B", white: "#FFFFFF", marker: "#FFD43B",
    restS: "#C4501B", restF: "#F6E3D8", agS: "#2251D1", agF: "#DDE5FA" };
  const R = { fill: C.restF, stroke: C.restS }, A = { fill: C.agF, stroke: C.agS }, Y = { fill: C.marker };
  const base = { strokeColor: C.ink, fillStyle: "solid", strokeWidth: 2, roughness: 1 };
  const conv = (s) => X.convertToExcalidrawElements(s, { regenerateIds: false });
  await X.exportToCanvas({ elements: conv([{ type: "text", x: 0, y: 0, fontFamily: 5, text: "Aa 0123456789 ·×%+,.?'" }]), appState: {}, files: {} });
  await document.fonts.ready;

  const LH = 1.25;
  let n = 0; const uid = (p) => `${p}-${++n}`;
  const measure = (text, size, align = "center", font = 5) => conv([{ type: "text", x: 0, y: 0, text, fontSize: size, fontFamily: font, strokeColor: C.ink, textAlign: align }])[0];
  const width = (text, size) => (text ? measure(text, size).width : 0);
  const tx = (text, size, cx, cy, color = C.ink, o = {}) => {
    const m = measure(text, size, o.align || "center", o.font || 5);
    return { ...m, id: uid("t"), x: o.align === "left" ? cx : cx - m.width / 2, y: cy - m.height / 2, strokeColor: color, angle: o.angle || 0 };
  };
  const hl = (t, sub, line = 0) => {
    const L = t.text.split("\n")[line], i = L.indexOf(sub);
    if (i < 0) throw new Error(`highlight "${sub}" not in "${L}"`);
    const lw = width(L, t.fontSize), lh = t.fontSize * LH;
    const lx = t.textAlign === "center" ? t.x + (t.width - lw) / 2 : t.x;
    return { ...conv([{ type: "rectangle", id: uid("hl"), x: lx + width(L.slice(0, i), t.fontSize) - 8, y: t.y + line * lh + lh * 0.42,
      width: width(sub, t.fontSize) + 16, height: lh * 0.5, ...base, strokeColor: "transparent", backgroundColor: C.marker, roundness: { type: 3 } }])[0], groupIds: t.groupIds || [] };
  };
  // box with centred label and optional pencil sub-label; o.hl = { on: "label"|"sub", text, line }
  const box = (x, y, w, h, o = {}) => {
    const { fill = C.white, stroke = C.ink, sw = 2, label, sub, size = 44, subSize = 32, shape = "rectangle", angle = 0, dashed, color = C.ink, subColor = C.pencil } = o;
    const id = uid("b"), g = [id + "-g"];
    const shp = { ...conv([{ type: shape, id, x, y, width: w, height: h, ...base, strokeWidth: sw, strokeColor: stroke, backgroundColor: fill,
      roundness: shape === "rectangle" ? { type: 3 } : { type: 2 }, angle, strokeStyle: dashed ? "dashed" : "solid" }])[0], groupIds: g };
    const els = [shp];
    if (label) {
      const a = measure(label, size), b = sub ? measure(sub, subSize) : null, gap = 8;
      const top = y + h / 2 - (a.height + (b ? gap + b.height : 0)) / 2;
      const ta = { ...a, id: id + "-t", x: x + w / 2 - a.width / 2, y: top, strokeColor: color, angle, groupIds: g };
      const tb = b && { ...b, id: id + "-s", x: x + w / 2 - b.width / 2, y: top + a.height + gap, strokeColor: subColor, angle, groupIds: g };
      if (o.hl) els.push(hl(o.hl.on === "sub" ? tb : ta, o.hl.text, o.hl.line || 0));
      els.push(ta); if (tb) els.push(tb);
    }
    els.shape = shp;
    return els;
  };
  const sticky = (x, y, w, h, label, o = {}) => box(x, y, w, h, { fill: C.marker, label, size: 38, angle: o.angle ?? -0.04, ...o });
  const center = (e) => [e.x + e.width / 2, e.y + e.height / 2];
  const edge = (e, dx, dy, gap = 12) => {
    const [cx, cy] = center(e), m = Math.hypot(dx, dy), t = Math.min(dx ? e.width / 2 / Math.abs(dx) : Infinity, dy ? e.height / 2 / Math.abs(dy) : Infinity);
    return [cx + dx * t + (dx / m) * gap, cy + dy * t + (dy / m) * gap];
  };
  const arrow = (pts, o = {}) => {
    const [x0, y0] = pts[0];
    return conv([{ type: "arrow", id: uid("a"), x: x0, y: y0, ...base, strokeWidth: o.sw || 2, strokeColor: o.color || C.ink, roundness: { type: 2 },
      points: pts.map(([x, y]) => [x - x0, y - y0]), startArrowhead: null, endArrowhead: o.head === false ? null : "arrow" }])[0];
  };
  const link = (a, b, o) => { a = a.shape || a; b = b.shape || b; const [ax, ay] = center(a), [bx, by] = center(b); return arrow([edge(a, bx - ax, by - ay), edge(b, ax - bx, ay - by)], o); };
  const line = (x, y, pts, o = {}) => conv([{ type: "line", id: uid("l"), x, y, points: pts, ...base, strokeColor: o.color || C.ink, strokeWidth: o.sw || 2,
    backgroundColor: o.fill || "transparent", roundness: o.round ? { type: 2 } : null }])[0];
  const check = (x, y, text, size = 40, done = false) => [
    conv([{ type: "rectangle", id: uid("c"), x, y: y - 24, width: 48, height: 48, ...base, backgroundColor: C.white, roundness: { type: 3 } }])[0],
    ...(done ? [line(x + 8, y - 2, [[0, 0], [14, 16], [36, -22]], { sw: 4 })] : []),
    tx(text, size, x + 76, y, C.ink, { align: "left" })];
  const doc = (x, y, w, h, o = {}) => { // page with a folded corner
    const f = 56;
    return [conv([{ type: "line", id: uid("d"), x, y, points: [[0, 0], [w - f, 0], [w, f], [w, h], [0, h], [0, 0]], ...base, backgroundColor: o.fill || C.white, roundness: null }])[0],
      line(x + w - f, y, [[0, 0], [0, f], [f, f]])];
  };
  const finish = (els) => X.serializeAsJSON(els.flat(), { viewBackgroundColor: C.paper, currentItemFontFamily: 5, currentItemRoughness: 1,
    currentItemStrokeWidth: 2, currentItemFillStyle: "solid" }, {}, "local");
  const col = (items, x, y, w, h, gap) => items.map((o, i) => box(x, y + i * (h + gap), w, h, o));
  const chain = (bs, o) => bs.slice(1).map((b, i) => link(bs[i], b, o));

  const build = {
    // a numbered chain with a sticky note: the shape most single-image posts use
    "example-steps"() {
      const s = col([{ shape: "ellipse", label: "Describe the job\nin plain words", size: 40 }, { label: "The AI plans it", sub: "and asks what's missing" },
        { label: "You approve", sub: "nothing runs before your yes" }, { ...Y, label: "It does the work", sub: "the same way every week", subColor: C.ink }], 0, 0, 600, 150, 70);
      return [...s, ...chain(s), sticky(640, 330, 340, 170, "you still check\nthe result", { size: 32, fill: C.restF, stroke: C.restS })];
    },
    // two columns side by side: before and after, or this versus that
    "example-compare"() {
      const left = col([{ label: "You paste it in", size: 40 }, { label: "It answers", size: 40 }, { label: "You do the work", size: 40, fill: C.restF, stroke: C.restS }], 0, 110, 440, 130, 60);
      const right = col([{ label: "Reads your files", size: 40 }, { label: "Uses your tools", size: 40 }, { label: "Does the job", size: 40, fill: C.marker }], 520, 110, 440, 130, 60);
      return [tx("Chatbot", 54, 220, 30), tx("Agent", 54, 740, 30), ...left, ...right, ...chain(left), ...chain(right),
        tx("you check it", 36, 740, 110 + 3 * 190 + 10, C.pencil), line(480, 0, [[0, 0], [0, 700]], { color: C.pencil })];
    },
  };
  const res = {};
  for (const k of want) {
    n = 0;
    const json = finish(build[k]());
    const scene = JSON.parse(json);
    const blob = await X.exportToBlob({ elements: scene.elements, files: {}, appState: { ...scene.appState, exportBackground: true, exportWithDarkMode: false },
      exportPadding: 40, getDimensions: (w, h) => ({ width: w * 2, height: h * 2, scale: 2 }), mimeType: "image/png" });
    const bytes = new Uint8Array(await blob.arrayBuffer());
    let s = ""; for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    res[k] = { json, png: btoa(s) };
  }
  return res;
}, want);

for (const [k, { json, png }] of Object.entries(out)) {
  const dir = path.join(EP, WHERE[k]);
  execSync(`mkdir -p "${dir}"`);
  writeFileSync(path.join(dir, `${k}.excalidraw`), json + "\n");
  writeFileSync(path.join(dir, `${k}.png`), Buffer.from(png, "base64"));
  console.log("wrote", path.join(WHERE[k], k + ".png"));
}
await browser.close();
