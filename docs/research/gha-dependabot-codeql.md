# Research: GitHub Actions, Dependabot, CodeQL

Question from [Research: GitHub Actions Dependabot CodeQL](https://github.com/DavillyDevTeam/davilly-starter/issues/17): how to set up GitHub Actions CI/CD and GitHub security features for (a) this Starter and (b) every Generated app (workflow files shipped in the Template).

**Already decided (map):** GitHub, not GitLab. Dependabot + CodeQL on both. uv in Python CI, pnpm in JS CI. Strict lint + typecheck fail the build. Public repo. Least-privilege workflow permissions. Starter may smoke-test by generating into a temp dir and running the Generated app’s `just ci` without Stripe/OAuth secrets.

This note is for [Task: CI and GitHub security on the starter](https://github.com/DavillyDevTeam/davilly-starter/issues/21) and [Task: Workspace CI and security in the generated app](https://github.com/DavillyDevTeam/davilly-starter/issues/20). Do **not** add workflows from this ticket. Python/Node pins and `just` recipes come from [Research: strict Python and TypeScript toolchains](https://github.com/DavillyDevTeam/davilly-starter/issues/16). Generator CLI flags come from [Research: uvx Typer Copier layout](https://github.com/DavillyDevTeam/davilly-starter/issues/2).

## Recommendation

Two workflow files plus one Dependabot config, same shape on both sides.

| File | Starter | Generated app (Template) |
|------|---------|--------------------------|
| `.github/workflows/ci.yml` | uv lint + typecheck + test; after the Template exists, generate into `$RUNNER_TEMP` and run that tree’s `just ci` | `just ci` (lint, typecheck, test, SPA build) |
| `.github/workflows/codeql.yml` | advanced CodeQL: `python`, `javascript-typescript`, `actions` | same languages |
| `.github/dependabot.yml` | `uv` + `github-actions` (+ Template lockfile directories once they exist) | `uv` + `npm` (pnpm) + `github-actions` + `docker` + `docker-compose` |

Do **not** enable CodeQL default setup on a repo that already ships `codeql.yml`. Default setup and a CodeQL SARIF upload fight each other. ([Upload rejected because default setup is enabled](https://docs.github.com/en/code-security/code-scanning/troubleshooting-sarif-uploads/default-setup-enabled))

Pin every `uses:` to a **full-length commit SHA** with a same-line `# vX.Y.Z` comment. Let Dependabot’s `github-actions` ecosystem move the SHA and the comment together. ([Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use); [GitHub Actions ecosystem](https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories#github-actions))

Group Dependabot **minor + patch** per ecosystem; leave majors as individual PRs so strangers are not flooded but still see breaking bumps. Weekly schedule. ([Optimizing Dependabot PRs](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/optimizing-pr-creation-version-updates#example-3-individual-pull-requests-for-major-updates-and-grouped-for-minorpatch-updates))

Secret scanning already runs on public GitHub.com repos. No workflow for it. ([Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning))

## Minimal workflow set

Workflows live in `.github/workflows` as YAML. ([Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax))

### (a) this Starter — two files

1. **`ci.yml`** — one job until the Template exists; two jobs after.
   - `check`: `uv sync --locked --all-extras --dev`, then lint, typecheck, test. Fail the job on any of those. uv’s own GitHub guide is this sequence. ([Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/#syncing-and-running))
   - `smoke` (after [Task: Scaffold generator landing boot](https://github.com/DavillyDevTeam/davilly-starter/issues/8)): generate into `$RUNNER_TEMP`, run the Generated app’s `just ci`. Issue 21 already says prefer waiting on scaffold over a green CI that never generates.

2. **`codeql.yml`** — GitHub’s advanced-setup template, languages listed below.

Do **not** add a PyPI publish workflow here. Publishing is [Task: Publish davilly-starter to PyPI](https://github.com/DavillyDevTeam/davilly-starter/issues/13). uv’s own release example splits `build` (`contents: read`) from `publish` (`id-token: write`) so the credential never shares a job with install/test. ([Using uv in GitHub Actions — Publishing](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi))

### (b) Generated app — two files, shipped in the Template

1. **`ci.yml`** — one job: install uv + pnpm + `just`, lockfile-sync, then `just ci`. `just ci` is the Consumer-facing gate (ADR 0002: `dev`, `lint`, `typecheck`, `test`, `ci`). Include SPA **build** inside `just ci` (or as a recipe `just ci` calls). That is the v1-sized extra the ticket asked about: Vite must actually emit `dist/`, not only typecheck.

2. **`codeql.yml`** — same advanced-setup file as the Starter, with Template paths already expanded (no Copier jinja left).

A third workflow (Pages deploy, Docker publish) is **not** v1 CI. Prod deploy docs are a different ticket.

Do **not** run `docker compose up` in GitHub Actions for v1. Compose is the local boot bar (map Notes). GHA Compose would pull images, need secrets, and burn minutes without gating lint/types. API tests that need Postgres can use a [service container](https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/creating-postgresql-service-containers) later; that is optional extra, not the minimum.

### Triggers (both)

```yaml
on:
  push:
    branches: [main]
  pull_request:
  merge_group:
```

CodeQL also takes a weekly `schedule` cron so alerts appear even when nobody is pushing. GitHub’s starter workflow does push + pull_request + weekly cron. ([Workflow configuration options for code scanning](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options#scan-frequency); [actions/starter-workflows codeql.yml](https://github.com/actions/starter-workflows/blob/main/code-scanning/codeql.yml))

Use `pull_request`, **not** `pull_request_target`. The latter is privileged and is the classic untrusted-checkout footgun. ([Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use#mitigating-the-risks-of-untrusted-code-checkout))

`merge_group` is required if the repo later turns on a merge queue; cheap to include now. ([Workflow configuration options](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options#scanning-pull-requests))

Cancel in-progress PR runs:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

`concurrency` ensures one run per group; `cancel-in-progress: true` (or an expression) cancels the previous one. Do not cancel `main` mid-push. ([Workflow syntax — concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency))

## Starter `ci.yml` shape

uv’s documented GitHub Actions path: `astral-sh/setup-uv`, then `uv python install` **or** `python-version:` on the action, then `uv sync --locked --all-extras --dev`, then `uv run …`. Pin the **uv tool** version (`version:` input, or `required-version` in `pyproject.toml` / `uv.toml` — setup-uv reads those). Pinning the action SHA is not the same as pinning uv. ([Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/); [setup-uv](https://github.com/astral-sh/setup-uv))

`setup-uv` `enable-cache` defaults to `auto` (on for GitHub-hosted runners except release/tag/`pull_request_target`/`workflow_run`). Leave it. If you manage the cache yourself, run `uv cache prune --ci` before save. ([setup-uv inputs](https://github.com/astral-sh/setup-uv); [uv cache prune --ci](https://docs.astral.sh/uv/guides/integration/github/#caching))

Do **not** add `actions/setup-python` unless you want the ~1s runner-image Python. setup-uv can install Python. uv’s guide still shows both. ([setup-uv FAQ](https://github.com/astral-sh/setup-uv))

Sketch (SHAs are examples from uv’s guide at research time; the implementation ticket resolves current SHAs):

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
  merge_group:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-sha> # v7.x
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@<full-sha> # v10.x
        with:
          enable-cache: true
          # python-version / version: from toolchain research
      - run: uv sync --locked --all-extras --dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run <typechecker>  # ty or basedpyright, from #16
      - run: uv run pytest
```

Exact lint/typecheck binaries are #16. The rule here is: they run, and a non-zero exit fails the job.

## Generated-app `ci.yml` shape

Needs **three** tools: uv (API), pnpm (SPA), `just` (root). ADR 0002: Just is the Consumer-facing surface.

**pnpm.** Official GitHub Actions recipe is now `pnpm/setup` (not `pnpm/action-setup` + `actions/setup-node`). It installs pnpm from the npm registry, installs Node via `pnpm runtime set`, and runs `pnpm install` unless `install: false`. pnpm version comes from `packageManager` or `devEngines.packageManager` in `package.json`, so the workflow does not pin pnpm twice. Set `cache: true` and `require-lockfile: true` (fails if `pnpm-lock.yaml` is missing; runs `--frozen-lockfile` when present). When the SPA is not at repo root, pass `working-directory:`. ([pnpm Continuous Integration](https://pnpm.io/continuous-integration#github-actions); [pnpm/setup](https://github.com/pnpm/setup))

In CI, pnpm already switches to frozen-lockfile mode because `CI` is set. A **missing** lockfile would still resolve from the registry and exit 0; `require-lockfile: true` is what makes that a failure. ([pnpm CI — lockfile behavior](https://pnpm.io/continuous-integration); [pnpm/setup — require-lockfile](https://github.com/pnpm/setup))

Corepack is no longer the documented GitHub Actions path. ([pnpm CI — Installing pnpm](https://pnpm.io/continuous-integration#installing-pnpm))

**just.** Official cross-platform install via uv: `uv tool install rust-just`. That avoids a third-party `setup-just` action. ([just packages](https://just.systems/man/en/packages.html))

**uv.** Same as the Starter, pointed at the FastAPI package directory if it is not `/`.

Sketch:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
  merge_group:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-sha> # v7.x
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@<full-sha> # v10.x
        with:
          enable-cache: true
      - run: uv tool install rust-just
      - uses: pnpm/setup@<full-sha> # v2.x / v3.x
        with:
          runtime: node@<from-#16>
          cache: true
          require-lockfile: true
          working-directory: <spa-dir>   # omit if SPA is repo root
          install: false                 # just ci / explicit install owns this
      - run: uv sync --locked --all-extras --dev
      - run: pnpm install --dir <spa-dir>   # CI already frozen; keep lockfile committed
      - run: just ci
```

If `pnpm/setup` `install: true` (the default) and the SPA **is** the working directory, drop the explicit `pnpm install`. If Just’s `ci` recipe runs `uv sync` / `pnpm install` itself, keep the workflow install anyway so a missing lockfile fails before Just, and so caches populate.

`just ci` must include:

| Gate | Tool |
|------|------|
| Python lint/format | ruff (uv) |
| Python typecheck | whatever #16 pins |
| Python tests | pytest (uv) |
| SPA lint | ESLint type-checked strict |
| SPA typecheck | `tsc --noEmit` |
| SPA tests | vitest or equivalent |
| SPA build | `pnpm build` / Vite |

No Stripe, no OAuth env. See smoke-test.

Optional Postgres service (not minimum):

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app
    ports: ["5432:5432"]
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

Only add this when API tests actually open a DB. Do not invent a Compose stack in GHA.

## Smoke-test shape for the Generator

After the Template exists, Starter CI generates a throwaway app and runs **its** `just ci`. That is the only way Starter CI proves the Template still works.

```yaml
  smoke:
    needs: check
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<full-sha> # v7.x
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@<full-sha> # v10.x
        with:
          enable-cache: true
      - uses: pnpm/setup@<full-sha>
        with:
          runtime: node@<from-#16>
          cache: true
          install: false
      - run: uv tool install rust-just
      - run: uv sync --locked --all-extras --dev
      - name: Generate into temp and run just ci
        env:
          # Intentionally empty: no STRIPE_*, no OAUTH_*, no REDIS_URL
          CI: true
        run: |
          set -euo pipefail
          DEST="${RUNNER_TEMP}/smoke-app"
          # Non-interactive flags: from #2 (Copier --defaults / Typer options).
          uv run davilly-starter new "$DEST" --defaults
          cd "$DEST"
          just ci
```

Constraints that the Template / Generated-app tests must honour (issue 20 already states this):

- `just ci` exits 0 with **no** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`, Google/GitHub OAuth client ids/secrets, or `REDIS_URL`.
- Auth/Stripe tests `skip` (pytest `skipif`, vitest `skip`) when those env vars are unset. Do **not** inject dummy `sk_test_` values in Starter CI — that would exercise a fake Stripe path and could trip secret scanning.
- Email/password JWT still works; Redis blacklist is off when `REDIS_URL` is unset (map Notes).
- Copier must be non-interactive. Copier’s `run_copy(..., defaults=True)` / CLI `--defaults` fills questions from template defaults. Exact Generator flags are #2. ([Copier API `defaults`](https://copier.readthedocs.io/reference/api/))
- Generate into `$RUNNER_TEMP`, not the workspace. Nothing from the smoke tree is uploaded as an artifact.
- Smoke job needs uv **and** pnpm **and** `just` because it runs the Generated app’s full `just ci`, not only the CLI unit tests.

Until the Template exists, Starter `ci.yml` is lint/typecheck/test only. Do not ship a `continue-on-error` smoke that always “passes.”

## Dependabot

Config file: `.github/dependabot.yml`, `version: 2`. One `updates` entry per ecosystem × directory. ([Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference))

### Ecosystems (YAML values)

| Manager | `package-ecosystem` | Notes |
|---------|---------------------|--------|
| uv (`pyproject.toml` + `uv.lock`) | **`uv`** | Not `pip`. Astral: add `package-ecosystem: "uv"`. GitHub table: `uv`, supported uv **v0.11**. Vendoring N/A. ([uv + Dependabot](https://docs.astral.sh/uv/guides/integration/dependabot/); [Supported ecosystems](https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories)) |
| pnpm (`package.json` + `pnpm-lock.yaml`) | **`npm`** | YAML value is `npm`, not `pnpm`. GitHub lists “pnpm \| npm \| v7–v10”. |
| GitHub Actions | **`github-actions`** | `directory: "/"` covers `.github/workflows`. Updates `owner/repo@sha` and a same-line `# tag` comment. Ignores local `./.github/actions/…`. |
| Docker | **`docker`** | Generated app Dockerfiles. |
| Docker Compose | **`docker-compose`** | v2/v3 Compose files. Same idea as Docker. |

Do **not** also add `pip` for the same `pyproject.toml`. That would double-PR the same Python deps. Poetry/pipenv still use `pip`; uv does not.

Commit `uv.lock` and `pnpm-lock.yaml`. Dependabot’s uv updater reads the lockfile. pnpm without a lockfile is not a version-update story.

### Grouping so strangers are not flooded

Default Dependabot behaviour: **one PR per dependency**. `groups` combines matches into one PR. Unmatched deps still get solo PRs. First matching group wins. ([groups](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#groups--))

GitHub’s own example 3 is the v1 policy: group `minor` + `patch`; majors stay individual so a FastAPI or React major is reviewed alone. ([Example 3](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/optimizing-pr-creation-version-updates#example-3-individual-pull-requests-for-major-updates-and-grouped-for-minorpatch-updates))

`groups.*.dependency-type` (`production` / `development`) is supported for `bundler`, `composer`, `mix`, `maven`, `npm`, and `pip` — **not** `uv` or `github-actions`. For uv, group with `patterns: ["*"]` + `update-types`. (`allow.dependency-type` *does* list `uv`; that is a different key.) ([dependency-type (groups)](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#dependency-type-groups); [allow.dependency-type](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#dependency-type-allow))

Schedule: **`weekly`**. Daily plus ungrouped deps is how strangers get flooded. GitHub assigns a random time unless you set `day` / `time`. ([schedule](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/optimizing-pr-creation-version-updates#controlling-the-frequency-and-timings-of-dependency-updates))

Cooldown: Dependabot already applies a **3-day** default cooldown on version updates (not security updates) even when `cooldown` is omitted. Only set `cooldown` if the project also uses uv `exclude-newer`. ([cooldown](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#cooldown-); [uv Dependabot cooldown](https://docs.astral.sh/uv/guides/integration/dependabot/#dependency-cooldown))

`multi-ecosystem-groups` can smash uv + npm + docker into one PR. Skip for v1: a failed Python bump should not block a SPA bump. ([multi-ecosystem-groups](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#multi-ecosystem-groups-))

### Starter `dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: uv
    directory: /
    schedule:
      interval: weekly
    groups:
      python-minor-patch:
        patterns: ["*"]
        update-types: [minor, patch]

  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    groups:
      actions:
        patterns: ["*"]

  # Once the Template commits lockfiles, add directory entries for those
  # paths so Generated-app deps move in the Starter, not only after generate:
  # - package-ecosystem: uv
  #   directory: /src/davilly_starter/template   # actual path from #2 / #8
  # - package-ecosystem: npm
  #   directory: /src/davilly_starter/template/<spa>
```

GitHub Actions grouping can include majors: SHA bumps are mechanical and Dependabot’s comment update keeps the tag readable.

### Generated-app `dependabot.yml` (Template)

```yaml
version: 2
updates:
  - package-ecosystem: uv
    directory: /          # or /api — wherever pyproject.toml + uv.lock live
    schedule:
      interval: weekly
    groups:
      python-minor-patch:
        patterns: ["*"]
        update-types: [minor, patch]

  - package-ecosystem: npm
    directory: /web       # SPA; adjust to the Template layout
    schedule:
      interval: weekly
    groups:
      js-minor-patch:
        patterns: ["*"]
        update-types: [minor, patch]
        # optional: split with dependency-type: production | development (npm supports it)

  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    groups:
      actions:
        patterns: ["*"]

  - package-ecosystem: docker
    directory: /
    schedule:
      interval: weekly
    groups:
      docker:
        patterns: ["*"]

  - package-ecosystem: docker-compose
    directory: /
    schedule:
      interval: weekly
```

Directories must match the Template layout from #8. `directory` is not globbed; `directories:` is, if the API and a second Python package both have lockfiles.

Dependabot **alerts** (security) are a repo setting, free on public repos, and do not need this file. The YAML is **version updates**. Keep alerts on. ([GitHub security features](https://docs.github.com/en/code-security/getting-started/github-security-features))

## CodeQL

Code scanning is free on public GitHub.com repositories. ([About code scanning](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning); [Configuring advanced setup](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configuring-advanced-setup-for-code-scanning))

### Default setup vs advanced (why the Template ships a workflow)

**Default setup** is a repository setting. GitHub generates the analysis config; there is no workflow file to Copier-copy into a Generated app. It scans on push/PR to default and protected branches, plus a weekly schedule after recent activity. ([About setup types](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types))

**Advanced setup** is a workflow you commit. That is the only form a Template can ship so a stranger’s `uvx davilly-starter new` repo has CodeQL without opening Settings.

Do not run both: SARIF upload is rejected while default setup is enabled. Switching is Settings → CodeQL analysis → Switch to advanced / Disable CodeQL. ([Default setup enabled](https://docs.github.com/en/code-security/code-scanning/troubleshooting-sarif-uploads/default-setup-enabled); [Configuring advanced setup](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configuring-advanced-setup-for-code-scanning))

Starter: ship the same advanced workflow for reviewability, SHA pinning, `paths-ignore` on Copier sources, and parity with Generated apps. Do not also click default setup on `davilly-starter`.

### Languages

Identifiers ([Workflow configuration options](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options#languages-to-be-analyzed); [Supported languages](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/)):

| Language | Identifier | Build mode | Why |
|----------|------------|------------|-----|
| Python | `python` | `none` | Generator CLI; FastAPI package. Extractor: `.py`. Built-in support includes FastAPI-relevant libs; the Python pack is the one we care about. |
| JavaScript/TypeScript | `javascript-typescript` | `none` | Vite React SPA. Specifying `javascript` still analyzes TypeScript. |
| GitHub Actions | `actions` | `none` | Workflow injection / dangerous-workflow queries. Files: `.github/workflows/*.yml`. v1-sized and matches the “least privilege” goal. |

`build-mode: none` is required for interpreted languages. Python, JS/TS, and Actions are interpreted. ([codeql-action README — Build Modes](https://github.com/github/codeql-action/blob/main/README.md))

Use a matrix, one language per job, `fail-fast: false`. GitHub’s starter workflow is this shape. ([actions/starter-workflows codeql.yml](https://github.com/actions/starter-workflows/blob/main/code-scanning/codeql.yml))

Query suite: leave **`default`** (omit `queries:`). `security-extended` adds lower-precision alerts; `security-and-quality` is advanced-setup-only and noisier. A stranger-facing starter should not train Consumers to ignore CodeQL. ([CodeQL query suites](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-query-suites))

### Copier templates vs the Python/JS extractors

Copier renders files whose names end in `_templates_suffix`, default **`.jinja`**. A `app.py.jinja` is a template; a generated `app.py` is Python. ([Copier `templates_suffix`](https://copier.readthedocs.io/configuring/#templates_suffix); [Creating a template](https://copier.readthedocs.io/creating/))

If Template sources are committed as `foo.py` containing `{{ project_name }}`, the Python extractor will parse invalid Python on the **Starter**. Two complementary rules:

1. Keep Copier’s default `.jinja` suffix on files that contain Jinja. CodeQL then ignores them (`.py.jinja` is not `.py`).
2. On the Starter CodeQL config, `paths-ignore` the Template directory anyway, so leftover `.ts` / `.yml` without a suffix cannot pollute Starter alerts. Generated-app CodeQL scans the expanded tree and should **not** ignore those paths.

### `codeql.yml` sketch (both repos)

Permissions from GitHub’s starter: `security-events: write` is required to upload; `contents: read` and `actions: read` are documented as needed for private repos and are the right least-privilege set on public too; `packages: read` is for private CodeQL packs (harmless if unused).

```yaml
name: CodeQL
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "27 4 * * 1"
  merge_group:

permissions:
  contents: read

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
      actions: read
      packages: read
    strategy:
      fail-fast: false
      matrix:
        include:
          - language: python
            build-mode: none
          - language: javascript-typescript
            build-mode: none
          - language: actions
            build-mode: none
    steps:
      - uses: actions/checkout@<full-sha> # v7.x
        with:
          persist-credentials: false
      - uses: github/codeql-action/init@<full-sha> # v4
        with:
          languages: ${{ matrix.language }}
          build-mode: ${{ matrix.build-mode }}
          # Starter only:
          # config-file: .github/codeql/codeql-config.yml
      - uses: github/codeql-action/analyze@<full-sha> # v4
        with:
          category: "/language:${{ matrix.language }}"
```

Starter optional config (`.github/codeql/codeql-config.yml`):

```yaml
paths-ignore:
  - "**/template/**"          # actual Copier tree from #2
  - "**/*.jinja"
```

Do not put `queries: security-extended` unless grilling later wants the noise.

## Pin actions by SHA

GitHub: pinning to a full-length commit SHA is currently the **only** way to use an action as an immutable release. Tags can be moved. Short SHAs are not acceptable. Verify the SHA is from the action repo, not a fork. ([Secure use reference — Pin actions to a full-length commit SHA](https://docs.github.com/en/actions/reference/security/secure-use); [Using SHAs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/find-and-customize-actions#using-shas))

Tags are allowed only if you trust the creator. We still SHA-pin GitHub-owned actions (`actions/checkout`, `github/codeql-action/*`). uv’s own docs already SHA-pin `actions/checkout` and `astral-sh/setup-uv`. pnpm’s CI page SHA-pins `pnpm/setup`. That is the documented pattern, not a tag policy. ([uv GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/); [pnpm CI](https://pnpm.io/continuous-integration#github-actions))

**Policy for this Starter and the Template:**

1. Every `uses:` is `owner/repo@<40-hex-sha> # vX.Y.Z` (or `# vX` if that is the release tag).
2. The comment is on the **same line**. Dependabot rewrites SHA **and** comment for `github-actions`. If the SHA is not associated with any tag, Dependabot may jump to latest commit, not latest release — prefer SHAs that are release tags. ([GitHub Actions ecosystem caveats](https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories#github-actions))
3. Do not pin floating tags (`@v4`, `@main`) even for `actions/*`.
4. Dependabot `github-actions` grouped weekly is how pins move. Do not hand-edit SHAs in routine work.
5. Third-party actions in v1: `astral-sh/setup-uv`, `pnpm/setup`. No `pnpm/action-setup`, no `extractions/setup-just`, no `docker/setup-buildx` until a deploy ticket needs them.
6. Resolve SHAs at implementation time from the action repo’s release tag (`git rev-parse vX.Y.Z`). Do not copy the example SHAs in this note; they will be stale.

Dependabot alerts for vulnerable actions require semantic-version tags; SHA pins still get version updates via `dependabot.yml`. GitHub documents that alerts prefer semver tags. The weekly grouped Actions PR is the mitigation. ([Using release management](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/find-and-customize-actions#using-release-management-for-your-custom-actions))

## Least-privilege permissions

`permissions` can be top-level (all jobs) or per-job. If you set any permission, unspecified ones become `none`. `write` includes `read`. ([Workflow syntax — permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax); [Use GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token#modifying-the-permissions-for-the-github_token))

GitHub’s hardening guide: default `GITHUB_TOKEN` to contents read-only; raise per job. ([Secure use](https://docs.github.com/en/actions/reference/security/secure-use))

| Workflow | Top-level | Job extras |
|----------|-----------|------------|
| `ci.yml` | `contents: read` | none |
| `codeql.yml` | `contents: read` | `security-events: write`, `actions: read`, `packages: read` |
| future `release.yml` | `contents: read` on build; `id-token: write` **only** on publish | never on `ci.yml` |

Also set the **repository** Actions setting “Workflow permissions” to read-only `GITHUB_TOKEN` (contents + packages read). Workflow keys can still raise per job. Org owners can force this. ([Disabling or limiting GitHub Actions](https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization#setting-the-permissions-of-the-github_token-for-your-organization))

`actions/checkout` `persist-credentials` defaults to `true` (token in git config for later steps). CI never pushes. Set `persist-credentials: false`. uv’s publish example already does. ([actions/checkout README](https://github.com/actions/checkout); [uv publish workflow](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi))

Fork PRs from a public repo already get a read-only token; still declare `contents: read` so a settings drift cannot grant write. Never use `pull_request_target` for CI or CodeQL.

No `secrets: inherit` on reusable workflows (none in v1). No repository secrets required for CI or CodeQL. Smoke test must not read Stripe/OAuth secrets even if a maintainer adds them later for some other workflow — do not reference `secrets.*` in `ci.yml`.

## Secret scanning (no workflow)

Public repositories: secret scanning **runs automatically for free**. Partner patterns go to the provider; user alerts show in Security. ([Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning))

**Push protection for repositories** is a separate toggle (Secret Protection / Advanced Security) and is **not** on by default. **Push protection for users** is on by default for the GitHub account and blocks pushing supported secrets to **public** repos. ([Push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection))

v1: rely on automatic public scanning + user push protection. Optionally enable repo push protection in org settings; not a Template file. Do not commit `sk_test` / `whsec` fixtures; tests skip when unset.

Dependency graph is permanently enabled for public repos. Enable **Dependabot alerts** in Settings if they are not already on. ([Managing security and analysis settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository))

## What is not v1

- GitHub Actions reusable workflows / composite actions shared between Starter and Template. Two copies in Copier is fine; DRY later.
- Nx/Turborepo remote cache, `pnpm pipeline` (experimental).
- Matrix of several Python or Node versions. One version, pinned by #16. uv’s matrix docs exist if grilling wants them later.
- `docker compose up` in GHA.
- Pages/Fly/Railway deploy workflows.
- PyPI Trusted Publishing (issue 13).
- CodeQL `security-extended` / custom QL packs.
- Default setup as the Generated-app path.
- `pull_request_target`, `workflow_run`, or cache sharing between privileged and untrusted jobs.

## Implementation order

1. Issue 16 pins Python, Node, ruff, typechecker, ESLint, `just` recipes (`lint`, `typecheck`, `test`, `ci` including SPA build).
2. Issue 8 scaffolds the Template so smoke has something to generate.
3. Issue 20 writes Generated-app `justfile`, lockfiles, `.github/workflows/{ci,codeql}.yml`, `.github/dependabot.yml`. Tests skip Stripe/OAuth when unset.
4. Issue 21 writes the same three files on the Starter; adds `smoke` once 8+20 exist.
5. Resolve action SHAs at the moment of writing those files. Do not copy SHAs from this note.

## Primary sources

- [Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Use GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)
- [Using SHAs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/find-and-customize-actions#using-shas)
- [Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)
- [Supported ecosystems](https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories)
- [Optimizing Dependabot PR creation](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/optimizing-pr-creation-version-updates)
- [About setup types for code scanning](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types)
- [Configuring advanced setup](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configuring-advanced-setup-for-code-scanning)
- [Workflow configuration options for code scanning](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options)
- [CodeQL query suites](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-query-suites)
- [CodeQL supported languages](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/)
- [github/codeql-action](https://github.com/github/codeql-action)
- [actions/starter-workflows `codeql.yml`](https://github.com/actions/starter-workflows/blob/main/code-scanning/codeql.yml)
- [Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning)
- [Push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection)
- [Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
- [Using uv with Dependabot](https://docs.astral.sh/uv/guides/integration/dependabot/)
- [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)
- [pnpm Continuous Integration](https://pnpm.io/continuous-integration)
- [pnpm/setup](https://github.com/pnpm/setup)
- [just packages](https://just.systems/man/en/packages.html)
- [Copier templates_suffix](https://copier.readthedocs.io/configuring/#templates_suffix)
