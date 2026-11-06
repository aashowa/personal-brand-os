// Export .excalidraw files to PNG with Excalidraw's own exporter in headless Chromium.
// Usage: node render.mjs <file.excalidraw> [more files...]  ->  writes <name>.png next to each input.
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const EXCALIDRAW = "https://esm.sh/@excalidraw/excalidraw@0.18.1";
const files = process.argv.slice(2);
if (!files.length) {
  console.error("Usage: node render.mjs <file.excalidraw> [more files...]");
  process.exit(1);
}

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync("npm root -g").toString().trim(), "playwright"));

const browser = await chromium.launch().catch(() => chromium.launch({ channel: "chrome" })); // fallback: the bundled build can lag the installed Playwright
const page = await browser.newPage();
page.on("pageerror", (e) => console.error("page error:", e.message));
await page.setContent("<!doctype html><html><body></body></html>");

for (const file of files) {
  const scene = JSON.parse(readFileSync(file, "utf8"));
  const b64 = await page.evaluate(async ({ url, scene }) => {
    const { exportToBlob } = await import(url);
    await document.fonts.ready; // exportToBlob also awaits the elements' fonts (Excalifont) before drawing
    const blob = await exportToBlob({
      elements: scene.elements,
      files: scene.files || {},
      appState: { ...scene.appState, exportBackground: true, exportWithDarkMode: false },
      exportPadding: 48,
      getDimensions: (w, h) => ({ width: w * 2, height: h * 2, scale: 2 }), // appState.exportScale is ignored here
      mimeType: "image/png",
    });
    const bytes = new Uint8Array(await blob.arrayBuffer());
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }, { url: EXCALIDRAW, scene });
  const out = file.replace(/\.excalidraw$/, "") + ".png";
  writeFileSync(out, Buffer.from(b64, "base64"));
  console.log("wrote", out);
}

await browser.close();
