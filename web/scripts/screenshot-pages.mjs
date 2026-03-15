#!/usr/bin/env node
/**
 * Captures full-page screenshots of all app routes for visual QA.
 *
 * Usage:
 *   UI_PORT=5174 node scripts/screenshot-pages.mjs
 *
 * Screenshots are saved to .runtime/qa-screens/{page}.png
 */

import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '..', '..');

const PORT = process.env.UI_PORT || '5173';
const BASE_URL = `http://127.0.0.1:${PORT}`;
const OUT_DIR = resolve(PROJECT_ROOT, '.runtime', 'qa-screens');

const ROUTES = [
  { path: '/',           name: 'dashboard' },
  { path: '/onboarding', name: 'onboarding' },
  { path: '/sources',    name: 'sources' },
  { path: '/profile',    name: 'profile' },
  { path: '/schedule',   name: 'schedule' },
  { path: '/run',        name: 'run-center' },
  { path: '/timeline',   name: 'timeline' },
  { path: '/history',    name: 'history' },
];

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  // Inject auth token if available (the API requires it)
  const token = process.env.DIGEST_WEB_API_TOKEN;
  if (token) {
    await context.addCookies([]);
    // Token is sent via Authorization header; set it in localStorage
    // after first navigation so the React app picks it up.
  }

  const page = await context.newPage();

  // If we have a token, set it in localStorage before navigating
  if (token) {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await page.evaluate((t) => localStorage.setItem('api_token', t), token);
  }

  console.log(`Capturing ${ROUTES.length} pages from ${BASE_URL} …\n`);

  for (const route of ROUTES) {
    const url = `${BASE_URL}${route.path}`;
    const outFile = resolve(OUT_DIR, `${route.name}.png`);

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 15_000 });
      // Brief pause for any CSS transitions / lazy renders
      await page.waitForTimeout(500);
      await page.screenshot({ path: outFile, fullPage: true });
      console.log(`  ✓ ${route.name.padEnd(14)} → ${outFile}`);
    } catch (err) {
      console.error(`  ✗ ${route.name.padEnd(14)} — ${err.message}`);
    }
  }

  await browser.close();
  console.log('\nDone.');
}

main().catch((err) => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
