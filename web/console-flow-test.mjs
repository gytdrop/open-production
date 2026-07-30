import { chromium } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
const SHOTS = 'web/web/web/.tmp/console-after-run';
await mkdir(SHOTS, { recursive: true });
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push('PE: ' + e.message));
async function shot(name) { await page.screenshot({ path: SHOTS + '/' + name + '.png' }); }
await page.goto('http://127.0.0.1:5173/flow', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2000);
await page.locator('textarea').first().fill('A short film about a barista who discovers their regular customer is an AI testing whether humans can tell.');
await page.getByRole('button', { name: /Continue/ }).click();
await page.waitForTimeout(2500);
await page.locator('article').first().getByRole('button').click();
// Wait for pipeline run to advance stages
await page.waitForTimeout(20000);
await shot('after-finalize-on-stage7');
// Now click Agent Console to view live audit
await page.click('a:has-text("Agent Console")');
await page.waitForTimeout(5000);
await shot('console-after-finalize');
const auditCount = await page.locator('text=/.+/').filter({ hasText: /event|gate|accepted|review|decision|status|gate_decision/ }).count();
const entryHeads = await page.locator('text=/^.{1,40}$/').count();
console.log('errors:', errors.length);
for (const e of errors) console.log('  ERR:', e.slice(0, 200));
await browser.close();
