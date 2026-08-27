"""Allowlist and slot updater. No live network."""

from __future__ import annotations

from pathlib import Path

import pytest

from lucy.allowlist import AllowlistError, assert_public_url, load_allowlist
from lucy.persona import DEFAULT_ALLOWLIST, load_persona
from lucy.update import install_from_dir, sha256_file

SPEC = load_allowlist(DEFAULT_ALLOWLIST)
ROOT = Path(__file__).resolve().parents[1]


def test_wool_persona_passes_allowlist() -> None:
    persona = load_persona(ROOT / "data/personas/wool.json")
    tube = next(s for s in persona.surfaces if s.id == "youtube")
    assert "/results?" in tube.url
    assert_public_url("https://consent.youtube.com/", SPEC)
    assert_public_url("https://m.youtube.com/results?search_query=x", SPEC)


@pytest.mark.parametrize(
    "url",
    [
        "http://en.wikipedia.org/wiki/X",
        "https://127.0.0.1/",
        "https://169.254.169.254/latest/meta-data",
        "https://localhost/admin",
        "https://evil.example/pwn",
    ],
)
def test_refuses_bad_urls(url: str) -> None:
    with pytest.raises(AllowlistError):
        assert_public_url(url, SPEC)


def test_slot_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "tree"
    src.mkdir()
    version = src / "VERSION"
    version.write_text("0.9.9\n", encoding="utf-8")
    (src / "SHA256SUMS").write_text(f"{sha256_file(version)}  VERSION\n", encoding="utf-8")
    slots = tmp_path / "slots"
    current = tmp_path / "current"
    monkeypatch.setattr("lucy.update.SLOT_ROOT", slots)
    monkeypatch.setattr("lucy.update.CURRENT_LINK", current)
    dest = install_from_dir(src, "v0.9.9")
    assert (dest / "VERSION").read_text(encoding="utf-8") == "0.9.9\n"
    assert current.resolve() == dest


def test_slot_refuses_missing_sums(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "tree"
    src.mkdir()
    (src / "VERSION").write_text("0.9.9\n", encoding="utf-8")
    monkeypatch.setattr("lucy.update.SLOT_ROOT", tmp_path / "slots")
    monkeypatch.setattr("lucy.update.CURRENT_LINK", tmp_path / "current")
    with pytest.raises(SystemExit, match="SHA256SUMS"):
        install_from_dir(src, "v0.9.9")


def test_slot_refuses_bad_sum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "tree"
    src.mkdir()
    (src / "VERSION").write_text("0.9.9\n", encoding="utf-8")
    (src / "SHA256SUMS").write_text("0" * 64 + "  VERSION\n", encoding="utf-8")
    monkeypatch.setattr("lucy.update.SLOT_ROOT", tmp_path / "slots")
    monkeypatch.setattr("lucy.update.CURRENT_LINK", tmp_path / "current")
    with pytest.raises(SystemExit, match="checksum mismatch"):
        install_from_dir(src, "v0.9.9")
