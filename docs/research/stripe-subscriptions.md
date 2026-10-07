# Research: FastAPI Stripe subscriptions

Question from [Research: FastAPI Stripe subscriptions](https://github.com/DavillyDevTeam/davilly-starter/issues/4): official Stripe path for a FastAPI Generated app that sells **subscriptions**, uses **Customer Portal**, and handles **webhooks**. Attach billing to a fastapi-users End-user. One Price ID via env until [Grilling: Stripe plan catalog](https://github.com/DavillyDevTeam/davilly-starter/issues/14) says otherwise. Test-mode happy path over live-mode ops.

This note is for [Task: Stripe subscriptions in the generated app](https://github.com/DavillyDevTeam/davilly-starter/issues/10). Do not implement Stripe in the Template from this ticket.

## Recommendation

Use **Stripe-hosted Checkout** in `mode=subscription` plus a **Customer Portal session**, both created server-side with the official `stripe` Python SDK. Persist Stripe IDs on the fastapi-users End-user. Verify webhooks with `construct_event` on the **raw** request body. Snapshot events are enough for v1.

Smallest FastAPI surface:

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/billing/checkout-session` | JWT (`current_active_user`) |
| `POST` | `/billing/portal-session` | JWT (`current_active_user`) |
| `POST` | `/webhooks/stripe` | Stripe-Signature only (no JWT) |

Optional fourth: `GET /billing/me` so the SPA can read cached subscription status without calling Stripe.

Env (server only except the SPA origin):

| Name | Example | Required |
|------|---------|----------|
| `STRIPE_SECRET_KEY` | `sk_test_…` | yes |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` | yes |
| `STRIPE_PRICE_ID` | `price_…` | yes |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | yes (success / cancel / portal return URLs) |

Do **not** require `STRIPE_PUBLISHABLE_KEY` in v1: hosted Checkout redirects to `session.url`; Stripe.js is not needed.

Library: official [`stripe`](https://pypi.org/project/stripe/) **16.x** (`stripe[async]` extra). Use `StripeClient` + `client.v1.*` + `*_async`. Python ≥ 3.9.

Customers v1 (`customer=`), not Accounts v2 (`customer_account=`). Accounts v2 is GA for Connect and public preview otherwise.

## Official integration shape

Stripe’s own “Build a subscriptions integration” guide is the path: hosted Checkout for signup, webhook provisioning, Dashboard-configured Customer Portal, portal session for self-serve. ([Build a subscriptions integration](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python))

That guide’s hosted-page mode is “low code” and uses a prebuilt Stripe-hosted page. Embedded Checkout / Elements are a larger FastAPI + SPA job and are not needed for v1.

Fulfillment **must** be webhook-driven. You cannot rely on the success page: a customer can pay and drop the connection before the SPA loads. Webhooks are required for subscriptions. ([Fulfill orders](https://docs.stripe.com/checkout/fulfillment?lang=python))

## Library

Current PyPI: **`stripe` 16.0.0** (Python ≥ 3.9). ([PyPI stripe](https://pypi.org/project/stripe/))

Install with the async extra so FastAPI routes can `await` SDK calls:

```text
stripe[async]~=16.0
```

`*_async` methods exist on `StripeClient` (`create_async`, `retrieve_async`, …). The default async HTTP client is `httpx`. ([PyPI stripe — Async](https://pypi.org/project/stripe/))

Use `StripeClient`, not the legacy `stripe.api_key` resource pattern. `StripeClient` arrived in v8; new endpoints will only appear there. From 13.0, top-level (non-`v1`) services are deprecated — call `client.v1.checkout.sessions.create(...)`. ([stripe-python README](https://github.com/stripe/stripe-python); [v1 namespace wiki](https://github.com/stripe/stripe-python/wiki/v1-namespace-in-StripeClient))

Webhook construction on the client:

```python
event = client.construct_event(payload, sig_header, secret)
```

That replaced `stripe.Webhook.construct_event(...)`. Both still exist; `StripeClient.construct_event` is the documented v8+ form. ([Migration guide for v8](https://github.com/stripe/stripe-python/wiki/Migration-guide-for-v8-(StripeClient)))

`Webhook.construct_event` takes `Union[str, bytes, bytearray]` and the type comment names FastAPI explicitly. Default timestamp tolerance is 300 seconds. Missing signature or secret raises `SignatureVerificationError`. ([stripe/_webhook.py](https://github.com/stripe/stripe-python/blob/master/stripe/_webhook.py))

Automatic network retries generate an `Idempotency-Key` when the caller does not pass one. ([PyPI stripe — Automatic retries](https://pypi.org/project/stripe/))

Pin a minor range (`~=16.0`). Types can change in minor releases even when runtime behaviour does not. ([PyPI stripe — Types and the Versioning Policy](https://pypi.org/project/stripe/))

## Environment variables

Secret keys stay on the server. Stripe’s keys guide: store in a secrets vault, or environment variables if there is no vault; never in source. ([Best practices for managing secret API keys](https://docs.stripe.com/keys-best-practices); [API keys](https://docs.stripe.com/keys))

Stripe’s own Python snippet uses `ENV["STRIPE_API_KEY"]`. The subscription webhook sample uses `{{STRIPE_WEBHOOK_SECRET}}`. The map already named `STRIPE_PRICE_ID`. Prefer names that match Dashboard objects:

| Env | Stripe object | Notes |
|-----|---------------|--------|
| `STRIPE_SECRET_KEY` | Secret key `sk_test_` / `sk_live_` | Server only. Sandbox keys start `sk_test_`. Equivalent to Stripe’s `STRIPE_API_KEY` example; pick this name because it is a *secret* key, not a publishable one. |
| `STRIPE_WEBHOOK_SECRET` | Endpoint signing secret `whsec_` | CLI `stripe listen` secret ≠ Dashboard endpoint secret. Do not mix them. ([Webhooks](https://docs.stripe.com/webhooks?lang=python); [signature errors](https://docs.stripe.com/webhooks/signature)) |
| `STRIPE_PRICE_ID` | Recurring Price `price_…` | One catalog entry for v1. Create the Product + Price in the Dashboard (test mode), copy the Price ID. ([Build a subscriptions integration — pricing model](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python)) |
| `FRONTEND_ORIGIN` | SPA origin | Used to build `success_url`, optional `cancel_url`, and portal `return_url`. Local Vite vs Pages hostname. |

Webhook secrets are **not** API keys. Find them under Workbench → Webhooks, or in `stripe listen` output. ([API keys — webhook signing secrets](https://docs.stripe.com/keys))

`STRIPE_PUBLISHABLE_KEY` (`pk_test_` / `pk_live_`) is only required for Stripe.js / Elements / embedded Checkout. Hosted Checkout (`ui_mode` default `hosted_page`) returns `session.url`; the SPA just navigates there. Skip the publishable key until an Elements ticket exists.

Do not ship live keys (`sk_live_`, `rk_live_`) in the Template. Test-mode happy path uses `sk_test_` + CLI `whsec_`.

## Attach billing to a fastapi-users End-user

fastapi-users SQLAlchemy: subclass `SQLAlchemyBaseUserTableUUID` and add columns. The docs say you can add your own fields. ([SQLAlchemy adapter](https://fastapi-users.github.io/fastapi-users/latest/configuration/databases/sqlalchemy/))

Pydantic schemas (`UserRead` / `UserCreate` / `UserUpdate`) are **separate** from the ORM model. Mirror only the fields that should round-trip through the auth API. ([Schemas](https://fastapi-users.github.io/fastapi-users/latest/configuration/schemas/))

Protect Checkout and Portal with `current_active_user = fastapi_users.current_user(active=True)`. That dependency returns the native ORM `User`. ([Get current user](https://fastapi-users.github.io/fastapi-users/latest/usage/current-user/))

### Columns on `User`

| Column | Type | Why |
|--------|------|-----|
| `stripe_customer_id` | `str \| None`, unique | Portal session requires a Customer ID. Saved from `checkout.session.completed`. |
| `stripe_subscription_id` | `str \| None` | Current subscription, if any. |
| `stripe_subscription_status` | `str \| None` | Stripe status (`active`, `trialing`, `past_due`, `canceled`, `unpaid`, `incomplete`, …). What the SPA gates on. |

Do **not** put these on `UserCreate`. An End-user must not set Stripe IDs at registration. Prefer omitting raw Stripe IDs from `UserRead`; expose `stripe_subscription_status` (or a derived `is_subscribed`) if the SPA needs it. `GET /billing/me` can return the rest without polluting `/users/me`.

### Who creates the Stripe Customer

Checkout in subscription mode **creates a Customer** if `customer` is blank. ([Create a Checkout Session](https://docs.stripe.com/api/checkout/sessions/create?lang=python))

The subscriptions guide then says: store the Customer (and Subscription) IDs from `checkout.session.completed`, and pass that Customer ID into the portal session. ([Build a subscriptions integration](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python))

v1 rule:

1. If the End-user already has `stripe_customer_id`, pass `customer=<id>` so Checkout reuses it (email is prefilled and locked).
2. Else omit `customer` and pass `customer_email=<user.email>` plus `client_reference_id=<user.id>`.
3. On `checkout.session.completed`, write `session.customer` (and `session.subscription`) onto that End-user.

Do **not** create a Customer at registration. That leaves orphan Stripe Customers for End-users who never pay.

`client_reference_id` is “a unique string to reference the Checkout Session… used to reconcile the session with your internal systems” (max 200 chars). Put the End-user UUID there. ([Create a Checkout Session](https://docs.stripe.com/api/checkout/sessions/create?lang=python))

Also set metadata so webhooks can find the End-user even if `client_reference_id` is missing:

- Session `metadata.end_user_id`
- `subscription_data.metadata.end_user_id` (copied onto the Subscription; appears on `customer.subscription.*` events). ([Metadata](https://docs.stripe.com/api/idempotent_requests?lang=python); [Metadata use cases](https://docs.stripe.com/metadata/use-cases))

Lookup order in the webhook: `client_reference_id` → `metadata.end_user_id` → `User.stripe_customer_id == session.customer`.

### One Price ID, do not take it from the SPA

The official HTML sample posts `priceId` from a hidden field. For v1 the Template has one env Price. The route reads `STRIPE_PRICE_ID` on the server so the SPA cannot swap prices. Catalog grilling may add more later.

If `stripe_subscription_status` is already `active`, `trialing`, or `past_due`, do not open a second Checkout Session. Return **409** (or create a portal session instead). Otherwise Checkout will happily create another subscription on the same Customer.

## Smallest FastAPI route set

### `POST /billing/checkout-session`

Authenticated. Body empty (or `{}`). Server:

```python
params = {
    "mode": "subscription",
    "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
    "success_url": f"{settings.frontend_origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
    "cancel_url": f"{settings.frontend_origin}/billing/canceled",
    "client_reference_id": str(user.id),
    "metadata": {"end_user_id": str(user.id)},
    "subscription_data": {"metadata": {"end_user_id": str(user.id)}},
}
if user.stripe_customer_id:
    params["customer"] = user.stripe_customer_id
else:
    params["customer_email"] = user.email

session = await client.v1.checkout.sessions.create_async(params)
# return {"url": session.url}  # SPA does window.location.assign
```

`mode` must be `subscription` when there is a recurring Price. `line_items` is required in subscription mode. `success_url` is required for hosted Checkout (`ui_mode` defaults to `hosted_page`). `cancel_url` is optional. `{CHECKOUT_SESSION_ID}` is replaced by Stripe on redirect. ([Create a Checkout Session](https://docs.stripe.com/api/checkout/sessions/create?lang=python); [Build a subscriptions integration](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python))

`quantity: 1` is required for licensed (non-metered) prices. The sample says not to pass quantity for usage-based billing.

Response: `{ "url": "https://checkout.stripe.com/c/pay/cs_test_…" }`. HTTP 303 redirect also matches the official Flask sample; a JSON URL is a better fit for a JWT SPA.

Optional: `subscription_data.billing_mode.type = "flexible"` needs API version `2025-06-30.basil` or later. stripe-python 16 is new enough. Skip for v1 unless you want the new billing behaviour; classic mode is the default.

### `POST /billing/portal-session`

Authenticated. Stripe: authenticate the customer on your site **before** creating the session; you need the Customer ID and a `return_url` unless a default is set in the Dashboard. ([Integrate the customer portal](https://docs.stripe.com/customer-management/integrate-customer-portal?lang=python); [Create a portal session](https://docs.stripe.com/api/customer_portal/sessions/create?lang=python))

```python
if not user.stripe_customer_id:
    raise HTTPException(409, "No billing customer yet")
session = await client.v1.billing_portal.sessions.create_async({
    "customer": user.stripe_customer_id,
    "return_url": f"{settings.frontend_origin}/billing",
})
# return {"url": session.url}
```

Use `customer`, not `customer_account`. The latter is Accounts v2.

If the End-user has never completed Checkout, there is no Customer — 409, and the SPA should send them through Checkout first.

Configure the portal in the Dashboard (test mode) so customers can **update payment methods** at minimum. Upgrades/downgrades need a product catalog; with one Price, leave plan-switching off until catalog grilling closes. ([Build a subscriptions integration — Configure the customer portal](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python))

The session `url` is short-lived. Create a new session on every click.

### `POST /webhooks/stripe`

No JWT. Stripe POSTs JSON with header `Stripe-Signature`.

FastAPI/Starlette: `await request.body()` returns the raw bytes. Do **not** declare a Pydantic body and do **not** call `request.json()` first — that parses the body and signature verification fails. ([Starlette Requests — Body](https://starlette.dev/requests/); [FastAPI Request](https://fastapi.tiangolo.com/advanced/using-request-directly/); stripe-python `WebhookPayload` comment names FastAPI)

```python
@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
):
    payload = await request.body()
    try:
        event = client.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(400, "invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(400, "invalid signature")
    # idempotency + dispatch; then:
    return {"received": True}
```

Return **2xx** quickly. Stripe treats redirects (3xx) as failures. Live-mode retries run up to three days with exponential backoff; sandbox retries three times over a few hours. ([Webhooks — event delivery](https://docs.stripe.com/webhooks))

For `checkout.session.completed`, Checkout waits up to **10 seconds** for the webhook before redirecting the customer. Keep the handler a few DB upserts. ([Fulfill orders](https://docs.stripe.com/checkout/fulfillment?lang=python))

Map Notes: v1 webhooks stay in-process unless research says otherwise. Stripe prefers an async queue at scale (month-start invoice spikes). v1 in-process is fine **if** the handler only upserts End-user billing columns and records `event.id`. Do not send email or call slow third parties inside the request. A queue is a later ticket.

### Optional `GET /billing/me`

Authenticated. Return `{ "stripe_subscription_status": "...", "has_customer": bool }` from the User row. Avoids a Stripe API call on every SPA load. Not required for the happy path (Checkout + webhook + Portal).

## Webhook events for v1

Subscribe **only** to what you handle. Listening to everything is discouraged. ([Webhooks best practices](https://docs.stripe.com/webhooks))

### Must handle (Checkout subscriptions guide)

| Event | Action |
|-------|--------|
| `checkout.session.completed` | New purchase. Provision. Save Customer + Subscription IDs onto the End-user. ([Build a subscriptions integration](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python)) |
| `invoice.paid` | Recurring payment succeeded. Keep access if subscription is `active`. Same event on the first invoice. |
| `invoice.payment_failed` | Payment method failed; subscription becomes `past_due` (after the first invoice). Point the End-user at the Portal. |

`invoice.paid` is also the event the subscription-webhooks table names for provisioning when status is `active`. ([Using webhooks with subscriptions](https://docs.stripe.com/billing/subscriptions/webhooks?lang=python))

### Must handle (Customer Portal)

| Event | Action |
|-------|--------|
| `customer.subscription.updated` | Plan/quantity/cancel-at-period-end/status changes from the portal. Copy `status` (and item price if the catalog grows) onto the End-user. If `cancel_at_period_end` (classic) or `cancel_at` (flexible) is set, access continues until period end. ([Integrate the customer portal](https://docs.stripe.com/customer-management/integrate-customer-portal?lang=python)) |
| `customer.subscription.deleted` | Subscription actually ended. Revoke access (`status=canceled` / clear entitlement). |

### Nice-to-have, skip for v1

- `checkout.session.async_payment_succeeded` / `async_payment_failed` — delayed methods (ACH, SEPA). Card `4242` is immediate.
- `customer.subscription.created` — redundant with `checkout.session.completed` for Checkout-originated subs. Events are **not** ordered; do not require `created` before `completed`. ([Webhooks — event ordering](https://docs.stripe.com/webhooks))
- `customer.updated`, `payment_method.attached` / `detached` — billing details in Stripe; the Generated app does not need a copy in v1.
- `entitlements.active_entitlement_summary.updated` — Entitlements product. Overkill for one Price.
- `invoice.upcoming`, trial events, subscription schedules — no trials/schedules in v1.
- Disputes / refunds / Radar — production hardening, not the test-mode happy path.

Unhandled types: log and return 2xx so Stripe does not retry them.

### Snapshot vs thin

Stripe now recommends **thin** events for new destinations (unversioned, typed, fetch latest object). Snapshot events still ship the full `Event` with `data.object` and `previous_attributes`. ([How events work](https://docs.stripe.com/events/how-events-work))

v1 should register a **snapshot** destination:

- Official subscription and fulfillment samples are snapshot (`construct_event` → `event.type` / `event.data.object`).
- In-process handler can upsert from the payload without a second Stripe GET.
- `customer.subscription.updated` needs `previous_attributes` (or a fetch) to detect cancel-at-period-end transitions; snapshot carries that field.

Revisit thin events if you add a queue and want SDK-typed notifications.

## Idempotency

Two layers.

### Outbound (our POSTs to Stripe)

All Stripe `POST`s accept an `Idempotency-Key`. Keys last **24 hours** on API v1; Stripe suggests UUIDv4; max 255 chars; no PII. Same key + different params → error. ([Idempotent requests](https://docs.stripe.com/api/idempotent_requests?lang=python))

`StripeClient` auto-generates a key on retries. That covers transport flakes, not End-user double-clicks (those are two requests).

For Checkout, pass an explicit key derived from the End-user, e.g. `checkout:{user.id}:{price_id}`. A double-click within 24h returns the same Session instead of a second one. If you need a *new* Session after expiry, include a time bucket or a client nonce.

Portal sessions are cheap and short-lived; auto-retry keys are enough.

### Inbound (Stripe POSTs to us)

Delivery is at-least-once. “Webhook endpoints might occasionally receive the same event more than once. Guard against duplicated event receipts by logging the event IDs you’ve processed, and then not processing already-logged events.” For two different Event objects that represent the same change, use `data.object.id` + `event.type`. Do not use `created` as a dedupe key (second-resolution, unordered). ([Webhooks — handle duplicate events](https://docs.stripe.com/webhooks); [event ordering](https://docs.stripe.com/webhooks))

Fulfillment guide: `fulfill_checkout` must be safe to run multiple times, possibly concurrently, with the same Checkout Session ID. Retrieve the Session from the API, check `payment_status`, record that this Session was fulfilled. ([Fulfill orders](https://docs.stripe.com/checkout/fulfillment?lang=python))

v1 tables:

1. `stripe_event` (`id` PK = `evt_…`, `type`, `created_at`). Insert first; unique violation → return 200 and skip.
2. Treat End-user writes as **upserts of absolute values** (`stripe_customer_id`, `stripe_subscription_id`, `stripe_subscription_status`), not increments. Then a replay of `invoice.paid` is a no-op.

Postgres unique on `stripe_event.id` is the lock. No Redis required (Redis is already optional for JWT blacklist).

A retried delivery gets a **new** `Stripe-Signature` timestamp. Verify each attempt; dedupe on `event.id`, which is stable. ([Webhooks — signature](https://docs.stripe.com/webhooks))

## Signature verification details

Stripe HMAC-SHA256 over `{timestamp}.{raw_body}`. Header form `t=…,v1=…`. Official libraries do this; do not roll your own unless you have to. ([Webhooks](https://docs.stripe.com/webhooks))

Raw body must be the exact UTF-8 bytes Stripe sent. Re-serializing JSON changes key order / whitespace and fails verification. FastAPI: `payload = await request.body()`.

CLI vs Dashboard: “The secret for a CLI-forwarded endpoint is different from the secret for a Dashboard-managed endpoint—don’t mix them up.” ([Signature errors](https://docs.stripe.com/webhooks/signature); [Manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints))

Local Compose: `stripe listen --forward-to localhost:<api-port>/webhooks/stripe`. Copy the printed `whsec_…` into `STRIPE_WEBHOOK_SECRET`. ([Webhooks — test locally](https://docs.stripe.com/webhooks?lang=python); [CLI listen](https://docs.stripe.com/cli/listen.md))

Live mode requires HTTPS. TLS 1.2+. Stripe treats 3xx as failure. ([Webhooks](https://docs.stripe.com/webhooks))

IP allowlisting is documented as a second control. Optional for v1; signature verification is the one that must ship.

## Test-mode happy path

1. Stripe Dashboard **test mode** (sandbox): create one Product + recurring Price; copy `price_…` → `STRIPE_PRICE_ID`. ([Build a subscriptions integration](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python))
2. Copy the sandbox secret key (`sk_test_…`) → `STRIPE_SECRET_KEY`. ([API keys — sandbox versus live](https://docs.stripe.com/keys))
3. Customer portal settings (test mode): enable payment-method update. Preview with Dashboard → Customer → Open customer portal.
4. API + SPA up. `FRONTEND_ORIGIN` = Vite origin.
5. `stripe login` then `stripe listen --forward-to localhost:<api>/webhooks/stripe`. Paste `whsec_…` into `STRIPE_WEBHOOK_SECRET`. Restart the API if env is read at boot.
6. Register / log in as an End-user (fastapi-users JWT).
7. SPA: `POST /billing/checkout-session` with `Authorization: Bearer …` → redirect to `url`.
8. Pay with `4242 4242 4242 4242`, any future expiry, any CVC, any postal code. Decline: `4000 0000 0000 9995`. 3DS: `4000 0025 0000 3155`. ([Build a subscriptions integration — test payment methods](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python); [Fulfill orders — test](https://docs.stripe.com/checkout/fulfillment?lang=python))
9. CLI shows `checkout.session.completed` (and `invoice.paid`). End-user row has `stripe_customer_id` / `stripe_subscription_id` / `status=active`.
10. `POST /billing/portal-session` → manage billing on Stripe-hosted portal → return to `FRONTEND_ORIGIN`.
11. Optional: `stripe trigger checkout.session.completed` for handler unit tests. Triggered fixtures are not the same as a full Checkout; prefer one real 4242 run for the happy path.

Do not register a Dashboard webhook URL until the API is on a public HTTPS origin. CLI forwarding is the local path.

`stripe trigger` / `stripe listen` talk to the sandbox by default. `--live` is opt-in. ([CLI listen](https://docs.stripe.com/cli/listen.md))

## SPA notes (not extra API)

- Checkout and Portal buttons are authenticated `fetch`es to the FastAPI API, then `window.location.assign(url)`.
- Success page may read `session_id` from the query string; **do not** provision there. Webhook is source of truth. Showing “we’re activating your plan…” and polling `GET /billing/me` is enough.
- Hosted Checkout is a different origin (`checkout.stripe.com`); CORS does not apply to that redirect.
- JWT stays in the SPA (memory / localStorage — decided by the auth research). Stripe never sees it.

## Explicitly out of v1

| Topic | Why skip |
|-------|----------|
| Stripe.js / Elements / embedded Checkout | Hosted page is the documented low-code path. |
| `STRIPE_PUBLISHABLE_KEY` | Only for client Stripe.js. |
| Multiple prices / lookup_keys | Catalog grilling. |
| Accounts v2 `customer_account` | Preview for non-Connect. |
| Thin events | Extra GET per event; samples are snapshot. |
| Stripe Tax, coupons, trials, metered usage | Not in the ticket. |
| Entitlements API | One Price; a status column is enough. |
| Background job worker | In-process upserts are enough while the handler stays small. |
| Creating Customer at register | Orphans; Checkout creates one. |
| Billing on a team/org | Billing attaches to the End-user. |
| Live-mode runbooks (restricted keys, rotation, IP allowlist) | Test-mode first. |

## Pointers for the implementation ticket

1. Add `stripe[async]~=16.0` to the Generated app API deps.
2. Env: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`, `FRONTEND_ORIGIN`.
3. Alembic: three nullable columns on `user` + `stripe_event(id PK)`.
4. Three routes as above; webhook excluded from JWT.
5. Dashboard test Product/Price + portal payment-method update; document `stripe listen` in the Generated app README.
6. Do not wait on catalog grilling unless that ticket closes with more than one Price.

## Sources

- [Build a subscriptions integration (Python, hosted Checkout)](https://docs.stripe.com/billing/subscriptions/build-subscriptions?lang=python)
- [Create a Checkout Session](https://docs.stripe.com/api/checkout/sessions/create?lang=python)
- [Fulfill orders](https://docs.stripe.com/checkout/fulfillment?lang=python)
- [Integrate the customer portal](https://docs.stripe.com/customer-management/integrate-customer-portal?lang=python)
- [Create a portal session](https://docs.stripe.com/api/customer_portal/sessions/create?lang=python)
- [Using webhooks with subscriptions](https://docs.stripe.com/billing/subscriptions/webhooks?lang=python)
- [Receive Stripe events in your webhook endpoint](https://docs.stripe.com/webhooks?lang=python)
- [How events work (thin vs snapshot)](https://docs.stripe.com/events/how-events-work)
- [Idempotent requests](https://docs.stripe.com/api/idempotent_requests?lang=python)
- [API keys](https://docs.stripe.com/keys)
- [Best practices for managing secret API keys](https://docs.stripe.com/keys-best-practices)
- [stripe 16.0.0 on PyPI](https://pypi.org/project/stripe/)
- [stripe-python Webhook.construct_event](https://github.com/stripe/stripe-python/blob/master/stripe/_webhook.py)
- [StripeClient v8 migration (construct_event)](https://github.com/stripe/stripe-python/wiki/Migration-guide-for-v8-(StripeClient))
- [Starlette Request.body()](https://starlette.dev/requests/)
- [fastapi-users SQLAlchemy](https://fastapi-users.github.io/fastapi-users/latest/configuration/databases/sqlalchemy/)
- [fastapi-users schemas](https://fastapi-users.github.io/fastapi-users/latest/configuration/schemas/)
- [fastapi-users current_user](https://fastapi-users.github.io/fastapi-users/latest/usage/current-user/)
