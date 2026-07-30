import { chromium } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
const SHOTS = 'web/.tmp/browser-test/screenshots';
await mkdir(SHOTS, { recursive: true });
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const messages = [];
page.on('console', (m) => {
  if (m.type() === 'error' || m.type() === 'warning' || m.type() === 'warn') {
    messages.push({ type: m.type(), text: m.text() });
  }
});
page.on('pageerror', (e) => messages.push({ type: 'pageerror', text: e.message }));
await page.goto('http://127.0.0.1:5173/flow', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2000);
await page.locator('textarea').first().fill('A short film about a barista who discovers their regular customer is an AI.');
await page.getByRole('button', { name: /Continue/ }).click();
await page.waitForTimeout(2500);
await page.locator('[role=button][aria-label^="Step"]').nth(2).click();
await page.waitForTimeout(500);
await page.goto('http://127.0.0.1:5173/console?id=stale', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2500);
await writeFile('web/.tmp/browser-test/warnings.json', JSON.stringify(messages, null, 2));
console.log('messages:', messages.length);
for (const m of messages) {
  console.log('  [' + m.type + ']', m.text.slice(0, 200));
}
await browser.close();
