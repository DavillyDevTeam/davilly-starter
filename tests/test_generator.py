import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from davilly_starter.main import app


def assert_api_style_clean(destination: Path) -> None:
    api = destination / "apps" / "api"
    for args in (
        ["ruff", "check", str(api)],
        ["ruff", "format", "--check", str(api)],
    ):
        result = subprocess.run(args, cwd=destination, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


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
    assert not (destination / "justfile").exists()
    assert "A Team" in (destination / "LICENSE").read_text()
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
