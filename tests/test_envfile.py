"""Dotenv loader. No network."""

from pathlib import Path

from lucy.envfile import apply_env_file


def test_apply_env_file_skips_set_keys(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("LUCY_ENGINE=live_public\n# comment\nLUCY_STATUS_TOKEN=secret\n", encoding="utf-8")
    env = {"LUCY_ENGINE": "local"}
    apply_env_file(path, env)
    assert env["LUCY_ENGINE"] == "local"
    assert env["LUCY_STATUS_TOKEN"] == "secret"
