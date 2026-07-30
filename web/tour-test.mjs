import { chromium } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
const SHOTS = 'web/web/.tmp/browser-test/screenshots';
await mkdir(SHOTS, { recursive: true });
const browser = await chromium.launch({ headless: true });
async function run(viewport, label) {
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push('PE: ' + e.message));
  await page.goto('http://127.0.0.1:5173/flow', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: SHOTS + '/' + label + '-1.png' });
  await page.locator('textarea').first().fill('A short film about a barista who discovers their regular customer is an AI.');
  await page.getByRole('button', { name: /Continue/ }).click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: SHOTS + '/' + label + '-2.png' });
  await page.getByRole('button', { name: /Continue to Find Your Angle/ }).click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: SHOTS + '/' + label + '-3.png' });
  await page.locator('article').first().getByRole('button').click();
  await page.waitForTimeout(12000);
  for (let i = 0; i < 7; i++) {
    await page.locator('[role=button][aria-label^="Step"]').nth(i).click();
    await page.waitForTimeout(700);
    await page.screenshot({ path: SHOTS + '/' + label + '-stage-' + (i + 1) + '.png' });
  }
  console.log(label, 'errors:', errors.length);
  for (const e of errors) console.log('  ', e.slice(0, 200));
  await ctx.close();
}
await run({ width: 1280, height: 900 }, 'desk');
await run({ width: 390, height: 800 }, 'mob');
await browser.close();
console.log('DONE');
