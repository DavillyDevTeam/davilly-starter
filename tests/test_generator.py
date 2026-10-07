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


@pytest.mark.parametrize("locales", ["en,pt-BR", "en", "pt-BR", "pt-BR,en"])
def test_generation(tmp_path: Path, locales: str) -> None:
    destination = tmp_path / "my-app"
    result = CliRunner().invoke(
        app,
        [
            "new",
            str(destination),
            "--project-name",
            'A "quoted" app',
            "--author",
            "A Team",
            "--locales",
            locales,
        ],
    )
    assert result.exit_code == 0, result.output
    catalog = (destination / "apps/web/src/copy.ts").read_text()
    assert 'A \\"quoted\\" app' in catalog
    assert ("Português" in catalog) == ("pt-BR" in locales)
    assert ("English" in catalog) == ("en" in locales)
    assert (destination / "compose.yaml").exists()
    assert "A Team" in (destination / "LICENSE").read_text()
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


@pytest.mark.parametrize("arguments", [["--locales", "fr"], ["--license", "bogus"]])
def test_invalid_flags_do_not_write(tmp_path: Path, arguments: list[str]) -> None:
    destination = tmp_path / "my-app"
    result = CliRunner().invoke(app, ["new", str(destination), *arguments])
    assert result.exit_code != 0
    assert not destination.exists()
