# Vercel deployment

**Current deployed configuration:** the frontend, FastAPI coordinator, and bank APIs are now hosted on Vercel, with persistent Neon schemas and restricted service roles. See [Neon/Vercel deployment](neon-vercel.md) for the serverless adaptations and limits. The persistent-container instructions below describe the original alternative; the unmodified local SQLite/container runtime still should not be uploaded as a Vercel Function.

Deploy the React frontend on Vercel, and run the existing FastAPI coordinator and bank clients on a persistent Docker host. The existing application uses SQLite/local bank stores, process-local coordination and long-running bank workers. Uploading it unchanged as a Vercel Function would not preserve these requirements.

1. Deploy the backend/bank services using the supplied Dockerfiles and private bank networks. Give the API a public HTTPS origin. Keep bank endpoints private, and do not deploy local `.env`, bank datasets or privacy journals as public assets.
2. Build the frontend: from `frontend`, run `pnpm install --frozen-lockfile` and `pnpm build`.
3. From the repository root: `node scripts/prepare-vercel.mjs --backend-url https://YOUR-API-HOST`. This stages only public built assets, SPA fallback routing, security headers and a same-origin `/api/*` rewrite. It deliberately fails when no backend origin is supplied.
4. Sign in to the Vercel CLI with `vercel login` and deploy the staged directory with `vercel runtime/vercel-deploy --prod --yes`. Select your intended account/team when prompted. Do not deploy the repository root; it contains runtime data and local secrets.
5. Set the backend's `FRONTEND_ORIGIN` to the exact final Vercel HTTPS URL and `COOKIE_SECURE=true`, then restart the backend. The API rewrite keeps the existing HttpOnly, SameSite=Strict session cookie on the frontend origin; no direct cross-site cookie relaxation is needed.
6. Verify registration, sign-in, `/api/auth/me`, a training round and case review at the final domain. Preview deployment domains require their own approved origin; the current backend accepts one origin. Do not disable origin checking to accommodate arbitrary preview URLs.

The UI uses polling, so its current round monitoring does not need a WebSocket proxy. A future WebSocket consumer should connect directly to an authenticated HTTPS/WSS backend endpoint with an explicit allowed origin policy. No credentials belong in frontend build variables.

Vercel account authentication and a public backend URL are required before a working deployment can be completed. The staging script alone does not publish the app.

References: [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite), [external rewrites](https://vercel.com/docs/routing/rewrites), [CLI deployment](https://vercel.com/docs/projects/deploy-from-cli).
