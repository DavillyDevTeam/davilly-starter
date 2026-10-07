# Research: strict Python and TypeScript toolchains

Question from [Research: strict Python and TypeScript toolchains](https://github.com/DavillyDevTeam/davilly-starter/issues/16): the strictest *practical* configs for this Starter and its Generated app, from primary sources. Pin a Python type checker (ty vs basedpyright vs mypy `--strict`) against FastAPI / Pydantic / SQLAlchemy / fastapi-users. Pin TypeScript compiler flags that still work with Vite + React, and an ESLint `typescript-eslint` type-checked strict flat config. Pin Python and Node versions.

Already decided on the map ([Wayfinder: davilly-starter v1](https://github.com/DavillyDevTeam/davilly-starter/issues/1)): uv for every Python dependency operation; ruff for Python lint/format; pnpm for the SPA; TypeScript + ESLint type-checked strict + `tsc --noEmit` as the CI gate; Just as the root task runner of the Generated app; hard-rules of no `Any`/`any` escape, no ignore comments without an error code and a why, no `as` to silence the checker.

This note is a sketch for later Template implementation. Do not implement configs in the Template from this ticket.

Versions below are what the publishers reported on **2026-10-06**.

## Recommendation

Pin **basedpyright 1.40.x** as the Python type checker for this Starter and the Generated app. Mode `typeCheckingMode = "recommended"` (basedpyright’s default: every diagnostic on, `failOnWarnings = true`) plus hard-rule overlays `reportExplicitAny = "error"` and `reportIgnoreCommentWithoutRule = "error"`. Pair it with ruff `ANN` (including [ANN401](https://docs.astral.sh/ruff/rules/any-type/)) + `PYI` + `PGH`.

Leave **ty** for a later revisit: it is 0.0.x beta, its own version policy says diagnostics may change between any two versions, it has no missing-annotation rule, and it has no pydantic / SQLAlchemy plugins (first-party support is only “considering”). Leave **mypy `--strict`** as a second checker at most; it is slower, treats untyped imports as `Any` without basedpyright’s `reportAny`/`reportExplicitAny` split, and is not the map’s intended shortlist.

Pin **Python 3.14** (`.python-version` + `requires-python = ">=3.14"`) and **Node.js 24** (`engines.node = ">=24 <25"`). SPA: **pnpm 12.9.1**, **TypeScript ~6.0.2**, **ESLint 10.x**, **typescript-eslint 8.71.x** with `strictTypeChecked` + `stylisticTypeChecked`, `parserOptions.projectService: true`, `@typescript-eslint/consistent-type-assertions` `assertionStyle: "never"`. CI gate: `tsc --noEmit` (Vite transpiles only).

fastapi-users **15.0.5** ships `py.typed`. It uses `Any` in library internals (`makefun` `*args: Any, **kwargs: Any`; `decode_jwt` → `dict[str, Any]`). That does **not** force *our* code to write `Any`. Wrap JWT payloads in a `TypedDict` at the boundary. Do not add `fastapi-users` to `allowedUntypedLibraries`.

## Pins (2026-10-06)

| Tool | Pin | Source |
|------|-----|--------|
| Python | **3.14** (`.python-version` = `3.14`, `requires-python = ">=3.14"`) | Latest bugfix is 3.14.8 ([Python Insider 2026-10-01](https://blog.python.org/2026/10/python-31022-31117/); [PEP 745](https://peps.python.org/pep-0745/)). Security fixes until ~October 2030. FastAPI 0.142.2, Pydantic 2.13.5, SQLAlchemy 2.1.3, fastapi-users 15.0.5, Typer 0.27.3 all classify 3.14. SQLAlchemy requires `>=3.11`. |
| uv | **0.12.x** (0.12.23 on PyPI) | Already decided. [Python version files](https://docs.astral.sh/uv/concepts/python-versions/#python-version-files); [PEP 735 dependency-groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies). |
| ruff | **0.16.x** (0.16.10) | [Ruff](https://docs.astral.sh/ruff/). |
| basedpyright | **1.40.x** (1.40.2) | [PyPI basedpyright](https://pypi.org/project/basedpyright/). Classifiers include 3.14. |
| ty (not pinned) | 0.0.85 beta | [PyPI ty](https://pypi.org/project/ty/); [version policy](https://github.com/astral-sh/ty/blob/0.0.85/README.md). |
| mypy (not pinned) | 2.4.0 | [`--strict` flag list](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict). |
| Node.js | **24** Active LTS “Krypton” | [nodejs/Release schedule](https://github.com/nodejs/Release): Active LTS 2025-10-28 → Maintenance 2026-10-20 → EOL 2028-04-30. Node 26 is Current until 2026-10-28. Production apps use Active/Maintenance LTS. create-vite pins `@types/node ^24.19.0`. |
| pnpm | **12.9.1** | npm dist-tag `latest` = 12.9.1; `next-12` = 12.10.1. Pin the `latest` tag. |
| TypeScript | **~6.0.2** (resolves 6.0.3) | [create-vite `template-react-ts` package.json](https://github.com/vitejs/vite/blob/main/packages/create-vite/template-react-ts/package.json). typescript-eslint 8.71.1 peer is `typescript >=4.8.4 <6.1.0`. npm `latest` is 7.0.2, which is outside that peer range. |
| ESLint | **10.x** (10.12.0) | ESLint v9 reached EOL on 2026-08-06 ([eslint.org banner](https://eslint.org/docs/latest/use/migrate-to-10.0.0)). |
| typescript-eslint | **8.71.x** (8.71.1) | [Shared configs](https://typescript-eslint.io/users/configs/); [typed linting](https://typescript-eslint.io/getting-started/typed-linting). |
| Vite | **^8.3.1** | Official template. |
| React | **^19.3.0** | Official template. |
| just | **1.58.x** (1.58.0) | [casey/just releases](https://github.com/casey/just/releases). |

## Python type checker

### Comparison

| | **basedpyright 1.40.2** | **ty 0.0.85** | **mypy 2.4.0 `--strict`** |
|---|---|---|---|
| Status | Stable fork of pyright. Default `typeCheckingMode = "recommended"`. | Beta. `0.0.x`; “breaking changes, including changes to diagnostics, may occur between any two versions.” ([ty README version policy](https://github.com/astral-sh/ty/blob/0.0.85/README.md)) | Stable. `--strict` flag set can change between releases. ([mypy CLI](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)) |
| Hard-rule: no writing `Any` | Exclusive `reportExplicitAny`. Warning in `recommended`, error in `all`. | No dedicated “ban the `Any` annotation” rule. | `--disallow-any-explicit` exists; **not** in the `--strict` set. `--strict` enables `--disallow-any-generics` and `--disallow-subclassing-any` only. |
| Hard-rule: ignore comments need a code | Exclusive `reportIgnoreCommentWithoutRule`. `enableTypeIgnoreComments` is **false** in `recommended`/`all` (prefer `# pyright: ignore[reportXyz]`). | `# ty: ignore[rule]` recommended; codes optional. `blanket-ignore-comment` is off by default (ty’s “even stricter” sketch turns it on). | `--warn-unused-ignores` is in `--strict`. Blanket `# type: ignore` still works unless ruff PGH003 is on. |
| Missing annotations | `reportMissingParameterType` / `reportUnknownParameterType` on in `recommended`. | **No rule.** FAQ: use ruff ANN. ([Why doesn’t ty warn about missing type annotations?](https://docs.astral.sh/ty/reference/typing-faq/#why-doesnt-ty-warn-about-missing-type-annotations)) | `--disallow-untyped-defs` + `--disallow-incomplete-defs` in `--strict`. |
| Using an `Any` expression | Exclusive `reportAny` (Unknown vs explicit `Any` split). Warning in `recommended`. | Gradual `Unknown`; default is already strict on many checks. | `--disallow-any-expr` exists; **not** in `--strict`. |
| FastAPI / Pydantic / SQLAlchemy | Pyright-family; Pydantic v2 `dataclass_transform` and SQLAlchemy 2.x `Mapped[]` work without plugins. Auto-detects `./.venv` (uv’s default). ([better defaults](https://docs.basedpyright.com/latest/benefits-over-pyright/better-defaults/)) | No plugin system; “considering adding support for pydantic, SQLAlchemy, attrs, or django directly.” ([Does ty support (mypy) plugins?](https://docs.astral.sh/ty/reference/typing-faq/#does-ty-support-mypy-plugins)) | Needs `pydantic.mypy` / SQLAlchemy mypy plugin for older patterns; SQLAlchemy 2.0 `Mapped[]` is plugin-free. |
| CI | `failOnWarnings` true in `recommended` → warnings fail the CLI. | `ty check`; `--error=all` is documented as too noisy. | `mypy --strict`. |
| Speed | Node-based; fine for a starter-sized tree. | 10–100× vs mypy/pyright (Astral claim). | Slowest of the three. |

ty’s own “approximate `--strict`” config is four extra rules plus ruff `ANN`+`PYI`. Its “even stricter” sketch adds `blanket-ignore-comment`, `unsound-*`, and `strict-equality-semantics`, and warns that `possibly-missing-attribute` / `possibly-missing-import` have many false positives. ([Coming from mypy or pyright](https://docs.astral.sh/ty/coming-from-mypy-or-pyright/#stricter-checking-with-ty))

basedpyright `recommended` already enables every diagnostic as warning or error and fails the CLI on warnings. `all` promotes the remaining warnings to error. `reportAny` as error (`all`) reports every *use* of a value typed `Any`, including values that leak out of fastapi-users. That is why this pin is `recommended` plus `reportExplicitAny = "error"`: our code cannot *write* `Any`; uses of library `Any` still fail CI as warnings until wrapped.

### fastapi-users and `Any`

fastapi-users 15.0.5 requires Python `>=3.10`, classifies 3.14, and ships [`fastapi_users/py.typed`](https://github.com/fastapi-users/fastapi-users/blob/master/fastapi_users/py.typed). It is a PEP 561 typed package. Do not list it in `allowedUntypedLibraries`.

`Any` in *its* sources:

- [`authentication/authenticator.py`](https://github.com/fastapi-users/fastapi-users/blob/master/fastapi_users/authentication/authenticator.py): `from typing import Any, Generic, cast`. `current_user_token_dependency(*args: Any, **kwargs: Any)` / `current_user_dependency(*args: Any, **kwargs: Any)` because [makefun `with_signature`](https://github.com/fastapi-users/fastapi-users/blob/master/fastapi_users/authentication/authenticator.py) builds a dynamic FastAPI dependency. `cast(Callable, backend.transport.scheme)` for OpenAPI.
- [`jwt.py`](https://github.com/fastapi-users/fastapi-users/blob/master/fastapi_users/jwt.py): `decode_jwt(...) -> dict[str, Any]` around PyJWT.

Those annotations live in site-packages. basedpyright does not type-check that tree. `reportAny` fires when *our* code uses an expression typed `Any` — typically the JWT dict.

Stay honest:

1. Never annotate our functions with `Any`. `reportExplicitAny = "error"` plus ruff ANN401 enforce this.
2. Wrap `decode_jwt` at the boundary:

```python
from typing import TypedDict

class AccessTokenPayload(TypedDict):
    sub: str
    aud: list[str]
    exp: int

def read_access_token(encoded: str, secret: str, audience: list[str]) -> AccessTokenPayload:
    raw = decode_jwt(encoded, secret, audience)
    return {
        "sub": str(raw["sub"]),
        "aud": list(raw["aud"]),
        "exp": int(raw["exp"]),
    }
```

3. `current_user(active=True)` returns the native ORM `User`. Depend on that; do not re-type the makefun wrapper.
4. A `# pyright: ignore[reportAny]  # PyJWT payload is dict[str, Any]; narrowed on the next line` is allowed only with a code and a why. `enableTypeIgnoreComments` is already false in `recommended`, so `# type: ignore` is inactive.

### Practical basedpyright + ruff

```toml
[tool.basedpyright]
pythonVersion = "3.14"
pythonPlatform = "All"
typeCheckingMode = "recommended"
# failOnWarnings is already true in recommended
reportExplicitAny = "error"
reportIgnoreCommentWithoutRule = "error"
# reportAny stays "warning" (CI-fail via failOnWarnings). Wrap library Any at the boundary.

[tool.ruff]
target-version = "py314"
src = ["src"]

[tool.ruff.lint]
select = [
  "E", "F", "W",   # pycodestyle + pyflakes
  "I",             # isort
  "UP",            # pyupgrade
  "B",             # bugbear
  "ANN",           # flake8-annotations, includes ANN401 (Any)
  "PYI",           # flake8-pyi
  "PGH",           # PGH003 blanket-type-ignore
  "RUF",
  "ASYNC",
]
preview = true     # ty’s coming-from guide: PYI033 also on .py files
# None of the formatter-conflicting rules (W191, E111, COM812, Q000, …)
# are in this select list. ([Conflicting lint rules](https://docs.astral.sh/ruff/formatter/#conflicting-lint-rules))

[tool.ruff.format]
docstring-code-format = true
```

ruff is the formatter. `ruff format --check` in CI. Default quote/indent (Black-compatible).

Dev deps via PEP 735, installed with `uv add --dev`:

```toml
[dependency-groups]
dev = [
  "basedpyright>=1.40.2,<1.41",
  "ruff>=0.16.10,<0.17",
]
```

([uv development dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies))

Revisit ty when it leaves `0.0.x` (Astral [Stable milestone](https://github.com/astral-sh/ty/milestone/4)) and documents pydantic / SQLAlchemy support.

## TypeScript + Vite + React

Vite transpiles `.ts` / `.tsx` and **does not type-check**. The docs tell you to run `tsc --noEmit` in production builds and (optionally) `--watch` in dev. ([Vite: TypeScript — Transpile Only](https://vite.dev/guide/features.html#transpile-only))

Official [create-vite `template-react-ts`](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) (Vite 8.3) layout:

- `tsconfig.json` — solution-style, `files: []`, project references to app + node.
- `tsconfig.app.json` — SPA (`include: ["src"]`), `moduleResolution: "bundler"`.
- `tsconfig.node.json` — `vite.config.ts`, `module: "nodenext"`, `types: ["node"]`.

Required-for-Vite flags (already in the template / [Vite compiler options](https://vite.dev/guide/features.html#typescript-compiler-options)):

| Flag | Value | Why |
|------|-------|-----|
| `isolatedModules` | implied by `verbatimModuleSyntax` | Oxc transpiles per-file. Vite: “Should be set to `true`.” |
| `verbatimModuleSyntax` | `true` | Type-only imports must use `import type`. Template sets it. |
| `moduleResolution` | `"bundler"` (app) / `"nodenext"` (node) | App is bundled; `vite.config.ts` is Node. |
| `allowImportingTsExtensions` | `true` | Bundler mode. |
| `noEmit` | `true` | `tsc` is a checker; Vite emits. |
| `jsx` | `"react-jsx"` | React 17+ automatic runtime. |
| `skipLibCheck` | `true` | Vite templates set this so dependency `.d.ts` files do not fail the app. |
| `erasableSyntaxOnly` | `true` | Template; bans runtime-emit syntax (parameter properties, enums without `erasable`). |
| `moduleDetection` | `"force"` | Template. |
| `types` | `["vite/client"]` (app) / `["node"]` (node) | Vite client shims; do not also pull every `@types/*` into the SPA. |

The official template’s “Linting” block is only `noUnusedLocals`, `noUnusedParameters`, `erasableSyntaxOnly`, `noFallthroughCasesInSwitch`. It does **not** set `"strict": true` (it did in create-vite 5.x). [`@tsconfig/vite-react` 8.1.1](https://github.com/tsconfig/bases/blob/main/bases/vite-react.json) matches that template and also omits `strict`.

Add the full [`@tsconfig/strictest`](https://github.com/tsconfig/bases/blob/main/bases/strictest.json) extra set on top of the Vite bundler flags:

| Flag | Value |
|------|-------|
| `strict` | `true` (includes `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `alwaysStrict`, `useUnknownInCatchVariables`) |
| `noUncheckedIndexedAccess` | `true` |
| `exactOptionalPropertyTypes` | `true` |
| `noPropertyAccessFromIndexSignature` | `true` |
| `noImplicitOverride` | `true` |
| `noImplicitReturns` | `true` |
| `allowUnusedLabels` | `false` |
| `allowUnreachableCode` | `false` |
| `noUnusedLocals` | `true` (already in template) |
| `noUnusedParameters` | `true` (already in template) |
| `noFallthroughCasesInSwitch` | `true` (already in template) |

These are type-checking-only. They do not change Vite’s emit. `exactOptionalPropertyTypes` plus `noUncheckedIndexedAccess` are the two that bite React props (`foo?: T` is not `{ foo: T | undefined }`; `obj[key]` is `T | undefined`). That is the intended strictness.

`target` / `lib`: template uses `es2023`. Vite **ignores** `tsconfig.target` for emit ([Vite: target](https://vite.dev/guide/features.html#target)). Keep `es2023` for `tsc`’s idea of the standard library.

TypeScript **7.0.2** is npm `latest`. typescript-eslint 8.71.1 declares `typescript: ">=4.8.4 <6.1.0"`. Stay on the 6.0 line (`~6.0.2` → 6.0.3) until typescript-eslint raises the peer. create-vite already pins `~6.0.2`.

create-vite’s `lint` script is now `oxlint`. The ticket requires ESLint `typescript-eslint` type-checked strict; use ESLint.

## ESLint typescript-eslint type-checked strict (flat config)

[Typed linting](https://typescript-eslint.io/getting-started/typed-linting): add `TypeChecked` to the preset name and set `languageOptions.parserOptions.projectService: true`. [Shared configs](https://typescript-eslint.io/users/configs/) say a proficient TypeScript project should replace `recommendedTypeChecked` with `strictTypeChecked`. `strictTypeChecked` is not semver-stable (rules may move outside majors); that is acceptable for a generated app we control.

Hard-rule overlays:

- `@typescript-eslint/no-explicit-any` and `no-unsafe-*` come with `strictTypeChecked`.
- `@typescript-eslint/consistent-type-assertions`: `{ assertionStyle: "never" }` — bans `value as T` and `<T>value`. `as const` stays allowed. ([consistent-type-assertions](https://typescript-eslint.io/rules/consistent-type-assertions/))
- `@typescript-eslint/ban-ts-comment`: `strict` already requires a description of length ≥ 10 on `@ts-expect-error` and reports `@ts-ignore` / `@ts-nocheck`. Tighten `ts-expect-error` to require a TS error code in the description. ([ban-ts-comment](https://typescript-eslint.io/rules/ban-ts-comment/))

`parserOptions.projectService: true` uses the same `tsconfig.json` the editor uses; no `tsconfig.eslint.json`. `allowDefaultProject` covers root `eslint.config.js`.

React 19: `eslint-plugin-react-hooks` 7.1.1 (plugin-react’s old `jsx-runtime` preset is largely redundant with `jsx: react-jsx`).

## Copy-pasteable sketches

Layout assumption for the Generated app (implementation ticket picks names): Python package at repo root (`src/<pkg>/`), SPA in `frontend/`. This Starter is Python-only.

### (a) this Starter (Typer + Copier CLI)

`.python-version`

```text
3.14
```

`pyproject.toml` (toolchain tables only)

```toml
[project]
name = "davilly-starter"
requires-python = ">=3.14"
dependencies = [
  "typer>=0.27",
  "copier",
]

[dependency-groups]
dev = [
  "basedpyright>=1.40.2,<1.41",
  "ruff>=0.16.10,<0.17",
  "pytest>=8",
]

[tool.basedpyright]
pythonVersion = "3.14"
pythonPlatform = "All"
typeCheckingMode = "recommended"
reportExplicitAny = "error"
reportIgnoreCommentWithoutRule = "error"

[tool.ruff]
target-version = "py314"
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "ANN", "PYI", "PGH", "RUF", "ASYNC"]
preview = true

[tool.ruff.format]
docstring-code-format = true
```

`justfile` (optional here; required on the Generated app per ADR 0002)

```just
set dotenv-load := false

lint:
    uv run ruff check .
    uv run ruff format --check .

typecheck:
    uv run basedpyright

test:
    uv run pytest

ci: lint typecheck test
```

No `tsconfig`, ESLint, or pnpm on this Starter.

### (b) Generated app (FastAPI API + Vite React SPA)

Root `.python-version`: `3.14`. Root `package.json` is absent; SPA lives in `frontend/` with its own `package.json`. Root `justfile` shells out to uv and pnpm.

Root `pyproject.toml` (API package)

```toml
[project]
name = "{{ project_slug }}"
requires-python = ">=3.14"
dependencies = [
  "fastapi>=0.142",
  "pydantic>=2.13",
  "sqlalchemy>=2.1",
  "fastapi-users[sqlalchemy]>=15.0.5",
]

[dependency-groups]
dev = [
  "basedpyright>=1.40.2,<1.41",
  "ruff>=0.16.10,<0.17",
  "pytest>=8",
  "httpx>=0.28",
]

[tool.basedpyright]
pythonVersion = "3.14"
pythonPlatform = "All"
typeCheckingMode = "recommended"
reportExplicitAny = "error"
reportIgnoreCommentWithoutRule = "error"
# Do not set allowedUntypedLibraries = ["fastapi_users"]

[tool.ruff]
target-version = "py314"
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "ANN", "PYI", "PGH", "RUF", "ASYNC"]
preview = true

[tool.ruff.format]
docstring-code-format = true
```

Root `justfile`

```just
set dotenv-load := false

frontend := "frontend"

dev:
    # implementation ticket: run uvicorn + `pnpm --dir {{frontend}} dev` together

lint:
    uv run ruff check .
    uv run ruff format --check .
    pnpm --dir {{frontend}} lint

typecheck:
    uv run basedpyright
    pnpm --dir {{frontend}} typecheck

test:
    uv run pytest
    pnpm --dir {{frontend}} test

ci: lint typecheck test
```

`frontend/package.json` (scripts + pins)

```json
{
  "name": "{{ project_slug }}-web",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@12.9.1",
  "engines": {
    "node": ">=24 <25",
    "pnpm": ">=12.9.1 <13"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit -b",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^19.3.0",
    "react-dom": "^19.3.0"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.0",
    "@types/node": "^24.19.0",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.1.1",
    "eslint": "^10.12.0",
    "eslint-plugin-react-hooks": "^7.1.1",
    "typescript": "~6.0.2",
    "typescript-eslint": "^8.71.1",
    "vite": "^8.3.1"
  }
}
```

`frontend/tsconfig.json`

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

`frontend/tsconfig.app.json`

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023", "DOM"],
    "module": "esnext",
    "types": ["vite/client"],
    "allowArbitraryExtensions": true,
    "skipLibCheck": true,

    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "allowUnusedLabels": false,
    "allowUnreachableCode": false,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

`frontend/tsconfig.node.json`

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023"],
    "types": ["node"],
    "skipLibCheck": true,
    "module": "nodenext",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "allowUnusedLabels": false,
    "allowUnreachableCode": false,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

`frontend/eslint.config.js`

```js
// @ts-check
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["dist/**", "node_modules/**"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.strictTypeChecked,
      tseslint.configs.stylisticTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "@typescript-eslint/consistent-type-assertions": [
        "error",
        { assertionStyle: "never" },
      ],
      "@typescript-eslint/ban-ts-comment": [
        "error",
        {
          "ts-expect-error": "allow-with-description",
          "ts-ignore": true,
          "ts-nocheck": true,
          "ts-check": false,
          minimumDescriptionLength: 10,
        },
      ],
    },
  },
  {
    files: ["**/*.js"],
    extends: [tseslint.configs.disableTypeChecked],
  },
);
```

CI (both trees): `just ci`. That is `ruff check` + `ruff format --check` + `basedpyright` + `eslint` + `tsc --noEmit -b` + tests. Vite `build` already runs `tsc -b` in the official template’s `build` script; keep that so a production image never ships unchecked JS.

## Hard-rules → config

| Hard-rule | Python | TypeScript |
|-----------|--------|------------|
| No `Any`/`any` escape | `reportExplicitAny = "error"` + ruff ANN401. `reportAny` warning (CI-fail) on *uses* of library `Any`; wrap at the boundary. | `@typescript-eslint/no-explicit-any` + `no-unsafe-*` via `strictTypeChecked`. |
| Ignore comments need a code + why | `enableTypeIgnoreComments` false in `recommended`. `# pyright: ignore[reportXyz]  # why`. ruff PGH003 bans blanket `# type: ignore`. | `@typescript-eslint/ban-ts-comment`: `@ts-expect-error` with ≥10-char description (include the TS error code); `@ts-ignore` / `@ts-nocheck` forbidden. |
| No `as` to silence the checker | n/a (Python `cast()` is `reportInvalidCast` in recommended — overlapping casts only). | `consistent-type-assertions` `assertionStyle: "never"`. `as const` remains allowed. |

Agents fix types. A suppression is a last resort and always carries a code plus a one-line why.

## What this ticket does not decide

- Directory names inside the Generated app (`frontend/` vs `web/`).
- Test runners (pytest layout, vitest vs node:test).
- Whether the Starter itself gets a `justfile` (ADR 0002 requires Just on the Generated app).
- Bumping to Node 26 after it enters LTS (scheduled 2026-10-28) or to TypeScript 7 once typescript-eslint allows it.
- Switching the Python checker to ty after a non-`0.0.x` release.
