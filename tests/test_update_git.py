"""Git TOFU pull and consent flags. Uses a local git repo, not GitHub."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lucy.update import (
    auto_update_mode,
    parse_github_origin,
    pull_git,
    report_status,
)


def test_parse_origin_from_url() -> None:
    assert parse_github_origin("https://github.com/acme/mythos-zine.git") == "acme/mythos-zine"
    assert parse_github_origin("git@github.com:acme/lucy.git") == "acme/lucy"
    with pytest.raises(SystemExit, match="not permitted"):
        parse_github_origin("https://evil.example/acme/lucy.git")


def test_auto_update_mode() -> None:
    assert auto_update_mode("") == ""
    assert auto_update_mode("off") == ""
    assert auto_update_mode("git") == "git"
    assert auto_update_mode("true") == "git"
    assert auto_update_mode("signed") == "signed"
    with pytest.raises(SystemExit, match="unknown"):
        auto_update_mode("botnet")


def _git(cwd: Path, *args: str) -> None:
    env = {
        **{k: v for k, v in __import__("os").environ.items()},
        "GIT_AUTHOR_NAME": "Lucy",
        "GIT_AUTHOR_EMAIL": "lucy@test",
        "GIT_COMMITTER_NAME": "Lucy",
        "GIT_COMMITTER_EMAIL": "lucy@test",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env)


def _bare_origin(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True, text=True)
    work = tmp_path / "work"
    work.mkdir()
    lucy = work / "lucy"
    lucy.mkdir()
    (lucy / "pyproject.toml").write_text("[project]\nname = \"lucy-ghost-zero\"\n", encoding="utf-8")
    (lucy / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    _git(work, "init", "-b", "main")
    _git(work, "add", ".")
    _git(work, "commit", "-m", "v0.1.0")
    _git(work, "tag", "v0.1.0")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "origin", "HEAD", "v0.1.0")
    return origin


def test_pull_git_flips_slot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    origin = _bare_origin(tmp_path)
    monkeypatch.setattr("lucy.update.SLOT_ROOT", tmp_path / "slots")
    monkeypatch.setattr("lucy.update.CURRENT_LINK", tmp_path / "current")
    monkeypatch.setattr("lucy.update.ORIGIN_CACHE", tmp_path / "cache")
    monkeypatch.setenv("LUCY_UPDATE_ALLOW_FILE", "1")
    monkeypatch.setenv("LUCY_UPDATE_GIT_URL", str(origin))
    dest = pull_git("acme/mythos-zine")
    assert (dest / "VERSION").read_text(encoding="utf-8") == "0.1.0\n"
    meta = json.loads((dest / "SOURCE.json").read_text(encoding="utf-8"))
    assert meta["trust"] == "git-tofu"
    assert meta["origin"] == "acme/mythos-zine"
    assert (tmp_path / "current").resolve() == dest


def test_no_consent_is_check_only(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LUCY_AUTO_UPDATE", raising=False)
    monkeypatch.setattr("lucy.update.CURRENT_LINK", Path("/nonexistent/current"))
    report_status("")
    assert auto_update_mode() == ""
