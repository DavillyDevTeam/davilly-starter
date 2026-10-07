# davilly-starter

Davilly Software’s open-source app **Starter** for Davilly and external Consumers alike. The Python **Generator** uses Typer and Copier to turn a parameterized **Template** into a FastAPI + Vite React SPA + Postgres **Generated app**.

## Status and Generator interface

The Generator and Template are not implemented yet on `main`. The commands below describe the planned interface; they cannot generate an app today.

Until publication to PyPI, the Generator will run directly from git:

```bash
uvx --from git+https://github.com/DavillyDevTeam/davilly-starter davilly-starter new my-app
```

After publication to PyPI (a v1 gate):

```bash
uvx davilly-starter new my-app
```

Copier parameters will include project name, author, license (MIT by default), and locales. Generated apps will have their own identity, without hard-coded Davilly product branding.

## Planned v1 Generated app

| Piece | v1 decision |
| --- | --- |
| API | FastAPI |
| Frontend | Vite + React SPA with a marketing landing page |
| Database | Postgres |
| Workspace | Nx at the Generated-app root; pnpm for the SPA; uv for all Python dependencies, with Nx targets calling `uv run` |
| Auth | fastapi-users with email/password and JWT; logout discards the client token (no server-side revoke, no Redis for auth); Google and GitHub OAuth optional via runtime environment variables |
| Billing | Stripe subscriptions, Customer Portal, and signed webhooks using Stripe’s official SDK; plans live in Postgres, admin-managed and feature-flagged; Stripe API keys stay in env |
| Locales | `en,pt-BR` by default, configurable through Copier |
| Local boot | Docker Compose; the first boot milestone is a visible marketing landing page |
| Production | SPA on Cloudflare Pages; FastAPI API on any Docker host |
| Agent guidance | `AGENTS.md` and `docs/agents/` for issue tracking, triage, and domain docs |

## Running a Generated app

Once the Generator and Template land, the local boot interface will be:

```bash
cd my-app
docker compose up
```

Local development uses Vite and Uvicorn. The Generated-app validation interface will be:

```bash
pnpm nx run-many -t lint,typecheck,test,build
```

The Workspace uses **Nx + pnpm + uv**, as specified in [ADR 0004](docs/adr/0004-nx-uv-pnpm-workspace.md), which supersedes the earlier Just decision. This Starter itself stays a uv Python project; its Copier Template is package data.

Production separates the SPA from the API: Cloudflare Pages hosts the frontend, and a Docker host runs FastAPI. See [ADR 0001](docs/adr/0001-fastapi-vite-generated-app.md).

## Scope and decisions

v1 targets web apps. Desktop/Tauri is a possible later Generator flag. Next.js and full-stack Node are outside v1, and Orca is optional for Consumers.

Follow [Wayfinder: davilly-starter v1](https://github.com/DavillyDevTeam/davilly-starter/issues/1) for implementation progress and open decisions. Domain vocabulary lives in [CONTEXT.md](CONTEXT.md).

## License

[MIT](LICENSE) © 2026 Davilly Software

## Generator development

The Starter is a standalone uv Python package, requiring Python 3.14
(`.python-version`). It has no Just or Nx task layer. Install Python and the
locked runtime/development dependencies with uv:

```bash
uv python install
uv sync --locked
uv run --locked davilly-starter --help
uv run --locked davilly-starter new --help
```

The `new` command currently exits with a clear not-implemented message;
[Task: Scaffold generator landing boot](https://github.com/DavillyDevTeam/davilly-starter/issues/8)
owns Template expansion and the Generated app.

Run the same Generator gates as CI:

```bash
uv lock --check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked basedpyright
uv build
```

To format code, use `uv run --locked ruff format .`. After intentionally changing
dependencies, run `uv lock` and commit `uv.lock`. uv is the only Python installer.

Ruff targets Python 3.14 with annotations (`ANN`, including the ban on `Any`),
`PYI`, `PGH`, and the research lint families. basedpyright is pinned to 1.40.x
in `recommended` mode, fails on warnings, and treats explicit `Any` and ignores
without a diagnostic code as errors. An exception needs a diagnostic code and
a one-line explanation; do not cast or suppress errors to make checks pass.
Lint discovery and type checking cover Generator sources, excluding the future
Template's Generated-app code.

The package follows the researched `src/davilly_starter` layout, Hatchling build,
and single `davilly-starter` console script. When task #8 adds root `copier.yml`
and `template/`, include them as package data at
`davilly_starter/copier_root/{copier.yml,template}` using Hatchling wheel
force-includes and ensure both originals are included in the sdist. Access the
installed tree with `importlib.resources.as_file`; do not fetch a second clone.
