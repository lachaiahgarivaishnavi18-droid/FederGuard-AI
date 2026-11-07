// Stage only built public frontend assets and an HTTPS API rewrite for Vercel.
import { cp, mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const index = process.argv.indexOf('--backend-url');
const value = index >= 0 ? process.argv[index + 1] : process.env.BACKEND_URL;
const frontendOnly = process.argv.includes('--frontend-only');
if (!value && !frontendOnly) throw new Error('Provide --backend-url https://your-backend-host. Login and training need a deployed backend.');
const backend = value ? new URL(value) : null;
if (backend && (backend.protocol !== 'https:' || backend.username || backend.password || backend.search || backend.hash || backend.pathname !== '/' || /^(localhost|127\.|0\.0\.0\.0|\[::1\])/.test(backend.hostname))) {
  throw new Error('Backend must be a public HTTPS origin without credentials, query strings or path.');
}
await readFile(path.join(root, 'frontend/dist/index.html'));
const stage = path.join(root, 'runtime', 'vercel-deploy');
await mkdir(stage, { recursive: true });
await cp(path.join(root, 'frontend/dist'), stage, { recursive: true });
await writeFile(path.join(stage, 'vercel.json'), JSON.stringify({
  $schema: 'https://openapi.vercel.sh/vercel.json',
  version: 2,
  rewrites: [
    ...(backend ? [{ source: '/api/:path*', destination: `${backend.origin}/api/:path*` }] : []),
    { source: '/((?!api/).*)', destination: '/index.html' },
  ],
  headers: [
    { source: '/(.*)', headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
    ] },
  ],
}, null, 2));
console.log(`Staged Vercel deployment at ${stage}. ${backend ? 'API origin: '+backend.origin : 'Frontend-only: backend not connected; API paths return 404.'}`);
