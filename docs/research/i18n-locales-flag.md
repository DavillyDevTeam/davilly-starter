# i18n locales flag (FastAPI + Vite React + Copier)

Research for [Research: locales flag FastAPI React](https://github.com/DavillyDevTeam/davilly-starter/issues/6).
Does not implement i18n in the Template.

## Recommendation (gist)

Default Copier answer: `locales: [en, pt-BR]`. The Generator flag `--locales` accepts a comma-separated subset of those two BCP 47 tags. Omitted flag → both. English-only → `--locales en`.

Keep **one catalog format** that both sides load: **i18next JSON v4**, one directory per tag (`locales/en/`, `locales/pt-BR/`). The SPA uses `i18next` + `react-i18next`. The API uses a small request-scoped Python loader over the **same files** (not gettext, not a second catalog). Transactional email copy is a namespace in those files, rendered with the **End-user's stored locale**, not the worker's `Accept-Language`.

Drop unused languages at generation time with a **templated Copier `_exclude` block**. Do not leave `pt-BR/` (or a switcher that lists it) in an English-only tree.

Do **not** put `/en` and `/pt-BR` in the Vite SPA router for v1. Use a language **switcher** (hidden when only one locale was generated) plus `i18next-browser-languagedetector`. The SPA sends its active tag as `Accept-Language` on API calls. Cloudflare Pages already serves the SPA for unknown paths; prefixes would not buy SEO without prerender, which ADR 0001 does not include.

## Canonical tags

Use IETF BCP 47 tags with a **hyphen**: `en` and `pt-BR`. HTTP language tags are defined as RFC 5646 `Language-Tag` values. [`Accept-Language`](https://www.rfc-editor.org/rfc/rfc9110.html#field.accept-language) carries RFC 4647 language ranges of those tags. i18next requires the same shape (`en-US`, not `en_US`).

Do not store POSIX/gettext forms (`pt_BR`, `en_US`) as the Generator's public vocabulary. Python's gettext loader looks up `localedir/language/LC_MESSAGES/domain.mo`; that `language` slot is conventionally underscore-separated. Babel's `Locale.parse` / `negotiate_locale` default separator is `_`, and Babel's default alias table maps bare `pt` → `pt_PT` (European Portuguese). For a Brazil-first starter that is a footgun: `Accept-Language: pt` must resolve to `pt-BR` when that is the only Portuguese catalog.

v1 Generator choices are exactly `{en, pt-BR}`. Arbitrary extra tags are out of scope: the Template would have no catalogs for them.

Fallback language: `en` if present in the generated set, otherwise the sole remaining locale.

## Library pair agents can keep in sync

**Pair: `i18next` + `react-i18next` (SPA) and a thin Python JSON catalog loader (API + email), sharing i18next JSON v4 files.**

Why this pair:

- One file tree, one key namespace, one interpolation syntax (`{{name}}`, plural suffixes `_one` / `_other`). Agents edit JSON, not a JS format plus a Python format.
- i18next JSON v4 is specified (nested keys, `{{value}}` interpolation, CLDR plural suffixes). English and Portuguese both use CLDR `one` / `other` for ordinary integers, so v1 does not need extra plural categories.
- `react-i18next` is the documented React binding (`useTranslation` / `t()`).
- FastAPI has **no** first-party i18n. There is nothing official to "just enable." A 30-line loader plus a locale dependency beats a gettext stack that cannot share files with the SPA.
- Catalogs can be bundled into the Vite build (import JSON / `import.meta.glob`) so Cloudflare Pages does not need extra locale HTTP routes.

Rejected pairs:

| Pair | Why not |
|------|---------|
| Babel gettext + `react-i18next` | Two catalogs (`.po`/`.mo` vs JSON). Underscore dirs vs hyphen tags. `.mo` compile step. Agents drift. |
| `fastapi-i18n` / `starlette-babel` / `starlette-i18n` + `react-i18next` | Those packages wrap gettext and `Accept-Language`; they do not read i18next JSON. |
| FormatJS (`react-intl`) + ICU on Python | ICU MessageFormat is excellent, but Python ICU is PyICU (native lib) or a second implementation. No FastAPI-native FormatJS. |
| Lingui + Babel PO | True shared gettext pair; worse for agents (PO syntax, compile, `pt_BR` paths). |
| Mozilla Fluent (`@fluent/react` + `fluent.runtime`) | True shared `.ftl` pair. Agents know i18next JSON far better. Extra syntax for a two-locale starter. |
| `python-i18n` YAML/JSON | Interpolation is `%{var}`, not i18next `{{var}}`. Still two dialects. |

Use **Babel only as CLDR data** (display names, date/number patterns) if needed later. Do not use it as the message-catalog runtime in v1.

Do **not** call `gettext.install()` (or Jinja `Environment.install_gettext_translations` on a process-global env) inside FastAPI. The stdlib GNU API "will affect the translation of your entire application globally"; concurrent requests would race. Keep a `contextvars.ContextVar` (or pass the translator into the request) the way `fastapi-i18n` describes, even if we do not take that package.

### Catalog layout in the Generated app

One shared tree, imported by both apps:

```
locales/
  en/
    common.json
    errors.json
    emails.json
  pt-BR/
    common.json
    errors.json
    emails.json
```

Namespaces (i18next `ns`): `common` (UI chrome, landing, auth forms), `errors` (API + Pydantic types), `emails` (subjects and bodies). Keys are stable English identifiers (`errors.user_not_found`), never the English sentence. i18next's default key fallback is the key itself, not natural language; do not put `:` or `.` inside key *segments*.

Python loads the same paths at process start (dict `locale → ns → tree`). Vite bundles the generated locales only; after Copier exclusion the unused folder is gone, so it cannot leak into the client bundle.

A Generated-app constant, rendered by Copier, is the single runtime allow-list:

```python
SUPPORTED_LOCALES = {{ locales | tojson }}  # e.g. ["en", "pt-BR"]
DEFAULT_LOCALE = "en" if "en" in SUPPORTED_LOCALES else SUPPORTED_LOCALES[0]
```

Mirror it in the SPA (`supportedLngs`, `fallbackLng`).

## Copier: flag, answers, no dead languages

### Question

Copier answers come from, in order: CLI/API `data`, interactive prompt, previous `.copier-answers.yml`, then `copier.yml` defaults. The Generator is a Typer wrapper around `copier.run_copy(..., data=..., defaults=True)` when flags are passed, so the Consumer is not prompted for locales they already set.

Use a **multiselect** question. Copier documents `multiselect: true` as producing `list[T]`:

```yaml
locales:
  type: str
  help: BCP 47 locales to ship (English and/or Portuguese Brazil)
  choices:
    - en
    - pt-BR
  multiselect: true
  default:
    - en
    - pt-BR
  validator: >-
    {%- if locales | length < 1 -%}
    Select at least one locale
    {%- endif -%}
```

That default is the ticket's omitted-flag value. A Copier discussion shows the same `length < 1` validator pattern for "require at least one."

### Generator CLI

Public interface (AFK-friendly):

```text
davilly-starter new my-app
davilly-starter new my-app --locales en
davilly-starter new my-app --locales en,pt-BR
```

Typer parses the comma-separated string into `list[str]`, validates each tag ∈ `{en, pt-BR}`, rejects the empty list, and passes a **Python list** into Copier:

```python
copier.run_copy(src, dst, data={"locales": ["en"]}, defaults=True)
```

`run_copy(..., data=dict)` is the documented API; values may be any Python object, so a list does not have to survive Copier's CLI `--data VARIABLE=VALUE` string parser.

If someone invokes Copier CLI directly, current Copier documents a YAML-style list for multiselect:

```text
copier copy -d 'locales=["en"]' template dest
```

`--data-file` is the other official escape hatch (YAML file of answers). The Generator should not rely on Consumers typing that; Typer is the interface.

Do not make `locales` a free-form `str` of `"en,pt-BR"` unless the Python API is unavailable. Multiselect is the interactive UX; the list is the render context.

### Excluding unused locale files

Copier `_exclude` patterns:

- are gitignore-style (via pathspec),
- are matched against **destination** paths,
- **each pattern can be templated with Jinja**,
- a single entry may render to several newline-separated patterns,
- an empty render excludes nothing extra.

Copier's own example is the mechanism to use:

```yaml
_exclude:
  - |
    {% if 'en' not in locales %}
    /locales/en/
    {% endif %}
    {% if 'pt-BR' not in locales %}
    /locales/pt-BR/
    {% endif %}
```

When `locales == ["en"]`, the `pt-BR` block emits `/locales/pt-BR/` and that tree is never copied. When both are selected, both `if`s are false and nothing extra is excluded.

**Must re-list Copier's default excludes.** Defining `_exclude` in `copier.yml` **replaces** the default list (`copier.yml`, `.git`, `__pycache__`, …). Always include those defaults (or set `_subdirectory` so the default becomes `[]` and the Template root is already clean).

Also gate UI that would otherwise name a missing language:

```jinja
{# LanguageSwitcher.tsx.jinja — omit the file entirely when one locale #}
```

```yaml
_exclude:
  - |
    {% if locales | length < 2 %}
    /frontend/src/components/LanguageSwitcher.tsx
    {% endif %}
```

Do **not** rely on post-copy `rm` `_tasks` as the primary exclusion. Tasks run with the Consumer's user privileges and are platform-dependent; templated `_exclude` is the documented, declarative path. A task can be a belt-and-suspenders check in tests of the Generator, not in the Template.

Do **not** wrap file *contents* in `{% if 'pt-BR' in locales %}` and still emit empty files. Exclusion must drop the path.

Copier cannot loop "for locale in locales: emit locales/{{ locale }}/". Ship both trees in the Template and exclude. That is the supported model.

`.copier-answers.yml` will record `locales: [en]` (or both). Later `copier update` replays that answer, so a Consumer who generated English-only does not suddenly gain `pt-BR/` on update unless they change the answer.

## FastAPI

FastAPI does not document an i18n system. Locale is an application concern: read a header, pick a catalog, translate on the way out.

### `Accept-Language`

RFC 9110 §12.5.4: `Accept-Language = #( language-range [ weight ] )`, language ranges from RFC 4647. Example: `da, en-gb;q=0.8, en;q=0.7`. Matching schemes are RFC 4647's; HTTP previously used Basic Filtering. For "pick one catalog" the API should use **Lookup** (exactly one tag): exact match, then strip subtags (`pt-BR` ← `pt`), then `DEFAULT_LOCALE`. Never 406 for a missing language; RFC 9110 tells servers to serve a default rather than fail negotiation.

Read the header with FastAPI `Header`. Underscores in the parameter name become hyphens:

```python
accept_language: Annotated[str | None, Header()] = None
```

That yields `Accept-Language`. Do not hand-roll `request.headers.get("Accept-Language")` in some routes and `Header()` in others.

Parse `q=` weights. A naive `split(",")[0]` treats `pt;q=0.1, en;q=0.9` as Portuguese.

Match only against `SUPPORTED_LOCALES` (the Copier-rendered list). Unknown tags fall through to default.

**SPA is the authority for UI language.** The browser's raw `Accept-Language` is a first-visit hint inside the SPA detector, not something the API should prefer over an explicit header the SPA sets to `i18n.language`. Axios/fetch default:

```ts
headers: { "Accept-Language": i18n.language }
```

Starlette's `CORSMiddleware` always allows `Accept-Language` on CORS requests (it is a CORS-safelisted request header, with character restrictions). The SPA on Cloudflare Pages can send it to a different API host without a preflight caused by that header alone.

Optional: send `Content-Language: pt-BR` on translated JSON so caches and clients see the choice. RFC 9110 also allows `Vary: accept-language` on cacheable responses; the Generated API is mostly authenticated JSON, so `Vary` is optional in v1.

Do not use Babel `negotiate_locale` with default aliases. Empty `aliases={}` and `sep='-'`, or a ten-line Lookup, is safer.

### Errors

Two channels:

1. **Application errors** (`HTTPException`). FastAPI's handler returns `{"detail": exc.detail}`. Raise **codes**, translate in a custom `@app.exception_handler(HTTPException)` (or a thin subclass) using the request locale:

   ```python
   raise HTTPException(status_code=404, detail={"code": "errors.user_not_found"})
   ```

   Handler: `t(code, locale=request.state.locale)` → `{"detail": {"code": "...", "message": "Usuário não encontrado"}}`. Keep `code` stable for the SPA; translate `message` for humans. Do not translate by matching English sentences.

2. **Validation errors** (`RequestValidationError`). FastAPI's default handler dumps `exc.errors()` (Pydantic v2 `type`, `loc`, `msg`, `ctx`). Pydantic's own docs say a common reason to replace `msg` from `error['type']` is **translation**, and show a `CUSTOM_MESSAGES` map keyed by type (`missing`, `int_parsing`, `string_too_short`, …) with `{ctx}` interpolation.

   Override `@app.exception_handler(RequestValidationError)`: for each error, look up `errors.pydantic.{type}` in the JSON catalog for the request locale, `str.format(**ctx)` when `ctx` exists, leave `loc` untranslated (field names are schema, not copy).

   Do not depend on Pydantic's English `msg` string as a lookup key; those strings change across versions. The stable handle is `type`.

   `pydantic-i18n` exists but keeps a second translation dict keyed on English messages. Prefer the same `locales/*/errors.json` the SPA uses for form-side copies of the same types.

Wire locale onto the request in middleware or a `Depends` used by both handlers (`request.state.locale`). Middleware is enough; FastAPI's tutorial middleware is `@app.middleware("http")` / `app.add_middleware`.

### Transactional email copy

Emails are not `Accept-Language` problems. A Stripe webhook or a password-reset worker has no End-user browser. Persist `user.locale` (BCP 47 tag, constrained to `SUPPORTED_LOCALES`) at signup / first successful SPA session, and render with that.

Put subjects and bodies in `locales/<tag>/emails.json`:

```json
{
  "password_reset": {
    "subject": "Reset your password",
    "preheader": "This link expires in {{hours}} hours.",
    "body_text": "Hi {{name}}, …"
  }
}
```

HTML bodies can stay Jinja templates that call the same `t()` (pass it in the template context). Jinja's `jinja2.ext.i18n` `{% trans %}` is gettext-oriented (`install_gettext_callables`). It is the right tool **only if** catalogs are gettext. With shared JSON, do not enable `jinja2.ext.i18n`; pass `t` / `_` as a context function that hits the JSON loader. That keeps one catalog.

Local Mailpit vs prod SMTP is still fog on the wayfinder map; whichever sender is chosen, the copy path above does not change.

## Vite React SPA

ADR 0001: Vite React SPA, no SSR, prod on Cloudflare Pages. i18n must work entirely after JS loads.

### UI copy

- `i18next` + `react-i18next` + `i18next-browser-languagedetector`.
- `supportedLngs` = Copier-rendered list; `fallbackLng` = `DEFAULT_LOCALE`; `lng` unset so the detector runs (setting `lng` **overrides** detection).
- Bundle JSON at build time (`resources` on `init`, or `import.meta.glob('../locales/*/common.json')`). Do not add `i18next-http-backend` for v1; Pages should not have to host `/locales/{{lng}}/{{ns}}.json` as a second contract.
- `interpolation.escapeValue: false` (React escapes). Documented in the react-i18next step-by-step guide.
- `html lang` updates on `languageChanged` (`document.documentElement.lang = i18n.resolvedLanguage`).
- TypeScript: i18next's typed keys (`useTranslation`) are optional v1 polish; the JSON files remain the source of truth.

Detector (library defaults): `order: ['querystring', 'cookie', 'localStorage', 'sessionStorage', 'navigator', 'htmlTag']`. Caches in `localStorage` (`i18nextLng`) by default. Official FAQ: a cached language **wins** over a later `fallbackLng` or browser change. For a Generated app that is correct (End-user choice sticks). For first visit, `navigator` (the same list the browser would send as `Accept-Language`) picks `pt-BR` for a Brazilian browser when that locale was generated.

**Do not enable the `path` detector in v1** unless URL prefixes are adopted.

Switcher: `i18n.changeLanguage('pt-BR')`. That updates the cache. Copier omits the switcher component when `locales|length < 2`.

### Routing: `/en`, `/pt-BR` vs a switcher

| | Prefix routes (`/pt-BR/login`) | Switcher + detector (no prefix) |
|--|--|--|
| Shareable marketing URL | Yes | No (language is client state) |
| SEO / `hreflang` | Needs prerendered HTML per prefix | Same; SPA index.html is one document |
| Cloudflare Pages | Works: no top-level `404.html` → SPA mode serves `/` for unknown paths | Same |
| Copier English-only | Must also drop prefix routes and redirects | No route tree to rewrite |
| Authenticated app | Every dashboard link needs a localized `Link` | Irrelevant |
| First paint language | Still the bundled default until JS runs (no SSR) | Same |

**v1 recommendation: switcher, no locale prefix.**

Reasons that are specific to this Starter, not generic i18n lore:

1. The Generated app is a client-only SPA (ADR 0001). Prefixes without prerender do not produce locale-specific first HTML, which is the usual reason to pay for them.
2. Cloudflare Pages SPA rendering already maps unmatched paths to the root document. Prefixes are possible, but they add a React Router param and Copier conditionals for no SEO gain.
3. A Consumer who generates `--locales en` must not be left with `/pt-BR` routes, a `pt-BR` `<option>`, or a `supportedLngs` that lists a missing folder. A switcher gated on `locales|length > 1` is one conditional; a prefix tree is many.
4. i18next's path detector exists when a later map wants prefixes (marketing prerender, `hreflang`). Defer it. The detector `order` can gain `'path'` without changing catalogs.

If a later ticket adds landing-page prerender, revisit prefixes for the **public** surface only (`/`, `/pt-BR`), and keep the logged-in shell unprefixed.

### Talking to the API

Every API client attaches `Accept-Language: <i18n.language>`. Display API `detail.message` when present; fall back to SPA `errors.*` keys using `detail.code`. That way a translated API and a translated SPA cannot disagree on the code, only on whether the message arrived already translated.

## What the Generator must emit vs omit

| Artifact | Both locales | `--locales en` |
|----------|--------------|----------------|
| `locales/en/*.json` | yes | yes |
| `locales/pt-BR/*.json` | yes | **excluded** |
| `SUPPORTED_LOCALES` | `["en","pt-BR"]` | `["en"]` |
| Language switcher component | yes | **excluded** |
| Router `/en`, `/pt-BR` | not in v1 | not in v1 |
| `i18n.init` `supportedLngs` | both | `["en"]` |
| User.locale column / check constraint | both tags | `en` only |

Tests of the Generator (not of this research) should grep the English-only tree for `pt-BR` and fail if it appears in paths or in `supportedLngs`.

## Agent rules (keep catalogs in sync)

1. Add a key to **every shipped locale file** in the same namespace, same JSON shape. Do not add `en` only.
2. Keys are identifiers (`emails.password_reset.subject`), not sentences.
3. Interpolation placeholders must match (`{{name}}` in all locales). i18next and the Python loader both replace that syntax.
4. Plurals: `key_one` / `key_other` (JSON v4). Pass `count` from both JS `t()` and Python `t()`.
5. Never hard-code End-user copy in FastAPI `HTTPException(detail="...")` or in JSX text nodes.
6. Never introduce a second catalog format in a follow-up PR ("just a quick gettext" / "just a FormatJS message").

## Open items this research does not decide

- Exact directory names of the FastAPI app and Vite app inside the Template (blocked on [Research: uvx Typer Copier layout](https://github.com/DavillyDevTeam/davilly-starter/issues/2)). The shared `locales/` tree should sit next to both, not nested inside only one.
- Mailpit vs prod SMTP.
- Whether `user.locale` is editable in account settings (v1 can set it at signup and update it whenever the SPA switcher changes, via a `PATCH /me`).
- Prerender / `hreflang` for the marketing landing page.

## Sources

- Copier configuration: questions, `multiselect`, `validator`, `when`, answer priority, templated `_exclude` (including empty-block and newline-separated patterns), `_exclude` replacing defaults, gitignore pathspec, `--data` / `--data-file`, `run_copy(..., data=)` — <https://copier.readthedocs.io/en/stable/configuring/>, <https://copier.readthedocs.io/en/stable/generating/>, <https://copier.readthedocs.io/en/stable/reference/api/>
- Copier multiselect require-one validator — <https://github.com/orgs/copier-org/discussions/1694>
- Copier YAML-style list for `--data` on multiselect — <https://github.com/copier-org/copier/blob/master/docs/configuring.md> (question `data` section)
- FastAPI headers (`Header`, underscore → hyphen) — <https://fastapi.tiangolo.com/tutorial/header-params/>
- FastAPI middleware — <https://fastapi.tiangolo.com/tutorial/middleware/>
- FastAPI / Starlette exception handlers, `HTTPException.detail`, `RequestValidationError` — <https://fastapi.tiangolo.com/tutorial/handling-errors/>, <https://github.com/fastapi/fastapi/blob/master/fastapi/exception_handlers.py>
- Pydantic v2 `errors()` `type` / `msg` / `ctx`; official "customize / translate" pattern — <https://docs.pydantic.dev/latest/errors/errors/>
- RFC 9110 `Accept-Language`, language tags (RFC 5646), quality values, matching (RFC 4647), prefer default over 406, `Vary` — <https://www.rfc-editor.org/rfc/rfc9110.html#field.accept-language>
- RFC 4647 Lookup vs Filtering — <https://www.rfc-editor.org/rfc/rfc4647>
- MDN `Accept-Language` (BCP 47, `q`, CORS-safelisted) — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Language>
- Starlette `CORSMiddleware` always allows `Accept-Language` — <https://www.starlette.io/middleware/>
- Python `gettext`: global GNU API vs class-based API; `localedir/language/LC_MESSAGES/domain.mo`; do not `install()` from a library — <https://docs.python.org/3/library/gettext.html>
- Babel `Locale`, `negotiate_locale` (default `sep='_'`, `pt` → `pt_PT` aliases), `pybabel` catalog CLI — <https://babel.pocoo.org/en/stable/api/core.html>, <https://babel.pocoo.org/en/stable/locale.html>, <https://babel.pocoo.org/en/latest/cmdline.html>
- Jinja2 `jinja2.ext.i18n` (gettext/`{% trans %}`, `install_gettext_callables`) — <https://jinja.palletsprojects.com/en/stable/extensions/#i18n-extension>
- i18next JSON v4 — <https://www.i18next.com/misc/json-format>
- i18next `init` options (`lng` overrides detection, `supportedLngs`, `fallbackLng`, hyphenated codes) — <https://www.i18next.com/overview/configuration-options>, <https://www.i18next.com/how-to/faq>
- react-i18next setup, `useTranslation`, detector + backend install line — <https://react.i18next.com/getting-started>, <https://react.i18next.com/latest/using-with-hooks>
- `i18next-browser-languagedetector` order and `localStorage` cache — <https://github.com/i18next/i18next-browser-languageDetector/blob/master/README.md>
- Cloudflare Pages SPA rendering (no top-level `404.html` → serve `/` for unknown paths) — <https://developers.cloudflare.com/pages/configuration/serving-pages/>
- ADR 0001 (FastAPI + Vite SPA, no Next.js, Pages for the SPA) — `docs/adr/0001-fastapi-vite-generated-app.md`
- starlette-babel `LocaleMiddleware` selector order (query, cookie, user, Accept-Language, default) — <https://pypi.org/project/starlette-babel/> (rejected as gettext-based)
- fastapi-i18n (gettext + contextvar + `Accept-Language`) — <https://pypi.org/project/fastapi-i18n/> (rejected as gettext-based)
