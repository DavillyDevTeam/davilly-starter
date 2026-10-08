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
