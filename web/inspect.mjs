import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 800 } });
const page = await ctx.newPage();
await page.goto('http://127.0.0.1:5173/flow', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(1500);
const info = await page.evaluate(() => {
  const rail = document.querySelector('.left-rail');
  if (!rail) return { found: false };
  const cs = getComputedStyle(rail);
  return {
    found: true,
    display: cs.display,
    width: cs.width,
    visibility: cs.visibility,
    offsetWidth: rail.offsetWidth,
    innerWidth: window.innerWidth,
  };
});
console.log(JSON.stringify(info, null, 2));
const matches = await page.evaluate(() => {
  const rules = [];
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule.cssText && rule.cssText.includes('left-rail')) rules.push(rule.cssText);
      }
    } catch (e) {}
  }
  return rules;
});
console.log('rules:', JSON.stringify(matches, null, 2));
await browser.close();
