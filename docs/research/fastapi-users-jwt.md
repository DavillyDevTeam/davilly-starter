# Research: fastapi-users, JWT, optional Redis, optional OAuth

Question: current, supported way to implement Generated-app auth with fastapi-users (or its documented successor): email/password, JWT, optional Redis token blacklist, optional Google and GitHub OAuth.

Constraints already decided on the map:

- SQLAlchemy + Postgres.
- Email/password always works with no OAuth apps and no Redis.
- If `REDIS_URL` is set, JWT revocation uses a Redis blacklist; if unset, JWT without blacklist.
- Google and GitHub OAuth turn on only when their env vars are present.
- SPA on another origin in prod (Cloudflare Pages); local Vite proxy.

Researched 2026-10-06 against official fastapi-users docs, GitHub source at tag `v15.0.5`, PyPI metadata, httpx-oauth source, and fastapi-users-db-sqlalchemy `7.0.0`.

## Verdict

Use **fastapi-users 15.0.5**. There is no published successor. The project is in maintenance mode: security and dependency updates only, no new features. A replacement “Python authentication toolkit” is mentioned with no name, package, or docs.

The map’s “JWT + optional Redis blacklist” is **not a first-party fastapi-users feature**. Redis in this library is a **different strategy** (`RedisStrategy`): opaque random tokens stored in Redis, not JWTs, not a denylist of JWTs. `JWTStrategy.destroy_token` always raises; logout is a no-op for JWT.

Supported shape that matches the constraints as closely as the library allows:

1. Always: SQLAlchemy User table + email/password routers + **Bearer JWT**.
2. Optional Redis: switch **strategy** at process boot (`JWTStrategy` vs `RedisStrategy`), not a JWT blacklist. Token format changes.
3. Optional Google/GitHub: always keep the `oauth_account` table; mount OAuth routers only when env vars are set.
4. SPA: Bearer + `Authorization` header. Cookie transport is the library’s “web frontend” path and fights a cross-origin Pages SPA.

If true JWT revocation is required without changing token format, that is a **custom `Strategy`**, not documented by fastapi-users. The first-party revocable alternative that does not need Redis is `DatabaseStrategy` (opaque tokens in Postgres).

## Library and successor

- Package: [`fastapi-users`](https://pypi.org/project/fastapi-users/) 15.0.5 (2026-03-27). `__version__ = "15.0.5"`.
- Docs: <https://fastapi-users.github.io/fastapi-users/>
- Source: <https://github.com/fastapi-users/fastapi-users>
- Status (README and PyPI): maintenance mode; “currently working on a new Python authentication toolkit that will ultimately supersede FastAPI Users. Stay tuned.”
- Python: `>=3.10`. Classifiers include 3.10–3.14.

No other library is documented as the successor. Do not wait on it for v1.

## Pins (PyPI + extras as of this research)

Install extras the docs name:

```text
fastapi-users[sqlalchemy,oauth,redis]==15.0.5
```

| Package | Pin / bound | Why |
|---|---|---|
| `fastapi-users` | `==15.0.5` | Current PyPI release |
| `fastapi-users-db-sqlalchemy` | `==7.0.0` (pulled by `[sqlalchemy]`, extra is `>=7.0.0`) | Current adapter; re-exported from `fastapi_users.db` |
| `httpx-oauth` | `>=0.13` extra; current PyPI **0.17.0** | `[oauth]` extra |
| `redis` | extra `>=4.3.3,<8.0.0` | Current redis-py is **8.1.0**, which **does not satisfy** the extra. Pin **`redis>=4.3.3,<8`**, e.g. `==7.4.1` |
| `sqlalchemy[asyncio]` | adapter requires `>=2.0.0,<2.1.0` | SQLAlchemy **2.1.x is out** (2.1.3 as of 2026-10-02). The adapter will not install 2.1. Pin **`sqlalchemy>=2.0.0,<2.1`**, latest 2.0 is **2.0.54** (2026-09-15) |
| `fastapi` | extra `>=0.65.2`; current PyPI **0.142.2** | Compatible; pin a current 0.142.x in the Template |
| `asyncpg` | not an extra; docs say `pip install asyncpg` | Postgres asyncio driver. URL: `postgresql+asyncpg://user:password@host:port/name` |
| `pwdlib[argon2,bcrypt]` | **exact** `==0.3.1` in fastapi-users 15.0.5 | Do not independently bump |
| `pyjwt[crypto]` | `>=2.12.0,<3.0.0` | JWT encode/decode |
| `python-multipart` | `>=0.0.22,<0.1.0` | Required: login is `application/x-www-form-urlencoded` |
| `email-validator` | `>=1.1.0,<2.4` | Pydantic `EmailStr` |

`fastapi-users-db-sqlalchemy` 7.0.0 also depends on `fastapi-users>=10.0.0` and `sqlalchemy[asyncio]>=2.0.0,<2.1.0`.

## How auth is assembled

An **authentication backend** is `transport + strategy` (`AuthenticationBackend(name, transport, get_strategy)`).

Transports (how the token is carried):

- `BearerTransport`: `Authorization: Bearer <token>`. Login returns JSON `{ "access_token", "token_type": "bearer" }`. Logout 204. Suited to “pure REST API” / mobile. SPA stores the token itself.
- `CookieTransport`: `Set-Cookie`. Login/logout 204. Defaults: `cookie_name=fastapiusersauth`, `cookie_secure=True`, `cookie_httponly=True`, `cookie_samesite=lax`. Docs: “use it if you want to implement a web frontend.” Needs CSRF for maximum security; the library does **not** ship CSRF for cookie auth (only for OAuth, since 15.0.2).

Strategies (how the token is generated/verified):

| Strategy | Token | Server-side revoke | Extra infra |
|---|---|---|---|
| `JWTStrategy` | Self-contained JWT (`sub` + `aud`) | **No.** Valid until `exp`. | None |
| `RedisStrategy` | `secrets.token_urlsafe()` stored as `fastapi_users_token:<token> → user_id` | Yes: `DELETE` on logout | Redis |
| `DatabaseStrategy` | Opaque token row (`token`, `user_id`, `created_at`) | Yes: delete row | Postgres (already required) |

`get_strategy` is a FastAPI dependency callable so strategies can take other deps (Redis client, DB session).

`FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])` then generates routers and `current_user(...)`.

## JWT is not a Redis blacklist

### JWT

```python
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)
```

Args: `secret`, `lifetime_seconds` (`None` = never expires — docs warn against this), `token_audience` default `["fastapi-users:auth"]`, `algorithm` default `HS256`, optional `public_key` for RS256.

Payload is `{ "sub": str(user.id), "aud": token_audience, "exp": ... }`. There is no `jti`.

Logout docs: “On logout, this strategy **won't do anything**. Indeed, a JWT can't be invalidated on the server-side: it's valid until it expires.”

Source (`fastapi_users/authentication/strategy/jwt.py`):

```python
async def destroy_token(self, token: str, user: models.UP) -> None:
    raise JWTStrategyDestroyNotSupportedError()
```

`AuthenticationBackend.logout` catches `StrategyDestroyNotSupportedError` and continues, so `POST /logout` still returns 204 for Bearer JWT but **does not revoke the token**.

### Redis

Install: `pip install 'fastapi-users[redis]'`.

```python
import redis.asyncio
from fastapi_users.authentication import RedisStrategy

redis = redis.asyncio.from_url("redis://localhost:6379", decode_responses=True)

def get_redis_strategy() -> RedisStrategy:
    return RedisStrategy(redis, lifetime_seconds=3600)
```

Args: `redis` (`redis.asyncio.Redis`, **`decode_responses=True` is required**), `lifetime_seconds` (default `None` = no TTL), `key_prefix` default `"fastapi_users_token:"`.

`write_token` does **not** encode a JWT. It stores a random URL-safe string. `read_token` `GET`s that key. `destroy_token` `DELETE`s it.

Import of `RedisStrategy` is wrapped in `try/except ImportError` in `fastapi_users.authentication` and `...strategy`. Installing without `[redis]` still lets JWT work.

### What this means for “Redis optional at runtime”

Awkwardness, in order of severity:

1. **Token format is not stable across the Redis on/off switch.** A JWT issued with `REDIS_URL` unset cannot be `GET` from Redis. An opaque Redis token is not a JWT. Clients and OpenAPI both see `access_token`, but the string is a different kind of credential. Rotating `REDIS_URL` between deploys invalidates every outstanding session (JWT still valid until expiry if you switch *to* Redis and keep verifying JWT — you will not, because `get_strategy` returns only one strategy).

2. **`get_strategy` is the supported runtime hook**, not a denylist. You can write:

   ```python
   def get_strategy() -> JWTStrategy | RedisStrategy:
       if settings.redis_url:
           return RedisStrategy(redis, lifetime_seconds=3600)
       return JWTStrategy(secret=SECRET, lifetime_seconds=3600)
   ```

   That is process-boot (or per-request) strategy selection. It is **not** “JWT plus optional blacklist.” Backends are still constructed at import; `get_enabled_backends` can hide backends from `current_user` but “every backend will appear in the OpenAPI documentation, as FastAPI resolves it statically.”

3. **Compile-time vs runtime extras.** `RedisStrategy` imports `redis.asyncio` at module load. The package guards that with `ImportError`, so `[redis]` can be omitted from the lockfile only if the Template never imports `RedisStrategy`. If the Template always imports it for the optional path, **`[redis]` must be a hard dependency** even when Compose omits Redis. That is install-time, not runtime. Connecting is runtime (`from_url(REDIS_URL)` only if set).

4. **A real JWT denylist is custom code.** Subclass `Strategy` (or wrap `JWTStrategy`): put a `jti` in `write_token`, `SET jti` with TTL = remaining lifetime on logout, reject `read_token` if `jti` is present. fastapi-users JWT has no `jti` today. Do this only if the map insists on JWT-shaped tokens when Redis is on. It will not get library tests or docs.

5. **First-party revocable-without-Redis path:** `DatabaseStrategy` + `SQLAlchemyBaseAccessTokenTableUUID`. Logout deletes the row. Always available because Postgres is required. Does not match “JWT” on the map, but it is the documented way to invalidate tokens without Redis.

**Recommendation for the Template:** default `BearerTransport` + `JWTStrategy`. If `REDIS_URL` is set at boot, use `RedisStrategy` instead (same transport, same `/auth/jwt` routes, different token). Document that logout is real only with Redis, and that tokens issued under one mode are invalid under the other. Do not call it a blacklist. Compose omits Redis; prod may set `REDIS_URL`.

If logout/revocation must work without Redis, use `DatabaseStrategy` always and drop JWT.

## Logout and refresh

### Logout

Auth router: `POST /logout` requires a current user+token (`401` if missing). Then `backend.logout`.

| Mode | Strategy effect | Transport effect | Client |
|---|---|---|---|
| JWT + Bearer | none | 204 empty | **Must drop the token locally.** Stolen tokens work until `exp`. |
| Redis + Bearer | `DELETE` key | 204 | Token unusable immediately. |
| Database + Bearer | delete row | 204 | Same. |
| Any + Cookie | as above | `Set-Cookie` expiry | Browser drops cookie. |

Short JWT `lifetime_seconds` (e.g. 3600 as in the official example) is the only first-party mitigation without Redis/DB tokens.

### Refresh

**There is no refresh-token route.** Login returns a single `access_token`. SPA re-logins (or the user uses OAuth again) when it expires.

OAuth *provider* `refresh_token` is stored on `oauth_account.refresh_token` (and `expires_at`) but fastapi-users does not exchange it to mint a new app session.

httpx-oauth `GitHubOAuth2.refresh_token` exists; GitHub user-to-server refresh tokens are opt-in on the GitHub App. Google supports refresh. None of that is wired to `/auth/jwt/login`.

Do not invent a refresh endpoint in v1 unless a later ticket specifies a custom strategy. Official path: one access token, finite `lifetime_seconds`.

## Email/password (always on)

Official SQLAlchemy JWT example layout and routers:

- `POST /auth/jwt/login` — `OAuth2PasswordRequestForm`: **`username` + `password` as form-urlencoded**, not JSON. Field is `username` even though it is the email.
- `POST /auth/jwt/logout`
- `POST /auth/register` — JSON `{ "email", "password" }` → `201` user
- `POST /auth/forgot-password`, `POST /auth/reset-password`
- `POST /auth/request-verify-token`, `POST /auth/verify`
- `/users/me`, `/users/{id}` (superuser for id routes)

`BearerTransport(tokenUrl="auth/jwt/login")` must match the mounted path so Swagger Authorize works.

User table (`SQLAlchemyBaseUserTableUUID`): `id` UUID, `email` (unique, 320), `hashed_password` (1024), `is_active`, `is_superuser`, `is_verified`. Table name `user`.

Password hashing is pwdlib (argon2/bcrypt), not passlib.

`UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID])` must set:

- `reset_password_token_secret`
- `verification_token_secret`

Override `on_after_register` / `on_after_forgot_password` / `on_after_request_verify` to send mail (out of scope here). Login does not require verification unless `get_auth_router(..., requires_verification=True)`.

Email lookup is case-insensitive (`func.lower`).

Production: Alembic, not `create_all`. Docs warn `expire_on_commit=False` on `async_sessionmaker`.

## Optional Google and GitHub OAuth

Install: `pip install 'fastapi-users[sqlalchemy,oauth]'`.

Clients (httpx-oauth 0.17.0):

```python
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.github import GitHubOAuth2

google_oauth_client = GoogleOAuth2(client_id, client_secret)  # name="google"
github_oauth_client = GitHubOAuth2(client_id, client_secret)  # name="github"
```

Default scopes:

- Google: `userinfo.profile`, `userinfo.email`. Profile is fetched from People API (`people/me?personFields=emailAddresses`).
- GitHub: `user`, `user:email`. If the profile email is null, a second call to `/user/emails` picks primary. GitHub App must allow **Email addresses**.

Official SQLAlchemy OAuth example env names for Google:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

Mirror for GitHub (not in the official example; naming should stay parallel):

- `GITHUB_OAUTH_CLIENT_ID`
- `GITHUB_OAUTH_CLIENT_SECRET`

Do **not** instantiate clients with `os.getenv(..., "")` and mount routers anyway (the official example does this). Empty client id fails at authorize time. Mount only when both vars are non-empty so email/password works with no OAuth apps.

### Schema when OAuth is optional

`SQLAlchemyUserDatabase(session, User, OAuthAccount)` takes an optional third argument. `get_by_oauth_account` / `add_oauth_account` raise `NotImplementedError` if it is `None`.

`OAuthAccount` (`SQLAlchemyBaseOAuthAccountTableUUID`): table `oauth_account` with `oauth_name`, `access_token`, `expires_at`, `refresh_token`, `account_id`, `account_email`, `user_id` FK cascade.

On `User`:

```python
oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")
```

**Keep `OAuthAccount` + the relationship + the third constructor arg always.** The table is empty until someone uses OAuth. Switching the User model / Alembic revision based on env vars is worse than an unused table. Routers are what should be conditional.

### Routers

```python
app.include_router(
    fastapi_users.get_oauth_router(google_oauth_client, auth_backend, SECRET),
    prefix="/auth/google",
    tags=["auth"],
)
```

Same for GitHub at `/auth/github`. One router per (client, backend) pair.

Routes:

- `GET /authorize` → `{ "authorization_url" }` plus **CSRF cookie** (since 15.0.2)
- `GET /callback?code&state` → logs the user in via the same backend (JSON token for Bearer, cookie for Cookie)

`associate_by_email=True` links an OAuth identity to an existing email. Docs warn this is unsafe if the provider does not verify email. Google and GitHub do; still a product choice. Default is HTTP 400 `OAUTH_USER_ALREADY_EXISTS`.

`is_verified_by_default=True` skips email verification for OAuth sign-ups. Safe for Google/GitHub if you trust their email verification.

`get_oauth_associate_router` exists for already-logged-in users; optional for v1.

Callback `redirect_url` is the **OAuth provider redirect_uri**, not a post-login SPA URL. If omitted, it is `request.url_for(callback_route_name)` (the API callback). Register that exact URL on the Google/GitHub app.

### OAuth CSRF cookie (15.0.2) — awkward for a Pages SPA

v15.0.2: authorize sets cookie `fastapiusersoauthcsrf` (httponly, secure=True, samesite=lax, max-age 3600). Callback compares it to a `csrftoken` claim inside the JWT `state`. Mismatch → `OAUTH_INVALID_STATE`.

Release notes: “in certain scenarios (e.g. cross-domain setups), additional configuration may be required.”

Cookie knobs on `get_oauth_router`: `csrf_token_cookie_name/path/domain/secure/httponly/samesite`. Local HTTP: `csrf_token_cookie_secure=False`. Cross-site Pages → API: `samesite="none"` and `secure=True`, plus CORS credentials.

Flow mismatch with Bearer + SPA:

1. SPA `GET /auth/google/authorize` (XHR) receives `authorization_url` and a Set-Cookie **for the API origin**.
2. Browser goes to Google, then **top-level GET** to API `/callback`.
3. Callback returns Bearer JSON `{access_token}` **as the document**. The SPA origin never sees it unless you add a custom redirect to the Pages app (not in the library).

Cookie transport makes callback a 204 + `Set-Cookie` on the API host; the user is still sitting on the API origin. Cross-site cookie needs `SameSite=None; Secure` and CORS `allow_credentials`. Chrome third-party cookie rules still apply.

Practical Template options (pick in implementation, not here):

- **A (simplest, recommended for v1 email/password):** Bearer JWT. OAuth: after library callback, a thin wrapper redirects to `{SPA_ORIGIN}/auth/callback#access_token=...` or a one-time code. That wrapper is **not** first-party.
- **B:** Cookie transport, API and SPA on a shared parent domain (`api.example.com` / `app.example.com`) with `cookie_domain=.example.com`. Cloudflare Pages `*.pages.dev` cannot share that domain unless a custom domain is used. Fine if Consumers attach a custom domain; bad as the default Pages URL.
- **C:** Local Vite proxy makes SPA and API same-origin in dev, so Lax cookies and no CORS. Prod still hits A/B.

Email/password Bearer does not need the CSRF cookie at all.

## SPA on another origin

Prod: Pages origin ≠ API origin. Local: Vite proxy → same origin.

For Bearer:

- `CORSMiddleware`: `allow_origins=[SPA_ORIGIN]`, `allow_credentials=False` is enough if the SPA sends `Authorization` and does not use cookies. `allow_headers=["Authorization", "Content-Type"]`. Login is form-urlencoded (`Content-Type: application/x-www-form-urlencoded`).
- SPA stores `access_token` (memory preferred; `localStorage` is XSS-visible).
- Logout: `POST /auth/jwt/logout` then delete local token (JWT still valid until expiry).

For Cookie (if chosen): `allow_credentials=True`, exact origin (not `*`), `cookie_samesite="none"`, `cookie_secure=True`. CSRF remains on the Template.

`tokenUrl` in `BearerTransport` should stay a **relative** path (`auth/jwt/login`) as the docs recommend.

## Minimal module layout

Match the official SQLAlchemy examples (`examples/sqlalchemy` and `examples/sqlalchemy-oauth`), with OAuth/Redis gated in one place:

```text
app/
  main.py          # FastAPI app, CORS, include routers (OAuth if env)
  db.py            # engine, session, User, OAuthAccount, get_user_db
  schemas.py       # UserRead / UserCreate / UserUpdate
  users.py         # UserManager, transport, get_strategy, auth_backend, FastAPIUsers
  config.py        # env: DATABASE_URL, SECRET, REDIS_URL, OAuth, CORS, SPA_ORIGIN
```

`users.py` sketch (JWT default, Redis if URL set):

```python
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_strategy() -> JWTStrategy | RedisStrategy:
    if settings.redis_url:
        return RedisStrategy(
            redis.asyncio.from_url(settings.redis_url, decode_responses=True),
            lifetime_seconds=3600,
        )
    return JWTStrategy(secret=settings.secret, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",  # keep the name even if strategy is Redis; it is the backend id
    transport=bearer_transport,
    get_strategy=get_strategy,
)
```

`main.py` mounts `get_auth_router(auth_backend)` at `/auth/jwt`, register/reset/verify at `/auth`, users at `/users`, and OAuth routers only when client ids are set.

Do not create two `FastAPIUsers` instances. Conditional OAuth is extra `include_router` calls, not a second app object.

## Env vars

| Var | Required | Role |
|---|---|---|
| `DATABASE_URL` | yes | `postgresql+asyncpg://...` |
| `SECRET` | yes | JWT encode, reset/verify JWT, OAuth `state` secret. Official examples use one `SECRET`. Use a long random value. |
| `REDIS_URL` | no | If set, `RedisStrategy`; if unset, `JWTStrategy`. Compose omits Redis. |
| `GOOGLE_OAUTH_CLIENT_ID` | no | With secret, mount `/auth/google` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | no | |
| `GITHUB_OAUTH_CLIENT_ID` | no | With secret, mount `/auth/github` |
| `GITHUB_OAUTH_CLIENT_SECRET` | no | |
| `SPA_ORIGIN` / `CORS_ORIGINS` | prod | Pages origin(s) for CORS. Local proxy can skip CORS. |
| `AUTH_CSRF_COOKIE_SECURE` | local | `False` on HTTP; default `True` |

OAuth app console redirect URIs:

- `{API_PUBLIC_URL}/auth/google/callback`
- `{API_PUBLIC_URL}/auth/github/callback`

## What not to do

- Do not describe Redis as a JWT blacklist in Template docs unless a custom `Strategy` is implemented.
- Do not use Cookie transport as the default for a Pages SPA on `*.pages.dev`.
- Do not require Redis or OAuth apps for `docker compose up` email/password.
- Do not pin SQLAlchemy 2.1 until `fastapi-users-db-sqlalchemy` raises its upper bound.
- Do not pin redis-py 8 until fastapi-users extra allows `>=8`.
- Do not wait for the unnamed successor.
- Do not implement auth in this research ticket.

## Sources

- fastapi-users docs (latest): installation, overview, authentication intro, backend, JWT, Redis, Database, Bearer, Cookie, SQLAlchemy, OAuth, full example, auth router, routes, current user, user manager. <https://fastapi-users.github.io/fastapi-users/>
- PyPI: [fastapi-users 15.0.5](https://pypi.org/project/fastapi-users/), [fastapi-users-db-sqlalchemy 7.0.0](https://pypi.org/project/fastapi-users-db-sqlalchemy/), [httpx-oauth 0.17.0](https://pypi.org/project/httpx-oauth/), [redis](https://pypi.org/project/redis/), [SQLAlchemy](https://pypi.org/project/SQLAlchemy/), [fastapi 0.142.2](https://pypi.org/project/fastapi/)
- Source: [fastapi-users `v15.0.5` `pyproject.toml`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/pyproject.toml), [`jwt.py`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/fastapi_users/authentication/strategy/jwt.py), [`redis.py`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/fastapi_users/authentication/strategy/redis.py), [`backend.py`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/fastapi_users/authentication/backend.py), [`router/auth.py`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/fastapi_users/router/auth.py), [`router/oauth.py`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/fastapi_users/router/oauth.py), [`authentication/__init__.py`](https://github.com/fastapi-users/fastapi-users/blob/v15.0.5/fastapi_users/authentication/__init__.py)
- [v15.0.2 release notes (OAuth CSRF cookie)](https://github.com/fastapi-users/fastapi-users/releases/tag/v15.0.2)
- [fastapi-users-db-sqlalchemy `pyproject.toml` and table classes](https://github.com/fastapi-users/fastapi-users-db-sqlalchemy)
- httpx-oauth: [`clients/google.py`](https://github.com/frankie567/httpx-oauth/blob/master/httpx_oauth/clients/google.py), [`clients/github.py`](https://github.com/frankie567/httpx-oauth/blob/master/httpx_oauth/clients/github.py)
- SQLAlchemy 2.0.54 / 2.1.3 announcements: <https://www.sqlalchemy.org/blog/>
