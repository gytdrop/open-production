import { chromium } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
const SHOTS = 'web/.tmp/browser-test/screenshots';
await mkdir(SHOTS, { recursive: true });
const browser = await chromium.launch({ headless: true });
const msgs = [];
async function test(viewport, label) {
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  page.on('console', (m) => msgs.push({ vp: label, type: m.type(), text: m.text() }));
  page.on('pageerror', (e) => msgs.push({ vp: label, type: 'pageerror', text: e.message }));
  await page.goto('http://127.0.0.1:5173/flow', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: SHOTS + '/' + label + '-flow-1.png' });
  await ctx.close();
}
await test({ width: 390, height: 800 }, 'mobile');
await test({ width: 1280, height: 800 }, 'desktop');
await writeFile('web/.tmp/browser-test/msgs-2.json', JSON.stringify(msgs, null, 2));
await browser.close();
console.log('DONE');
