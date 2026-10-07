# Nx + uv + pnpm for a FastAPI and Vite Generated app

Research for [Wayfinder issue 27](https://github.com/DavillyDevTeam/davilly-starter/issues/27). Verified **2026-10-07 UTC** (2026-10-06 in America/Sao_Paulo). This note specifies a future Template baseline; it does not implement one.

## Recommendation and boundary

Follow [ADR 0004](../adr/0004-nx-uv-pnpm-workspace.md): the **Generated app** is an Nx Workspace; this **Starter**, including its Generator and Copier Template package data, remains a uv Python package. Use pnpm for JavaScript, uv for Python, and Nx for task orchestration. No Just or Python package management through JavaScript executors.

Use an empty Nx `apps` preset plus the React application generator at an explicit `apps/web` path when preparing the Template. Register `apps/api` with `project.json` and `nx:run-commands`. Prefer official Vite/Vitest/ESLint plugins for the SPA; use explicit Python targets and conservative cache inputs. This is a recommendation, rather than an official Nx FastAPI integration.

## Pins and generation

Exact versions observed in first-party registry metadata:

| Tool | Pin | Evidence |
| --- | --- | --- |
| Nx and create-nx-workspace | `23.2.1` | [Nx metadata](https://registry.npmjs.org/nx/23.2.1), [creator metadata](https://registry.npmjs.org/create-nx-workspace/23.2.1) |
| @nx/react, @nx/vite | `23.2.1` | [React metadata](https://registry.npmjs.org/@nx/react/23.2.1), [Vite plugin metadata](https://registry.npmjs.org/@nx/vite/23.2.1) |
| @nx/eslint, @nx/vitest | `23.2.1` | [ESLint metadata](https://registry.npmjs.org/@nx/eslint/23.2.1), [Vitest metadata](https://registry.npmjs.org/@nx/vitest/23.2.1) |
| pnpm | `12.9.1` | [pnpm metadata](https://registry.npmjs.org/pnpm/12.9.1) |
| uv | `0.12.23` | [PyPI release metadata](https://pypi.org/pypi/uv/0.12.23/json) |
| Vite | `8.3.3` | [Vite metadata](https://registry.npmjs.org/vite/8.3.3) |

Keep all installed `nx`/`@nx/*` packages on the same exact version. `@nx/vite` accepts Vite 5–8, and Vite 8.3.3 requires Node `^20.19.0 || >=22.12.0`; the Node 24 major selected in [issue 16](https://github.com/DavillyDevTeam/davilly-starter/issues/16) fits that requirement. Lock the chosen Node/Python patch releases at Template implementation time; this ticket does not change their major-version decisions. [Nx Vite requirements](https://nx.dev/docs/technologies/build-tools/vite/introduction), [Vite package engines](https://registry.npmjs.org/vite/8.3.3).

Do not interpret “current” as permission to upgrade every dependency to latest: TypeScript latest is `7.0.2`, but typescript-eslint `8.71.1` accepts `<6.1.0`. Retain issue 16's `~6.0.2` constraint pending an explicitly tested upgrade. Its Just sketches are superseded by ADR 0004 and the ticket's retarget comment. The pnpm pin agrees with current metadata. [TypeScript metadata](https://registry.npmjs.org/typescript/7.0.2), [typescript-eslint peer dependencies](https://registry.npmjs.org/typescript-eslint/8.71.1).

Illustrative maintainer commands, executed in a disposable directory when preparing the Template:

```sh
pnpm dlx create-nx-workspace@23.2.1 generated-app \
  --preset=apps --packageManager=pnpm --nxCloud=skip \
  --interactive=false --skipGit --skipGitHubPush --aiAgents=none
cd generated-app
pnpm add -Dw --save-exact nx@23.2.1 @nx/react@23.2.1 \
  @nx/vite@23.2.1 @nx/eslint@23.2.1 @nx/vitest@23.2.1
pnpm nx g @nx/react:application apps/web --name=web \
  --bundler=vite --unitTestRunner=vitest --e2eTestRunner=none \
  --linter=eslint --style=css --routing=false
pnpm nx show project web --json
```

`apps` is the current empty integrated preset; avoid old examples using `empty`. `react-monorepo --bundler=vite --appName=web --packageManager=pnpm` is also supported and useful for exploration, but its generated path/layout should be inspected rather than assumed. The explicit directory generator makes `apps/web` deliberate. Both routes require a reviewed lockfile and subsequent strict-toolchain configuration; generator defaults are not the final Template policy. [Creator options/presets](https://nx.dev/docs/reference/create-nx-workspace), [React generator directory/options](https://nx.dev/docs/technologies/react/generators).

Set root `package.json` `packageManager` to `pnpm@12.9.1`, commit `pnpm-lock.yaml`, and retain `pnpm-workspace.yaml` for JS packages (for example `apps/web` and future JS libraries). The Python API needs no dummy npm package: its Nx registration is `project.json`. [pnpm workspace requirements](https://pnpm.io/workspaces), [Nx project configuration](https://nx.dev/docs/reference/project-configuration).

## Projects and Consumer commands

Suggested shape:

```text
nx.json, package.json, pnpm-workspace.yaml, pnpm-lock.yaml
apps/web/{package.json,project.json,vite.config.ts,tsconfig*.json,src/}
apps/api/{project.json,pyproject.toml,uv.lock,.python-version,src/api/,tests/}
compose.yaml
```

Keep a single Python project/lockfile inside `apps/api` initially. A root uv workspace is unnecessary for one Python project and would require adding its root manifest/lockfile to all relevant Nx inputs.

In Nx 23, `@nx/vite/plugin` infers `build`, `dev`, and `typecheck` from Vite/TypeScript configuration; Vitest moved into `@nx/vitest` in Nx 22. Ensure the generated ESLint/Vitest plugin options expose `lint` and `test`; verify the resolved project rather than copying older `@nx/vite:test` recipes. [Nx Vite introduction](https://nx.dev/docs/technologies/build-tools/vite/introduction), [Nx Vitest integration](https://nx.dev/docs/technologies/test-tools/vitest/introduction).

Consumer interface:

```sh
pnpm install --frozen-lockfile
uv sync --project apps/api --locked
pnpm nx run-many -t lint,typecheck,test,build
pnpm nx run-many -t dev --parallel=2
```

The ticket's combined `lint,typecheck,test,build,dev` invocation is possible, but separate finite checks from the never-ending development session. `run-many` runs the named targets across matching projects; CI must omit `dev`. [Nx CLI commands](https://nx.dev/docs/reference/nx-commands).

Illustrative `apps/api/project.json` (assumes ruff, basedpyright, pytest, Uvicorn and the chosen build backend are declared in the API's locked dependency groups):

```json
{
  "name": "api",
  "projectType": "application",
  "sourceRoot": "apps/api/src",
  "namedInputs": {
    "python": [
      "{projectRoot}/**/*",
      "!{projectRoot}/.venv/**/*",
      "!{projectRoot}/dist/**/*",
      "!{projectRoot}/**/__pycache__/**/*",
      "!{projectRoot}/.pytest_cache/**/*",
      "!{projectRoot}/.ruff_cache/**/*",
      "{workspaceRoot}/nx.json",
      "{workspaceRoot}/package.json",
      "{workspaceRoot}/pnpm-lock.yaml",
      { "runtime": "uv --version" },
      { "runtime": "uv run --project apps/api --locked python --version" }
    ]
  },
  "targets": {
    "lint": {
      "executor": "nx:run-commands", "cache": true,
      "inputs": ["python"], "outputs": [],
      "options": {
        "cwd": "apps/api", "parallel": false,
        "commands": ["uv run --locked ruff check .", "uv run --locked ruff format --check ."]
      }
    },
    "typecheck": {
      "executor": "nx:run-commands", "cache": true,
      "inputs": ["python"], "outputs": [],
      "options": { "cwd": "apps/api", "command": "uv run --locked basedpyright" }
    },
    "test": {
      "executor": "nx:run-commands", "cache": false,
      "inputs": ["python"], "outputs": [],
      "options": { "cwd": "apps/api", "command": "uv run --locked pytest" }
    },
    "build": {
      "executor": "nx:run-commands", "cache": true,
      "inputs": ["python"], "outputs": ["{projectRoot}/dist"],
      "options": {
        "cwd": "apps/api",
        "command": "uv run --locked uv build --no-build-isolation --wheel --clear"
      }
    },
    "dev": {
      "executor": "nx:run-commands", "cache": false, "continuous": true,
      "options": {
        "cwd": "apps/api",
        "command": "uv run --locked uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
      }
    }
  }
}
```

`cwd` makes Python discovery predictable; multiple lint commands need `parallel: false`. API `build` produces a wheel, not an empty success or Docker image. It requires a packaged `src/api` tree and explicit `[build-system]`; with `--no-build-isolation`, declare and lock the backend and all its build requirements in the environment. `uv run --locked` validates/syncs that environment before invoking uv's build command. `uv build` alone does not promise that isolated build dependencies follow `uv.lock`. [run-commands reference](https://nx.dev/docs/reference/nx/executors), [uv build guidance](https://docs.astral.sh/uv/guides/package/), [uv command options](https://docs.astral.sh/uv/reference/cli/).

## Graph and cache correctness

Nx discovers the explicit API project, but does not infer Python imports or a browser's HTTP dependency on FastAPI. Add `implicitDependencies: ["api"]` to `web` only if its generated contract/client actually depends on API changes; otherwise keep the graph independent. Model shared contract generation as its own project when introduced. `continuous: true` describes development tasks that never exit; it does not make service readiness checks unnecessary. [Project configuration](https://nx.dev/docs/reference/project-configuration).

The API input glob includes its manifest, lockfile, version file, tools/configs and tests. Runtime inputs account for uv and the selected Python interpreter. Add an OS/platform input if caching across incompatible platforms. Explicitly include any future root Python config/lockfile. Keep `.venv`, caches and build products out of hashes; never restore `.venv` through Nx. [Inputs reference](https://nx.dev/docs/reference/inputs).

Keep Python integration tests noncached initially: Postgres/network/environment state is not represented by source hashes. Cache only deterministic, isolated tests after describing their inputs. Development, migrations and installs remain noncached. Configure `web:dev` as noncached too. Nx caches terminal results and declared outputs, so a stale input definition can silently restore an incorrect artifact. [Cache behavior](https://nx.dev/docs/concepts/how-caching-works).

Preserve inferred SPA inputs/outputs and supplement its `build` inputs with `{ "env": "VITE_API_URL" }` and any other actual build-time variables. Ensure `.env` files used by Vite are inputs, without committing secrets. Align `outputs` with the real `build.outDir`; do not copy a `dist/apps/web` assumption when output is `apps/web/dist`. Check merged configuration with `pnpm nx show project web --json`. [Input environment hashing](https://nx.dev/docs/reference/inputs), [Nx target defaults](https://nx.dev/docs/reference/nx-json).

## Locked Python semantics

Commit `apps/api/uv.lock`. Prefer `uv sync --locked` and `uv run --locked` in CI and Nx targets: they fail if the existing lockfile needs updating. `--frozen` skips the freshness check and trusts the lockfile; it is not a stronger validation mode. Neither option means offline execution. Use `uv lock` intentionally when changing dependencies. [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

In Docker, a partial manifest copy can justify `--frozen` for a dependency layer, followed by a complete-project `uv sync --locked`. For the one-project API, copying its manifest and lockfile is simpler. Pin the uv image/binary version; do not adopt the docs' moving `latest` example as a reproducible pin. [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/).

## GitHub Actions without configured secrets

Use ordinary `pull_request`/`push` workflows with full history (`actions/checkout`, `fetch-depth: 0`). Install the pinned pnpm/uv and selected Node/Python, then run the two locked installs above before Nx. No Nx Cloud account, token, remote cache, task distribution or privileged pull-request workflow is required. [Nx GitHub integration](https://nx.dev/docs/kb/github-integration).

For a PR, pass the base SHA from `github.event.pull_request.base.sha` and the checked-out SHA as `--base`/`--head`:

```sh
pnpm nx affected -t lint,typecheck,test,build --base="$NX_BASE" --head="$NX_HEAD"
```

Set those environment variables through workflow expressions, not shell interpolation of PR text. Use `run-many` for all-project validation on main pushes, scheduled/manual runs, or when a reliable base is unavailable. This conservative baseline also catches earlier failed main builds. Later, `nrwl/nx-set-shas` can select the last successful main run with the automatic GitHub token and read permissions; configured repository secrets remain unnecessary. [Affected Git/base/head guidance](https://nx.dev/docs/features/ci-features/affected), [GitHub integration](https://nx.dev/docs/kb/github-integration).

Affected selection and task hashing are separate: declare shared files as project inputs so their changes select the API, and verify with a throwaway change to `uv.lock`, `nx.json` and any shared contract. Be conservative about lockfile changes instead of opting into narrow JS dependency-update heuristics before the Python graph is modeled. [Affected and lockfile behavior](https://nx.dev/docs/features/ci-features/affected).

## Compose and Pages alignment

Keep [issue 5](https://github.com/DavillyDevTeam/davilly-starter/issues/5)'s `/api` convention. Vite inside Compose proxies to the API service name; on the host it proxies to localhost. Illustrative Vite fragment:

```ts
server: {
  host: '0.0.0.0',
  port: 5173,
  strictPort: true,
  proxy: {
    '/api': {
      target: process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

Compose sets `API_PROXY_TARGET=http://api:8000`, leaves `VITE_API_URL` empty, publishes the web port, and starts both services using the corresponding Nx `dev` targets. Keep API routes under `/api`; the fragment preserves the prefix. Readiness/healthchecks and mounts belong to Compose implementation. No separate Compose DNS name should reach the browser. [Vite server proxy](https://vite.dev/config/server-options).

Pages receives a production `VITE_API_URL` at build time; it is public configuration, not a secret. The dev proxy does not exist in static Pages output. FastAPI uses explicit Pages/custom-domain origins, allows `Authorization` and the required methods, and keeps cookie credentials disabled for the selected bearer-token flow. Nx only runs the build; it does not alter these deployment decisions. [Vite env behavior](https://vite.dev/guide/env-and-mode), [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/).

## Copier ownership and implementation handoff

Run Nx generators while maintaining the Template, inspect their outputs and commit the parameterized result as Copier package data. Do not invoke create-nx-workspace as a routine Consumer post-generation step: it can overwrite package/config files and introduces network-dependent version drift. Retain Copier's answers file and versioned update path. Copier updates merge Template changes with Consumer changes and can produce conflicts. [Copier update model](https://copier.readthedocs.io/en/stable/updating/).

Nx generators/migrations and Copier can both edit `package.json`, lockfiles, `nx.json`, Vite/TS config and workflow files. Treat that overlap as an explicit maintainer decision: migrate a disposable generated baseline, review the diff, then port it into the Template; Consumers review conflicts after their own Nx migrations. Nx does not create an ownership boundary that exempts these files from Copier updates. This ownership policy is a recommendation derived from the two tools' editing models, not a built-in coordination mechanism. [Nx generators](https://nx.dev/docs/technologies/react/generators), [Copier updates](https://copier.readthedocs.io/en/stable/updating/).

Before implementing, smoke-generate outside this Starter, verify resolved targets/graph, run locked installs and finite checks, repeat build to check caching, mutate lock/config/env inputs to check invalidation, and boot Compose through `/api`. These remain future implementation acceptance checks; this research did not execute the illustrated Generated app or modify the Template.
