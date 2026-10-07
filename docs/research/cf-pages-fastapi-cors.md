# Cloudflare Pages SPA talking to a FastAPI API (CORS, JWT, local one-origin)

Research for [Research: Cloudflare Pages plus FastAPI CORS](https://github.com/DavillyDevTeam/davilly-starter/issues/5).
Do not implement deploys from this note.

**Already decided (map / ADR 0001):** JWT auth (access token, not cookie sessions as primary); Redis optional; prod SPA on Cloudflare Pages; API is **not** on Cloudflare Workers; API on any Docker host (Fly / Railway / VPS — not pinned). Local bar is `docker compose up` showing the landing page.

## Recommendation (gist)

Two origins in production, one origin in local Compose.

- **Prod SPA** is a static Vite React build on Cloudflare Pages (`<project>.pages.dev` and any custom domains). It calls the API at an absolute HTTPS URL baked in at **build time** as `VITE_API_URL`.
- **Prod API** is a FastAPI container on any Docker host. It serves CORS for an **explicit allowlist** of the Pages hostname plus custom domains. Access tokens travel as `Authorization: Bearer <jwt>` on `fetch`. Do not send cookies (`credentials: "include"`) for the primary path.
- **Local Compose** puts Vite in front and **proxies** `/api` to Uvicorn. The SPA uses a relative `/api` (empty or omitted `VITE_API_URL`). The browser sees one origin, so CORS is not on the tomorrow-morning path.
- Pages `_redirects` **cannot** proxy the API. Changing `VITE_API_URL` requires a rebuild. Preview deployments (`<hash>.<project>.pages.dev`) are extra origins and need CORS coverage if they talk to a live API.

## Two origins in prod, one origin locally

An origin is scheme + host + port ([FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/), [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)). `https://app.example.com` and `https://api.example.com` are different origins even on the same registrable domain. `http://localhost:5173` and `http://localhost:8000` are also different origins.

| Environment | SPA origin | API origin | Browser CORS? |
| --- | --- | --- | --- |
| Pages + Docker API | `https://<project>.pages.dev` or custom domain | `https://api.example.com` (or host URL) | Yes |
| Local Compose with Vite proxy | `http://localhost:5173` (or published web port) | Same, via `/api` proxy | No |
| Local without proxy | `http://localhost:5173` | `http://localhost:8000` | Yes — avoid this for the boot bar |

Pages is static hosting with SPA fallback: if there is no top-level `404.html`, unmatched paths serve `/` so React Router can handle `/about` ([Serving Pages](https://developers.cloudflare.com/pages/configuration/serving-pages/)). Do **not** add a `404.html` unless you want real 404s instead of client routing.

Pages `_redirects` can rewrite only **relative** URLs. “Proxying will only support relative URLs on your site. You cannot proxy external domains.” ([Redirects](https://developers.cloudflare.com/pages/configuration/redirects/)). The SPA cannot hide the API behind Pages. CORS on FastAPI is required in production.

A Pages SPA is HTTPS. The API URL must be HTTPS too, or the browser blocks it as mixed content.

Stripe webhooks and similar server-to-server calls hit the API origin, not Pages, and are not a CORS problem.

## `VITE_API_URL`: build-time, not runtime

Vite exposes only `VITE_`-prefixed variables on `import.meta.env`. They are “defined as global variables during dev and **statically replaced at build time**”. They are bundled into client JS. They must not hold secrets ([Env Variables and Modes](https://vite.dev/guide/env-and-mode)).

```ts
const apiBase = import.meta.env.VITE_API_URL ?? "";
await fetch(`${apiBase}/health`);
```

| Value of `VITE_API_URL` | Result |
| --- | --- |
| unset / `""` | Relative URLs. Local proxy can make `/api/...` same-origin. |
| `https://api.example.com` | Absolute cross-origin calls from Pages. |

HTML can also substitute `%VITE_API_URL%` ([HTML constant replacement](https://vite.dev/guide/env-and-mode.html#html-constant-replacement)). Same build-time rule.

Existing process env wins over `.env` files. `vite build` loads `.env.production` by default. `VITE_API_URL=https://api.example.com vite build` is the CI form.

`base` ([shared options](https://vite.dev/config/shared-options.html#base)) is the public path of the SPA, not the API. Pages at the domain root uses the default `/`.

### Pages environment variables

Pages injects custom env vars into the **build** when Cloudflare runs the build ([Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)): dashboard **Settings → Environment variables**. Built-in: `CI`, `CF_PAGES=1`, `CF_PAGES_COMMIT_SHA`, `CF_PAGES_BRANCH`, `CF_PAGES_URL`.

Production and preview are separate `deployment_configs` with their own `env_vars` ([Pages project API](https://developers.cloudflare.com/api/resources/pages/subresources/projects/methods/create/)). Set `VITE_API_URL` on **both** if preview builds should call an API. A production-only variable is absent from PR builds.

Framework preset for Vite: build command `npm run build`, output directory `dist` ([Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)).

**Git integration** (Cloudflare builds from GitHub/GitLab): dashboard `VITE_API_URL` is in the build environment and Vite inlines it. Preview vs production can point at different APIs.

**Direct Upload** (`npx wrangler pages deploy dist`): you upload **already-built** assets ([Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)). Dashboard env vars do not rewrite the JS. Set `VITE_API_URL` in CI *before* `vite build`. Git integration and Direct Upload cannot be swapped on the same project ([Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/)).

Wrangler `[vars]` / `[env.production].vars` are **Pages Functions runtime bindings**, not Vite compile-time env ([Functions wrangler configuration](https://developers.cloudflare.com/pages/functions/wrangler-configuration/)). A static SPA does not read them. Do not add a Function just to inject the API URL; that is extra runtime and the map forbids putting the API on Workers.

There is no first-party Vite runtime config on Pages. Changing the API host means a new `vite build` (and a new Pages deployment). A `public/config.json` fetched at boot is a possible escape hatch, but it is still a static asset and still a deploy to change.

## CORS allowlist on FastAPI

Use Starlette `CORSMiddleware` via FastAPI ([CORS tutorial](https://fastapi.tiangolo.com/tutorial/cors/), [source](https://github.com/encode/starlette/blob/master/starlette/middleware/cors.py)).

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://<project>.pages.dev",
        "https://app.example.com",  # custom domain, if any
    ],
    allow_origin_regex=r"https://[a-z0-9-]+\.<project>\.pages\.dev",  # preview hashes / branch aliases
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Drive `allow_origins` from API env (e.g. `CORS_ORIGINS` comma-separated). Do not hard-code a Consumer’s Pages hostname in the Template.

### Why not `allow_origins=["*"]`

FastAPI: a wildcard “will only allow certain types of communication, excluding everything that involves credentials: Cookies, Authorization headers like those used with Bearer Tokens, etc.” Explicit origins are the documented path ([CORS](https://fastapi.tiangolo.com/tutorial/cors/#wildcards)).

OWASP: allow only selected trusted domains; do not use `*` on sensitive URLs; do not echo `Origin` blindly ([HTML5 Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)).

`allow_credentials=True` forbids `*` on origins, methods, and headers ([FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/), [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSNotSupportingCredentials)). Bearer-in-header as primary should keep `allow_credentials=False` so cookies are not in play. If a later refresh cookie appears, switch to explicit origins **and** `allow_credentials=True`.

### `Authorization` is not a wildcard header

`Authorization` is a CORS non-wildcard request-header name ([Fetch Standard](https://fetch.spec.whatwg.org/#cors-non-wildcard-request-header-name)). A preflight fails unless `Access-Control-Allow-Headers` lists `Authorization` by name; `*` does not cover it ([MDN Access-Control-Allow-Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Headers)).

Starlette with `allow_headers=["*"]` mirrors `Access-Control-Request-Headers` on the preflight, which usually includes `authorization`. Listing `Authorization` (and `Content-Type`) is clearer and survives `allow_credentials=True`.

`Authorization` is not a CORS-safelisted request header, so every Bearer call is **preflighted** (`OPTIONS` + `Access-Control-Request-Method` / `Headers`). FastAPI’s middleware answers those `OPTIONS` requests ([CORS preflight](https://fastapi.tiangolo.com/tutorial/cors/#cors-preflight-requests)). Default `allow_methods` is `["GET"]` only — POST login will fail until methods are opened.

### Origins to put on the list

Production Pages hostname is `<project>.pages.dev`. Custom domains are extra origins (apex or subdomain CNAME to `<project>.pages.dev`) ([Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)). `www` vs apex are different origins if both are attached.

Preview deployments: `<hash>.<project>.pages.dev` (atomic) and `<branch>.<project>.pages.dev` (alias; branch names lowercased, non-alphanumeric → hyphen) ([Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/)). They do not affect production custom domains. They are public unless Cloudflare Access is enabled.

Do **not** regex `https://.*\.pages\.dev` — that is every Pages project on the account *and* others. Scope the regex to **this** project, or skip preview→API CORS and point preview `VITE_API_URL` at a staging API whose allowlist uses the same regex.

Local Vite without proxy would need `http://localhost:5173` (and `127.0.0.1` if used). The Compose proxy path should not need those.

Scheme and port must match. `http://` vs `https://` are different origins.

## JWT from the SPA

Decided primary: JWT access token, not cookie sessions. fastapi-users models this as `BearerTransport` + `JWTStrategy` ([Authentication](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/), [Bearer](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/transports/bearer/), [JWT](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/strategies/jwt/)). FastAPI’s own JWT tutorial uses the same JSON shape ([OAuth2 JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)).

Login (form fields `username` + `password`, not JSON):

```http
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=...
```

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Authenticated calls:

```http
Authorization: Bearer <jwt>
```

fastapi-users Bearer docs: the client must **store the token itself**. Cookie transport is the one browsers store automatically; that is not the primary path.

`JWTStrategy` default lifetime is 3600 seconds. Logout **does nothing** — a JWT is valid until `exp`. Redis strategy can delete tokens on logout; that is the optional runtime blacklist already on the map.

There is **no refresh-token grant** in fastapi-users `JWTStrategy`. “Refresh” for v1:

1. Keep access tokens short-lived (the 3600s default is fine).
2. On 401, send the end-user through login again.
3. Optional later: a custom refresh endpoint, or a cookie refresh **in addition to** Bearer access — not instead of it.

Do not invent a second cookie session as the primary Generated-app auth.

### Where the access token lives

OWASP: do not store authentication tokens / JWTs in `localStorage` or `sessionStorage`; any XSS can read them. Prefer `HttpOnly; Secure; SameSite` cookies or a BFF ([Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [HTML5 Storage](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#local-storage)).

That conflicts with “Bearer, not cookie sessions.” For this Starter, the least-wrong Bearer fit is:

| Place | Survives reload | XSS can steal | Fits Bearer primary |
| --- | --- | --- | --- |
| JS memory (React state / module var) | No | Yes, while the tab is open | Yes — default |
| `sessionStorage` | Same tab | Yes | Common, weaker |
| `localStorage` | Until cleared | Yes, and persists | Do not |
| `HttpOnly` cookie | Yes | No | Cookie transport; not primary |

Recommend **in-memory access token**. Tab reload logs the end-user out unless they sign in again (or a later refresh design is added). If a Generated app persists anyway, `sessionStorage` is less bad than `localStorage` (cleared when the tab closes) but still XSS-readable — document that.

JWTs are signed, not encrypted; anyone who has the string can read claims ([FastAPI JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [OWASP JWT](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)). Do not put secrets in claims. TLS covers the wire.

### `fetch` + `Authorization`

Default `fetch` `credentials` is `"same-origin"` ([Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)). Setting `headers: { Authorization: "Bearer …" }` does **not** require `credentials: "include"`. `"include"` is for cookies / TLS client certs / browser-managed HTTP auth, forces `Access-Control-Allow-Credentials: true`, and forbids `Access-Control-Allow-Origin: *`.

```ts
await fetch(`${apiBase}/users/me`, {
  headers: { Authorization: `Bearer ${accessToken}` },
  // credentials: "include"  // do not set for Bearer-only
});
```

Login `Content-Type: application/x-www-form-urlencoded` plus POST is a simple CORS request *until* you add `Authorization`. After login, every Bearer call preflights.

Default `mode` is `"cors"`. Do not use `"no-cors"` — the response would be opaque and `Authorization` is not allowed.

## Local Vite proxy so Compose feels like one origin

Vite `server.proxy` forwards matching paths to a backend. Proxied requests are **not** transformed by Vite. The browser stays on the Vite origin ([Server options](https://vite.dev/config/server-options.html#server-proxy)). `preview.proxy` defaults to `server.proxy` ([Preview options](https://vite.dev/config/preview-options.html#preview-proxy)), so `vite preview` can keep the same one-origin trick.

```ts
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: true,       // 0.0.0.0 — required if Vite is in a container
    port: 5173,
    strictPort: true, // fail if 5173 is taken (Compose published port)
    proxy: {
      "/api": {
        target: "http://api:8000", // Compose service DNS name
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

Drop `rewrite` if FastAPI is already mounted at `/api`.

Inside Compose, services reach each other by **service name** on the project default network ([Compose networking](https://docs.docker.com/compose/how-tos/networking/)). `http://api:8000` is correct **from the Vite container**. `http://localhost:8000` is the API only from the Docker host, not from another container.

Sketch (not an implementation):

```yaml
services:
  api:
    # uvicorn on 8000
  web:
    # vite --host 0.0.0.0 --port 5173
    ports:
      - "5173:5173"
    depends_on:
      - api
  db:
    image: postgres
    # no Redis unless REDIS_URL is set
```

`docker compose up` → open `http://localhost:5173` → landing page. SPA calls `/api/...` → Vite → `api:8000`. No CORS, no `VITE_API_URL`.

Vite in Docker must listen on `0.0.0.0` (`server.host: true` or `--host`). Bind-mount the frontend tree if HMR is wanted; that is a Template detail, not a Pages detail.

If Vite runs on the host against Compose-published `8000:8000`, proxy `target` is `http://localhost:8000`. Pick one topology and generate it; mixing them is the usual “proxy ECONNREFUSED” footgun.

## Deploy sketch (not pinned to a host)

```
Generated app repo
├── frontend/          → vite build → dist/ → Cloudflare Pages
└── backend/           → Docker image → any host running that image
```

### SPA → Pages

1. Set `VITE_API_URL=https://<api-host>` in the environment that **runs** `vite build` (Pages dashboard for Git integration; CI for Direct Upload). Set it on preview too if preview should call an API.
2. `npm run build` (or pnpm/bun — package manager is still fog). Output `dist/`.
3. Git integration: connect the repo, root directory `frontend/` if the SPA is not at repo root, build command `npm run build`, output `dist`. Production branch updates `<project>.pages.dev` and custom domains; other branches get preview URLs ([Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/)).
4. Direct Upload: `npx wrangler pages deploy dist --project-name=<name>` ([Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [CI recipe](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)).
5. Optional custom domain: apex needs a Cloudflare zone; a subdomain can CNAME to `<project>.pages.dev` ([Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)). Add every attached origin to `CORS_ORIGINS`.
6. Do not add top-level `404.html`. Optional `_headers` for CSP etc. ([Headers](https://developers.cloudflare.com/pages/configuration/headers/)). Pages already sends `Access-Control-Allow-Origin: *` on **static assets**; that is not API CORS.

### API → Docker host

1. Image runs Uvicorn (or gunicorn+uvicorn workers) on an internal port.
2. Env: `CORS_ORIGINS=https://<project>.pages.dev,https://app.example.com`, plus DB URL, JWT secret, optional `REDIS_URL`, Stripe keys, OAuth client IDs.
3. Publish behind HTTPS (the host’s proxy, Fly/Railway edge, Caddy, …). The SPA cannot call `http://` from Pages.
4. Not a Cloudflare Worker. Not served by FastAPI `StaticFiles` in prod (ADR 0001).

Order: API must be reachable at the URL baked into the SPA **before** that Pages deployment is useful. A first API deploy with a placeholder CORS origin, then a Pages deploy, then tightening CORS, is fine.

### What this is not

- FastAPI on Pages Functions / Workers.
- Pages `_redirects` 200-proxy to the API.
- Cookie `SameSite=None` as the v1 session.
- Runtime `VITE_API_URL` without a rebuild.
- `allow_origins=["*"]` with Bearer tokens as the documented FastAPI setup.

## Implementation notes for later tickets

These are facts for [Task: Prod deploy docs Pages and Docker API](https://github.com/DavillyDevTeam/davilly-starter/issues/12), [Task: Scaffold generator landing boot](https://github.com/DavillyDevTeam/davilly-starter/issues/8), and [Task: Auth in the generated app](https://github.com/DavillyDevTeam/davilly-starter/issues/9) — not work in this research ticket.

- Template should generate `VITE_API_URL` (typed on `ImportMetaEnv`) and `CORS_ORIGINS`. Empty `VITE_API_URL` locally; required for a Pages build.
- Auth client: `FormData` / `application/x-www-form-urlencoded` to `/auth/jwt/login`, keep `access_token` in memory, attach `Authorization` on later `fetch`. No `credentials: "include"`.
- OAuth redirect URIs (Google/GitHub) belong on the **API** origin, then the API must send the SPA back with a token. That is auth-ticket work; CORS still uses the Pages origin as the browser origin of the JS that stores the token.
- Preview hash origins either get a tight `allow_origin_regex` or they do not call production APIs.

## Sources

- Cloudflare Pages: [Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/), [Serving Pages](https://developers.cloudflare.com/pages/configuration/serving-pages/), [Redirects](https://developers.cloudflare.com/pages/configuration/redirects/), [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/), [Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/), [Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/), [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Functions wrangler configuration](https://developers.cloudflare.com/pages/functions/wrangler-configuration/), [Pages project API](https://developers.cloudflare.com/api/resources/pages/subresources/projects/methods/create/)
- Vite: [Env and mode](https://vite.dev/guide/env-and-mode), [server.proxy](https://vite.dev/config/server-options.html#server-proxy), [preview.proxy](https://vite.dev/config/preview-options.html#preview-proxy)
- FastAPI / Starlette: [CORS](https://fastapi.tiangolo.com/tutorial/cors/), [OAuth2 JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [CORSMiddleware source](https://github.com/encode/starlette/blob/master/starlette/middleware/cors.py)
- fastapi-users: [Authentication](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/), [Bearer](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/transports/bearer/), [JWT](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/strategies/jwt/)
- Fetch / CORS: [Fetch Standard](https://fetch.spec.whatwg.org/), [Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch), [Access-Control-Allow-Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Headers)
- OWASP: [HTML5 Security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html), [Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [JWT](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)
- Docker: [Compose networking](https://docs.docker.com/compose/how-tos/networking/)
