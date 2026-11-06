// Renders the templates to PNG in out/. Usage: node render.mjs [thumbnail banner ig-cover]
import { createRequire } from 'module';
import { execSync } from 'child_process';
import { mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require(execSync('npm root -g').toString().trim() + '/playwright');
const SIZES = { thumbnail: [1280, 720], banner: [2560, 1440], 'ig-cover': [1080, 1920], 'x-article-cover': [1500, 600] };
const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(SIZES);
const here = new URL('.', import.meta.url);
mkdirSync(new URL('out/', here), { recursive: true });
const browser = await chromium.launch();
for (const name of names) {
  const [width, height] = SIZES[name];
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(new URL(`${name}.html`, here).href);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: fileURLToPath(new URL(`out/${name}.png`, here)) });
  console.log(`out/${name}.png`);
  await page.close();
}
await browser.close();
