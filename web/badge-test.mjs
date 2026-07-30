import { chromium } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
const SHOTS = 'web/web/web/.tmp/screens-final';
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
  await page.locator('textarea').first().fill('A short film about a barista who discovers their regular customer is an AI testing whether humans can tell.');
  await page.getByRole('button', { name: /Continue/ }).click();
  await page.waitForTimeout(3500);
  // Now should be on Stage 3
  await page.screenshot({ path: SHOTS + '/' + label + '-stage3-angles.png' });
  const articles = await page.locator('article').count();
  const fitBadges = await page.locator('[title^="Reviewer fit score"]').count();
  console.log(label, 'articles:', articles, 'fit badges:', fitBadges);
  await ctx.close();
}
await run({ width: 1280, height: 900 }, 'desk');
await run({ width: 390, height: 800 }, 'mob');
await browser.close();
