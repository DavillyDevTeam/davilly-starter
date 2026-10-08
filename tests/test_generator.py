import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from davilly_starter.main import app

RAILS_FILES = (
    "AGENTS.md",
    "CONTEXT.md",
    "docs/agents/handoff.md",
    "docs/agents/issue-tracker.md",
    "docs/agents/triage-labels.md",
    "docs/agents/domain.md",
    "docs/adr/0001-nx-uv-pnpm-workspace.md",
    "docs/adr/0002-orca-matt-handoff.md",
)

TASK_FILES = (
    "package.json",
    "nx.json",
    "compose.yaml",
    "Dockerfile.api",
    "Dockerfile.web",
    "pyproject.toml",
    "apps/api/project.json",
    "apps/web/project.json",
    "apps/web/package.json",
)

AGENT_TRIGGERS = (
    "Handoff",
    "Wayfinder",
    "Grilling",
    "Domain-modeling",
    "Triage",
)


def generate(destination: Path, *flags: str) -> None:
    result = CliRunner().invoke(app, ["new", str(destination), *flags])
    assert result.exit_code == 0, result.output


def read(destination: Path, relative: str) -> str:
    return (destination / relative).read_text(encoding="utf-8")


def files_mentioning(destination: Path, needle: str) -> list[Path]:
    hits: list[Path] = []
    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if needle in text:
            hits.append(path)
    return hits


def assert_api_style_clean(destination: Path) -> None:
    api = destination / "apps" / "api"
    for args in (
        ["ruff", "check", str(api)],
        ["ruff", "format", "--check", str(api)],
    ):
        result = subprocess.run(args, cwd=destination, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


def assert_agent_rails(destination: Path, project_name: str) -> None:
    for relative in RAILS_FILES:
        assert (destination / relative).is_file(), relative
    assert not (destination / "justfile").exists()
    assert not (destination / ".agents").exists()
    assert not (destination / "docs/research").exists()
    assert not (destination / "docs/adr/0003-orca-matt-handoff.md").exists()
    assert not (destination / "docs/adr/0004-nx-uv-pnpm-workspace.md").exists()
    assert list(destination.rglob("skills-lock.json")) == []
    agents = (destination / "AGENTS.md").read_text()
    for trigger in AGENT_TRIGGERS:
        assert f"**{trigger}**" in agents
    context = (destination / "CONTEXT.md").read_text()
    assert project_name in context
    handoff = (destination / "docs/agents/handoff.md").read_text()
    assert "DavillyDevTeam/davilly-starter" not in handoff
    assert "just ci" not in handoff
    assert "pnpm nx run-many -t lint,typecheck,test,build" in handoff
    assert "accepted: true" in handoff
    assert "Blocked by" in handoff
    for relative in TASK_FILES:
        text = (destination / relative).read_text().lower()
        assert "orca" not in text, relative
        assert "justfile" not in text, relative
        assert "just ci" not in text, relative


def test_existing_directory_is_preserved(tmp_path: Path) -> None:
    marker = tmp_path / "keep.txt"
    _ = marker.write_text("keep")
    result = CliRunner().invoke(app, ["new", str(tmp_path)])
    assert result.exit_code != 0
    assert marker.read_text() == "keep"


def test_default_locales_are_english_and_portuguese(tmp_path: Path) -> None:
    destination = tmp_path / "my-app"
    generate(
        destination,
        "--project-name",
        'A "quoted" app',
        "--author",
        "A Team",
    )
    english = read(destination, "locales/en/common.json")
    portuguese = read(destination, "locales/pt-BR/common.json")
    assert "Your next chapter starts here." in english
    assert "Seu próximo capítulo começa aqui." in portuguese
    assert (destination / "locales/en/errors.json").exists()
    assert (destination / "locales/pt-BR/errors.json").exists()
    assert (destination / "apps/web/src/LanguageSwitcher.tsx").exists()
    assert not (destination / "apps/web/src/copy.ts").exists()
    answers = read(destination, ".copier-answers.yml")
    assert "pt-BR" in answers
    supported = read(destination, "apps/web/src/supportedLocales.ts")
    assert '"pt-BR"' in supported
    assert '"en"' in supported
    api = read(destination, "apps/api/i18n.py")
    assert '"pt-BR"' in api
    assert 'A \\"quoted\\" app' in supported
    assert "A Team" in read(destination, "LICENSE")
    assert (destination / "compose.yaml").exists()
    assert "Sign in" in english
    assert "Entrar" in portuguese
    project = read(destination, "pyproject.toml")
    compose = read(destination, "compose.yaml")
    assert "fastapi-users[sqlalchemy,oauth]==15.0.5" in project
    assert "redis" not in project.lower()
    assert "REDIS_URL" not in compose
    assert "image: redis" not in compose
    assert "DATABASE_URL" in compose
    assert "SECRET:" in compose
    assert "GOOGLE_OAUTH_CLIENT_ID" in compose
    assert "127.0.0.1:${API_PORT:-8000}:8000" in compose
    assert_agent_rails(destination, 'A "quoted" app')
    assert_api_style_clean(destination)


def test_apache_license_includes_full_text(tmp_path: Path) -> None:
    destination = tmp_path / "my-app"
    result = CliRunner().invoke(
        app,
        ["new", str(destination), "--license", "Apache-2.0", "--author", "A Team"],
    )
    assert result.exit_code == 0, result.output
    text = (destination / "LICENSE").read_text()
    assert "A Team" in text
    assert "Apache License" in text
    assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in text


def test_prod_deploy_docs_and_template_files(tmp_path: Path) -> None:
    destination = tmp_path / "my-app"
    result = CliRunner().invoke(app, ["new", str(destination)])
    assert result.exit_code == 0, result.output
    readme = (destination / "README.md").read_text()
    assert "Cloudflare Pages" in readme
    assert "VITE_API_URL" in readme
    assert "CORS_ORIGINS" in readme
    assert "DATABASE_URL" in readme
    assert "REDIS_URL" in readme
    assert "STRIPE_SECRET_KEY" in readme
    assert "GOOGLE_OAUTH_CLIENT_ID" in readme
    assert "GITHUB_OAUTH_CLIENT_ID" in readme
    assert "SECRET" in readme
    env_example = (destination / ".env.example").read_text()
    assert "VITE_API_URL=" in env_example
    assert "CORS_ORIGINS=" in env_example
    assert "DATABASE_URL=" in env_example
    api_main = (destination / "apps/api/main.py").read_text()
    assert "CORSMiddleware" in api_main
    assert "CORS_ORIGINS" in read(destination, "apps/api/config.py")
    assert "apiUrl" in (destination / "apps/web/src/api.ts").read_text()
    assert "VITE_API_URL" in (destination / "apps/web/src/vite-env.d.ts").read_text()
    compose = (destination / "compose.yaml").read_text()
    assert "API_PROXY_TARGET" in compose
    assert "VITE_API_URL" not in compose
    assert (destination / "Dockerfile.api").exists()
    assert_api_style_clean(destination)


def test_english_only_omits_portuguese(tmp_path: Path) -> None:
    destination = tmp_path / "my-app"
    generate(destination, "--locales", "en")
    assert (destination / "locales/en/common.json").exists()
    assert (destination / "locales/en/errors.json").exists()
    assert not (destination / "locales/pt-BR").exists()
    assert not (destination / "apps/web/src/LanguageSwitcher.tsx").exists()
    supported = read(destination, "apps/web/src/supportedLocales.ts")
    assert "pt-BR" not in supported
    api = read(destination, "apps/api/i18n.py")
    assert "pt-BR" not in api
    hits = files_mentioning(destination, "pt-BR")
    assert hits == [], hits


def test_portuguese_only_omits_english_files(tmp_path: Path) -> None:
    destination = tmp_path / "my-app"
    generate(destination, "--locales", "pt-BR")
    assert (destination / "locales/pt-BR/common.json").exists()
    assert not (destination / "locales/en").exists()
    assert not (destination / "apps/web/src/LanguageSwitcher.tsx").exists()
    supported = read(destination, "apps/web/src/supportedLocales.ts")
    assert "pt-BR" in supported
    assert '"en"' not in supported
    api = read(destination, "apps/api/i18n.py")
    assert 'DEFAULT_LOCALE: str = "pt-BR"' in api
    assert "tuple([" in api and "pt-BR" in api


@pytest.mark.parametrize("locales", ["en,pt-BR", "pt-BR,en"])
def test_both_locales_keep_switcher_and_default_english(
    tmp_path: Path, locales: str
) -> None:
    destination = tmp_path / "my-app"
    generate(destination, "--locales", locales)
    assert (destination / "locales/en").is_dir()
    assert (destination / "locales/pt-BR").is_dir()
    assert (destination / "apps/web/src/LanguageSwitcher.tsx").exists()
    supported = read(destination, "apps/web/src/supportedLocales.ts")
    assert 'export const defaultLocale: string = "en"' in supported


@pytest.mark.parametrize(
    "arguments",
    [
        ["--locales", "fr"],
        ["--locales", "en,fr"],
        ["--locales", ""],
        ["--license", "bogus"],
    ],
)
def test_invalid_flags_do_not_write(tmp_path: Path, arguments: list[str]) -> None:
    destination = tmp_path / "my-app"
    result = CliRunner().invoke(app, ["new", str(destination), *arguments])
    assert result.exit_code != 0
    assert not destination.exists()
