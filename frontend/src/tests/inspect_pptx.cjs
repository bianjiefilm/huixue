const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  
  await page.goto('http://127.0.0.1:3005/#/login');
  await page.fill('input[placeholder="用户名/手机号"]', 'admin');
  await page.fill('input[placeholder="密码"]', 'admin123');
  await page.click('.login-form-button');
  await page.waitForTimeout(3000);
  
  await page.goto('http://127.0.0.1:3005/#/classroom/101/resources');
  await page.waitForTimeout(2000);
  
  const files = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.file-name')).map(n => n.textContent);
  });
  console.log("FILES FOUND:", files);
  
  await browser.close();
})();
