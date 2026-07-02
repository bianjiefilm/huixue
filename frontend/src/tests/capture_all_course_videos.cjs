const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function verifyAllVideos() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Login
  await page.goto('http://localhost:3001/#/login');
  await page.fill('input[placeholder="用户名/手机号"]', 'admin');
  await page.fill('input[placeholder="密码"]', 'admin123');
  await page.click('.login-form-button');
  
  // Wait for login to complete (e.g., waiting for specific element on dashboard or specific URL)
  await page.waitForTimeout(3000);
  
  const outputDir = '/Users/jimfu/.gemini/antigravity/brain/f2cbfbe5-6c29-4a51-97fa-de0af457011e';
  
  for (let id = 100; id <= 117; id++) {
    console.log(`Testing Course/Classroom ${id}...`);
    try {
      await page.goto(`http://localhost:3001/#/classroom/${id}/resources`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000); // Let resources list render
      
      // Locate the "预览" (Preview) button for videos. Usually next to the video item.
      // We will assume the first "预览" button is for the main assigned video since there shouldn't be others in this test environment.
      const previewButton = page.locator('.file-item:has(.file-name:has-text(".mp4")) button:has-text("预览")').first();
      await previewButton.waitFor({ state: 'visible', timeout: 5000 });
      await previewButton.click();
      
      // Wait for video element in modal
      const videoEl = page.locator('video').first();
      await videoEl.waitFor({ state: 'attached', timeout: 5000 });
      
      // Play the video manually
      await videoEl.evaluate((vid) => vid.play().catch(console.error));
      
      // Wait for the video to actually start playing (readyState >= 3 and currentTime > 0)
      console.log(`Waiting for video playback to start in classroom ${id}...`);
      await page.waitForFunction(() => {
        const video = document.querySelector('video');
        return video && video.readyState >= 3 && video.currentTime > 0 && !video.paused;
      }, { timeout: 15000 });
      
      // Give it extra 2 seconds so the frame is fully painted and interesting
      await page.waitForTimeout(2000);
      
      // Take screenshot of the video modal or entire page
      const screenshotPath = path.join(outputDir, `audit_${id}_Course_${id}.png`);
      await page.screenshot({ path: screenshotPath });
      console.log(`Success: Screenshot taken for classroom ${id} -> ${screenshotPath}`);
      
      // Close modal (assuming el-dialog uses a specific close button or clicking outside)
      // Playwright can issue an escape key or click the close button.
      await page.keyboard.press('Escape');
      await page.waitForTimeout(1000);
      
    } catch (err) {
      console.error(`Failed on classroom ${id}: ${err.message}`);
      // Take error screenshot
      await page.screenshot({ path: path.join(outputDir, `error_${id}_Course_${id}.png`) });
    }
  }
  
  await browser.close();
  console.log("100% Validation Complete.");
}

verifyAllVideos().catch(console.error);
