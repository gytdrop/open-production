import { chromium } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
const SHOTS = 'web/web/web/.tmp/screens';
await mkdir(SHOTS, { recursive: true });
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push('PE: ' + e.message));
async function shot(name) { await page.screenshot({ path: SHOTS + '/' + name + '.png' }); }

// Stage 1: empty
await page.goto('http://127.0.0.1:5173/flow', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2000);

// Stage 1: with topic
await page.locator('textarea').first().fill('A short film about a barista who discovers their regular customer is an AI testing whether humans can tell.');
await page.getByRole('button', { name: /Continue/ }).click();
await page.waitForTimeout(2500);
await shot('s1-after-continue');

// Click Continue to Find Your Angle
await page.getByRole('button', { name: /Continue to Find Your Angle/ }).click();
await page.waitForTimeout(1500);
await shot('s3-before-pick');

// Pick first angle
await page.locator('article').first().getByRole('button').click();
// Pipeline runs and steps 3-7 auto-advance
await page.waitForTimeout(15000);
await shot('s7-final');

// Hard navigate to each stage using the Zustand store directly via page evaluate
for (let n = 1; n <= 7; n++) {
  await page.evaluate((stepNum) => {
    // Hack: get the Zustand store from the window. First check if exposed.
    const events = document.querySelectorAll('[role=button][aria-label^="Step"]');
    // Direct approach: simulate clicks via keyboard arrows
  }, n);
  await page.keyboard.press('Escape');
  // Use footer Next if available
  if (n > 1) {
    await page.getByRole('button', { name: /^← Back$/ }).click();
    await page.waitForTimeout(500);
    await shot('s' + n + '-via-back');
  }
}

console.log('errors:', errors.length);
for (const e of errors) console.log('  ', e.slice(0, 200));
await browser.close();
