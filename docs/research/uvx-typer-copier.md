# Research: uvx + Typer + Copier layout

How this Starter should be packaged so a Consumer can run `uvx davilly-starter new my-app` and have the Generator (Typer) expand a Copier Template that ships *inside* the wheel — not a second git clone.

This note does not implement the Generator. Copier questions beyond name / author / license / locales remain fog ([Wayfinder: davilly-starter v1](https://github.com/DavillyDevTeam/davilly-starter/issues/1)).

## Answer (gist)

1. Publish one Python project named `davilly-starter` with a console script of the **same** name. `new` is a Typer **subcommand**, not a second console script.
2. After PyPI: `uvx davilly-starter new my-app`. Until then: `uvx --from git+https://github.com/DavillyDevTeam/davilly-starter davilly-starter new my-app`.
3. Keep the Template at repo-root `template/` with `copier.yml` beside it (`_subdirectory: template`). Hatchling `force-include` maps those paths into the installed package. At runtime the Generator hands Copier a local filesystem path from `importlib.resources.as_file`.
4. Typer flags become Copier `data={...}`. Call `copier.run_copy(..., data=data, defaults=True)` so answered questions are not prompted and the rest take `copier.yml` defaults.

## 1. Exact `uvx` invocations

`uvx` is an alias for `uv tool run`. It installs the tool into an ephemeral environment and runs one of its executables. Arguments after the tool name are passed through to that executable. ([uv tools guide](https://docs.astral.sh/uv/guides/tools/); [uv tools concept](https://docs.astral.sh/uv/concepts/tools/); [CLI: uv tool run](https://docs.astral.sh/uv/reference/cli/#uv-tool-run))

By default uv assumes **package name = command name**. `--from` is required when they differ, when the source is not the default index, or when the version spec is more than `name@exact`. ([uv tools guide — different package names / different sources](https://docs.astral.sh/uv/guides/tools/#commands-with-different-package-names); [CLI `--from`](https://docs.astral.sh/uv/reference/cli/#uv-tool-run--from))

### From PyPI (intended)

Project name `davilly-starter` is still free: `GET https://pypi.org/pypi/davilly-starter/json` returned **HTTP 404** on 2026-10-06. PyPI’s JSON API documents that route as project metadata (`GET /pypi/<project>/json`). ([PyPI JSON API](https://docs.pypi.org/api/json/))

Once published:

```bash
uvx davilly-starter new my-app
uvx davilly-starter@latest new my-app
uvx --from davilly-starter davilly-starter new my-app
```

The first form works because package and console script share the name `davilly-starter`; `new` and `my-app` are arguments to that script (same pattern as `uvx pycowsay hello from uv`). ([uv tools guide — running tools](https://docs.astral.sh/uv/guides/tools/#running-tools))

Pin a version with `command@<version>` or `--from 'davilly-starter==x.y.z'`. `@` is only for an exact version. ([uv tools guide — requesting specific versions](https://docs.astral.sh/uv/guides/tools/#requesting-specific-versions))

### From git (until PyPI)

uv’s documented git form is `--from git+https://github.com/<org>/<repo> <command>`:

```bash
uvx --from git+https://github.com/DavillyDevTeam/davilly-starter davilly-starter new my-app
uvx --from git+https://github.com/DavillyDevTeam/davilly-starter@main davilly-starter new my-app
```

Branch, tag, and commit all use `@ref` on the git URL. ([uv tools guide — requesting different sources](https://docs.astral.sh/uv/guides/tools/#requesting-different-sources))

Do **not** write `uvx --from git+https://github.com/DavillyDevTeam/davilly-starter new my-app`. That asks uv to run a console script named `new` from the package, and this Starter will not ship one.

`uv tool install git+https://github.com/DavillyDevTeam/davilly-starter` then `davilly-starter new my-app` is the persistent equivalent; it installs every executable the package declares. ([uv tools guide — installing tools](https://docs.astral.sh/uv/guides/tools/#installing-tools))

Git installs build the project from the clone. The repo must contain a `[build-system]` and `[project.scripts]` or uv has nothing to invoke. ([uv: build systems and entry points](https://docs.astral.sh/uv/concepts/projects/config/#entry-points))

## 2. Console script vs `uvx … davilly-starter new`

`[project.scripts]` is the standard console-scripts table. The key is the installed command name; the value is an object reference. After install, running the command is equivalent to importing that object and calling it. ([Writing pyproject.toml — creating executable scripts](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#creating-executable-scripts); [pyproject.toml spec — entry points](https://packaging.python.org/en/latest/specifications/pyproject-toml/#entry-points); [uv: command-line interfaces](https://docs.astral.sh/uv/concepts/projects/config/#command-line-interfaces))

Typer’s packaging tutorial uses exactly that table and points the value at the `Typer()` instance, which is callable:

```toml
[project]
name = "davilly-starter"

[project.scripts]
davilly-starter = "davilly_starter.main:app"
```

([Typer: building a package](https://typer.tiangolo.com/tutorial/package/))

uv will not emit that executable unless a build backend is declared. ([uv: entry points require a build system](https://docs.astral.sh/uv/concepts/projects/config/#entry-points))

`new` must **not** be a `[project.scripts]` key. It is a Typer command of the `davilly-starter` program. With a single `@app.command()` and no callback, Typer collapses that function into the *main* program, so `uvx davilly-starter my-app` would work and `… new my-app` would not. A `@app.callback()` keeps a one-command app in subcommand mode, which is what `uvx davilly-starter new my-app` needs. ([Typer: one or multiple commands](https://typer.tiangolo.com/tutorial/commands/one-or-multiple/); [Typer: commands](https://typer.tiangolo.com/tutorial/commands/); [Typer: callback](https://typer.tiangolo.com/tutorial/commands/callback/))

Optional: `src/davilly_starter/__main__.py` calling `app()` supports `python -m davilly_starter`. Shell completion is tied to the console-script name, not to `-m`. ([Typer: support python -m](https://typer.tiangolo.com/tutorial/package/#support-python--m-optional))

Tool executables uv installs are the package’s own console scripts, not those of its dependencies (Copier’s `copier` CLI is not on PATH via `uvx davilly-starter`). ([uv tools concept — tool executables](https://docs.astral.sh/uv/concepts/tools/#tool-executables))

## 3. Where the Template lives and how it enters the wheel

### Copier’s view of a template

`copier.yml` / `copier.yaml` lives at the **root of the template path** passed to `run_copy`. `_subdirectory` (Copier setting, no CLI flag) is “the subdirectory to use as the template root when generating a project” and exists so metadata and the files that become the Generated app can stay apart. Default excludes include `copier.yml`, `copier.yaml`, and `.git`, so those do not land in the Generated app even without `_subdirectory`. ([Copier: the copier.yml file](https://copier.readthedocs.io/en/stable/configuring/#the-copieryml-file); [Copier: subdirectory](https://copier.readthedocs.io/en/stable/configuring/#subdirectory); [Copier: exclude](https://copier.readthedocs.io/en/stable/configuring/#exclude))

The template argument to `copier.run_copy` may be a local path or a git URL. ([Copier: generating a project](https://copier.readthedocs.io/en/stable/generating/))

The ticket constraint is **package data, not a second git clone**. The Generator should pass a local path inside the installed wheel.

### Runtime location

Wheels are zip files; resources need not exist as real paths until extracted. `importlib.resources.files(anchor)` returns a Traversable; `as_file(...)` (directory support since 3.12) yields a `pathlib.Path` and cleans up any temp extraction. Copier needs that filesystem path.

```python
from importlib.resources import as_file, files
from copier import run_copy

with as_file(files("davilly_starter").joinpath("copier_root")) as src:
    run_copy(str(src), dst_path, data=data, defaults=True)
```

([importlib.resources](https://docs.python.org/3/library/importlib.resources.html); [Copier: run_copy](https://copier.readthedocs.io/en/stable/generating/))

### Build backends

**uv_build** (uv’s default) includes the Python module under `src/<package>/` in the wheel. “There are no specific wheel includes… all data files must either be under the module root or in the appropriate data directory. Most packages store small data in the module root alongside the source code.” `tool.uv.build-backend.data` is the wheel `.data` directory (environment prefix), not importable package data — the wrong place for a Copier tree. uv itself points at Hatchling “when build scripts or a more flexible project layout are required.” ([uv build backend](https://docs.astral.sh/uv/concepts/build-backend/))

**Hatchling** ships the discovered package (`<NAME>/__init__.py` or `src/<NAME>/__init__.py`) when no file-selection options are set. Files that live *inside* that package directory therefore ride along. Files *outside* it need `force-include`, which maps a source path onto a path inside the wheel. Directory sources are included recursively. Put the same mapping on **sdist and wheel**: many frontends build the wheel from the sdist. ([Hatch: file selection / force-include](https://hatch.pypa.io/latest/config/build/#forced-inclusion); [Hatch wheel: default file selection](https://hatch.pypa.io/latest/plugins/builder/wheel/#default-file-selection))

**setuptools** treats non-`.py` files inside the package as data. With `pyproject.toml`, `include-package-data` defaults to true; `package-data` globs select extra files (dotfiles need an explicit `.*` pattern). ([setuptools: data files](https://setuptools.pypa.io/en/latest/userguide/datafiles.html))

### Recommendation

Use Hatchling. Keep the Template as a sibling of `src/` (a FastAPI + Vite tree is not “small data” next to CLI modules). Force-include it *into* `davilly_starter/` so `importlib.resources` can see it:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel.force-include]
"copier.yml" = "davilly_starter/copier_root/copier.yml"
"template" = "davilly_starter/copier_root/template"

[tool.hatch.build.targets.sdist.force-include]
"copier.yml" = "davilly_starter/copier_root/copier.yml"
"template" = "davilly_starter/copier_root/template"
```

Zero-config alternative: put `copier.yml` and the Template files under `src/davilly_starter/copier_root/` and use uv_build. Same runtime API; worse editing layout.

Do not clone `git+https://github.com/DavillyDevTeam/davilly-starter` from inside `new`. That would fetch the Template a second time and ignore the wheel.

**Update story (fog).** Copier records answers (default `.copier-answers.yml`) so later `copier update` can find the original template. A `_src_path` that points at a uv cache / site-packages directory will not survive a cache prune. The map already leaves “Copier update story for already-generated apps” unspecified. ([Copier: answers_file](https://copier.readthedocs.io/en/stable/configuring/#answers_file); [Copier: generating / templates versions](https://copier.readthedocs.io/en/stable/generating/))

## 4. Recommended directory tree

```
.
├── pyproject.toml                 # name = "davilly-starter"; [project.scripts]; hatchling
├── README.md
├── LICENSE
├── CONTEXT.md
├── AGENTS.md
├── docs/
│   ├── adr/
│   ├── agents/
│   └── research/
├── src/
│   └── davilly_starter/           # Generator (importable package)
│       ├── __init__.py
│       ├── __main__.py            # optional python -m
│       └── main.py                # app = typer.Typer(); @app.callback(); @app.command() def new
├── copier.yml                     # questions + _subdirectory: template
└── template/                      # files that become the Generated app
    ├── {{ _copier_conf.answers_file }}.jinja
    └── … FastAPI + Vite tree …
```

This matches Typer’s `uv init --package` layout (`src/<import_name>/`) and Copier’s `_subdirectory` example (metadata at template-path root, renderable files in a subfolder). Docs, ADR, and Generator Python stay out of the Generated app because they are not under `template/`. ([Typer: create a project](https://typer.tiangolo.com/tutorial/package/#create-a-project); [Copier: subdirectory](https://copier.readthedocs.io/en/stable/configuring/#subdirectory); [uv_build module layout](https://docs.astral.sh/uv/concepts/build-backend/#modules))

`copier.yml` at the git root also means `copier copy gh:DavillyDevTeam/davilly-starter` would work as a *secondary* interface. The public interface stays the Typer CLI.

## 5. Copier parameters → Typer flags (AFK)

### Answer sources

Copier fills answers in this order: (1) CLI/API `data`, (2) interactive prompt — **it will not ask questions already answered in (1)**, (3) previous answers file, (4) defaults in `copier.yml`. ([Copier: configuration sources](https://copier.readthedocs.io/en/stable/configuring/#configuration-sources))

`data` is API-only (not a `copier.yml` key). The documented AFK pattern is force + data:

```bash
copier copy -fd 'user_name=Manuel Calavera' template destination
```

“take all default answers from template, except the user name, which is overridden, and don’t ask user anything else.” `-f` / `--force` is `--defaults --overwrite`. ([Copier: data](https://copier.readthedocs.io/en/stable/configuring/#data); [Copier: force](https://copier.readthedocs.io/en/stable/configuring/#force); [Copier: defaults](https://copier.readthedocs.io/en/stable/configuring/#defaults))

`defaults=True` uses default answers. “Any question that does not have a default value must be answered via CLI/API. Otherwise, an error is raised.” Leave `default` empty in `copier.yml` only to *force* an answer. ([Copier: defaults](https://copier.readthedocs.io/en/stable/configuring/#defaults); [Copier: questions — default](https://copier.readthedocs.io/en/stable/configuring/#questions))

Programmatic copy:

```python
copier.run_copy(src_path, dst_path, data=data, defaults=True)
```

Do **not** pass Copier’s `force`/`overwrite` for a first-time `new`: overwrite is for existing files. If `dst_path` is missing, Copier creates it. If it exists, keep it writable and let the Generator fail rather than clobber. ([Copier: generating a project](https://copier.readthedocs.io/en/stable/generating/); [Copier API `run_copy`](https://copier.readthedocs.io/en/stable/reference/api/))

### Typer mapping

CLI arguments are required by default; CLI options are optional. A required option is `Annotated[T, typer.Option()]` with no default. ([Typer: first steps](https://typer.tiangolo.com/tutorial/first-steps/); [Typer: required options](https://typer.tiangolo.com/tutorial/options/required/); [Typer: command options](https://typer.tiangolo.com/tutorial/commands/options/))

| Consumer CLI | Typer | Copier `data` key (suggested) | `copier.yml` default |
|---|---|---|---|
| `new my-app` | `name: Annotated[str, typer.Argument()]` | `project_name` (and `dst_path = name`) | none — always passed |
| `--author` | optional `str \| None = None` | `author` if not `None` | a non-empty default so AFK does not error |
| `--license` | optional, default `None` or `"MIT"` | `license` | `MIT` (map) |
| `--locales` | optional, default `None` or `"en,pt-BR"` | `locales` | `en,pt-BR` (map) |

Put **only provided values** in `data`. Always include `project_name` from the argument. With `defaults=True`, omitted flags take `copier.yml` defaults and Copier does not prompt.

Do not use `typer.Option(prompt=True)` for these: that prompts in Typer even when Copier already has a default, which is not AFK.

Interactive mode, if wanted later: `defaults=False` and omit unspecified keys from `data` so Copier asks. That is the opposite of overnight-agent use; v1 should default to `defaults=True`.

Give every question a `default` (or always pass it in `data`). `project_name` has no template default; the Argument supplies it.

### Unsafe features

`_tasks` (and other “dangerous features”) are off unless `unsafe=True` / `--UNSAFE` / `--trust`. Not settable in `copier.yml`. v1 can skip `_tasks` and leave `unsafe` false; if tasks are added, the Generator must pass `unsafe=True` because this Template is first-party. ([Copier: unsafe](https://copier.readthedocs.io/en/stable/configuring/#unsafe); [Copier: tasks](https://copier.readthedocs.io/en/stable/configuring/#tasks); [Copier: generating — trust warning](https://copier.readthedocs.io/en/stable/generating/))

## 6. `pyproject.toml` sketch (not an implementation)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "davilly-starter"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["typer", "copier"]

[project.scripts]
davilly-starter = "davilly_starter.main:app"
```

Plus the Hatchling `force-include` tables in §3. `[project]` `name` is the PyPI / uvx package name; it cannot be dynamic. ([Writing pyproject.toml — name](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#name); [choosing a build backend](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#declaring-the-build-backend))

## Sources

- [uv: using tools](https://docs.astral.sh/uv/guides/tools/)
- [uv: tools concept](https://docs.astral.sh/uv/concepts/tools/)
- [uv: CLI reference (`uv tool run`)](https://docs.astral.sh/uv/reference/cli/#uv-tool-run)
- [uv: project entry points](https://docs.astral.sh/uv/concepts/projects/config/#entry-points)
- [uv: build backend](https://docs.astral.sh/uv/concepts/build-backend/)
- [Typer: building a package](https://typer.tiangolo.com/tutorial/package/)
- [Typer: commands](https://typer.tiangolo.com/tutorial/commands/)
- [Typer: one or multiple commands](https://typer.tiangolo.com/tutorial/commands/one-or-multiple/)
- [Typer: callback](https://typer.tiangolo.com/tutorial/commands/callback/)
- [Typer: command options](https://typer.tiangolo.com/tutorial/commands/options/)
- [Typer: required options](https://typer.tiangolo.com/tutorial/options/required/)
- [Copier: generating a project](https://copier.readthedocs.io/en/stable/generating/)
- [Copier: configuring a template](https://copier.readthedocs.io/en/stable/configuring/)
- [Copier API](https://copier.readthedocs.io/en/stable/reference/api/)
- [Hatch: build configuration](https://hatch.pypa.io/latest/config/build/)
- [Hatch: wheel builder](https://hatch.pypa.io/latest/plugins/builder/wheel/)
- [setuptools: data files](https://setuptools.pypa.io/en/latest/userguide/datafiles.html)
- [PyPA: writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [PyPA: pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [importlib.resources](https://docs.python.org/3/library/importlib.resources.html)
- [PyPI JSON API](https://docs.pypi.org/api/json/)
