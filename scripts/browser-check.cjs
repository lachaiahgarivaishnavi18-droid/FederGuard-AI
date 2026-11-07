const base = process.env.APP_URL || 'http://localhost:5173';
// Browser QA uses the locally installed runtime's Playwright module.
const fs=require('fs');
const path=require('path');
const playwright=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
  const browser=await playwright.chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
  const page=await browser.newPage({viewport:{width:1512,height:1100}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const env=Object.fromEntries(fs.readFileSync('.env','utf8').split(/\r?\n/).filter(l=>l.includes('=')).map(l=>[l.slice(0,l.indexOf('=')),l.slice(l.indexOf('=')+1)]));
  await page.goto(base + '/login');
  await page.getByLabel('Password',{exact:true}).fill(base.startsWith('https:') ? (env.CLOUD_DEMO_PASSWORD || env.DEMO_PASSWORD) : env.DEMO_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('heading',{name:'A clearer view. A stronger defense.'}).waitFor();
  await page.waitForTimeout(1200);
  fs.mkdirSync('docs/screenshots',{recursive:true});
  await page.screenshot({path:'docs/screenshots/dashboard.png',fullPage:true});
  for(const route of ['banks','federated','privacy','fraud','intelligence','knowledge','assistant','graph','investigations','agents','analytics','settings']){
    await page.goto(base + '/'+route);await page.locator('.content h1').waitFor();await page.waitForTimeout(250);
    if(await page.locator('body').evaluate(e=>e.scrollWidth>window.innerWidth+2))throw Error('Overflow on '+route);
  }
  await page.goto(base + '/assistant');
  await page.getByRole('button',{name:'Retrieve & explain'}).click();
  await page.getByText('Local evidence summary (extractive demo):',{exact:false}).waitFor();
  await page.goto(base + '/fraud');
  await page.getByRole('button',{name:'Assess local risk'}).click();
  await page.getByRole('heading',{name:'Model assessment',exact:true}).waitFor();
  await page.getByRole('button',{name:'Create investigation',exact:true}).click();
  await page.goto(base + '/investigations');
  await page.getByLabel('Case title',{exact:true}).fill('Browser verified synthetic case');
  await page.getByRole('button',{name:'Create case',exact:true}).click();
  await page.getByRole('button',{name:/Browser verified synthetic case/}).waitFor();
  await page.setViewportSize({width:390,height:844});await page.goto(base + '/dashboard');
  await page.getByRole('heading',{name:'A clearer view. A stronger defense.'}).waitFor();
  await page.screenshot({path:'docs/screenshots/mobile.png',fullPage:true});
  if(await page.locator('body').evaluate(e=>e.scrollWidth>window.innerWidth+2))throw Error('Mobile overflow');
  await browser.close();
  if(errors.length)throw Error(errors.join('\n'));
  console.log('PASS: 13 routes, grounded answer, local scoring, case creation, desktop/mobile layout; no browser errors.');
})().catch(e=>{console.error(e);process.exit(1)});
