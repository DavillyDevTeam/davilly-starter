# davilly-starter

A Python Generator that writes a parameterized FastAPI + Vite React Generated app.
The Generated app is an Nx workspace using pnpm for JavaScript and uv for Python.

```sh
uvx --from git+https://github.com/DavillyDevTeam/davilly-starter davilly-starter new my-app
cd my-app
docker compose up --build
```

Open http://localhost:5173 for the marketing landing in English and Português
(Brasil). FastAPI docs are at http://localhost:8000/docs. Compose includes Postgres.
PyPI publishing is a follow-up; `uvx davilly-starter` is not available yet.

```sh
uvx --from git+https://github.com/DavillyDevTeam/davilly-starter davilly-starter new my-app \
  --project-name 'My Product' --author 'My Team' --license MIT --locales en,pt-BR
```

`--locales en` writes an English-only tree (no `pt-BR` catalogs or language switcher).
The directory name must be lowercase kebab-case. Existing directories are
rejected. Supported locales are `en`, `pt-BR`, or both; supported license options
are `MIT`, `Apache-2.0`, and `UNLICENSED`. No prompts or second Template clone.
The Template is bundled inside the installed wheel at `davilly_starter/copier_root`.
Landing copy and API-facing strings live in shared i18next JSON v4 catalogs.

The Generated app README documents native development,
`pnpm nx run-many -t lint,typecheck,test,build`, and production deploy
(Cloudflare Pages SPA + FastAPI on any Docker host). Generated apps ship
`AGENTS.md` and `docs/agents/` (Orca optional). No credentials are needed
for boot. Auth, billing, OAuth, and CI are follow-up work.

## Develop the Generator

Use Python 3.14 and uv. The Starter itself is a uv-only package.
Hatchling bundles the repo-root `template/` and `copier.yml` into the wheel.
Use a non-editable install to exercise that packaged Template:

```sh
uv lock --check
uv sync --no-editable
uv run --no-editable ruff check src tests
uv run --no-editable ruff format --check src tests
uv run --no-editable basedpyright
uv run --no-editable pytest
uv build
uvx --no-cache --from ./dist/davilly_starter-0.1.0-py3-none-any.whl davilly-starter new /tmp/my-app
```

## License

[MIT](LICENSE) © 2026 Davilly Software
