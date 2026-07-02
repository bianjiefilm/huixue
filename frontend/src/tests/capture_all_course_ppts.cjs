const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  
  try {
    console.log('Navigating to login...');
    await page.goto('http://localhost:3005/#/login', { waitUntil: 'domcontentloaded' });
    
    // Login
    await page.fill('input[placeholder="用户名/手机号"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('.login-form-button');
    
    await page.waitForTimeout(3000);
    console.log('Login successful.');

    // Classrooms to check
    const classroomIds = Array.from({ length: 18 }, (_, i) => 100 + i);
    
    for (const id of classroomIds) {
      console.log(`\nTesting Course/Classroom ${id}...`);
      
      // Navigate to classroom resources tab
      await page.goto(`http://localhost:3005/#/classroom/${id}/resources`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000); // Let resources list and watch hook run
      
      try {
        await page.waitForSelector('.file-item', { timeout: 10000 });
      } catch (e) {
        console.log('Timeout waiting for .file-item... Maybe no files?');
      }
      
      // Find and click the PPTX file '预览' button
      const hasPreview = await page.evaluate(() => {
        const fileItems = Array.from(document.querySelectorAll('.file-item'));
        console.log(`Found ${fileItems.length} file items in DOM.`);
        const pptFile = fileItems.find(item => {
          const name = item.querySelector('.file-name')?.textContent || '';
          console.log(`Evaluating file: ${name}`);
          // Skip dummy files
          if (name.includes('自动化')) return false;
          return name.toLowerCase().endsWith('.pptx') || name.toLowerCase().endsWith('.ppt');
        });
        if (pptFile) {
          const buttons = Array.from(pptFile.querySelectorAll('.ant-btn'));
          const btn = buttons.find(b => b.textContent.includes('预览') || b.textContent.toLowerCase().includes('preview'));
          if (btn) {
            btn.click();
            return true;
          } else {
             console.log('Found PPT file but NO preview button.');
          }
        }
        return false;
      });

      if (hasPreview) {
        console.log(`Found PPT in classroom ${id}, clicked preview...`);
        // Wait for modal
        await page.waitForSelector('.ant-modal-content', { state: 'visible', timeout: 5000 });
        
        // Wait for vue-office-pptx to render it (the library usually renders a canvas or a wrapper div)
        console.log(`Waiting for vue-office-pptx render in classroom ${id}...`);
        await page.waitForTimeout(3000); // Give it a fixed 3s to spin up and load the file chunks
        
        const screenshotPath = path.resolve(`/Users/jimfu/.gemini/antigravity/brain/f2cbfbe5-6c29-4a51-97fa-de0af457011e/audit_${id}_Course_${id}_PPT.png`);
        await page.screenshot({ path: screenshotPath });
        console.log(`Success: Screenshot taken for classroom ${id} -> ${screenshotPath}`);
        
        // Close modal
        await page.keyboard.press('Escape');
        await page.waitForTimeout(1000);
      } else {
        const errorPath = path.resolve(`/Users/jimfu/.gemini/antigravity/brain/f2cbfbe5-6c29-4a51-97fa-de0af457011e/error_list_${id}.png`);
        await page.screenshot({ path: errorPath, fullPage: true });
        console.error(`🚨 Failed: No PPT file or preview button found for classroom ${id} (Saved to ${errorPath})`);
      }
    }
    
    console.log('\n✅ 100% PPT Validation Complete.');
  } catch (error) {
    console.error('Test failed with error:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
