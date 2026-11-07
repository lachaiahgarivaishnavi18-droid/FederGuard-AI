const base = process.env.APP_URL || 'http://localhost:5173';
const fs = require('fs');
const crypto = require('crypto');
const playwright = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const env = Object.fromEntries(fs.readFileSync('.env', 'utf8').split(/\r?\n/).filter(l => l.includes('=')).map(l => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
  const browser = await playwright.chromium.launch({ headless: true, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/login');
    await page.getByRole('link', { name: 'Create account', exact: true }).click();
    await page.getByRole('heading', { name: 'Create your account', exact: true }).waitFor();
    if (await page.locator('form input').count() !== 2) throw Error('Signup must contain only email and password');
    fs.mkdirSync('docs/screenshots', { recursive: true });
    await page.screenshot({ path: 'docs/screenshots/create-account.png', fullPage: true });
    const email = `signup-check-${Date.now()}@federguard.demo`;
    const password = crypto.randomBytes(20).toString('hex');
    await page.getByLabel('Email address', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill('short');
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await page.getByText('Use at least 12 characters.', { exact: true }).waitFor();
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Account created successfully' }).waitFor();
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('heading', { name: 'A clearer view. A stronger defense.', exact: true }).waitFor();
    const r = await page.request.get(base + '/api/auth/me');
    const user = await r.json();
    if (user.role !== 'analyst' || !user.bank_id.startsWith('demo_') || user.email !== email) throw Error('Incorrect account permissions');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + '/register');
    await page.getByRole('heading', { name: 'Create your account', exact: true }).waitFor();
    if (await page.locator('body').evaluate(e => e.scrollWidth > innerWidth + 2)) throw Error('Mobile registration overflow');
    if (errors.length) throw Error(errors.join('\n'));
    console.log('PASS: create-account link, exactly two fields, password validation, registration, sign-in, isolated analyst scope, mobile layout.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
