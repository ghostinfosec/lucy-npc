"""Load a dotenv-style file. Does not overwrite existing environment keys."""

from __future__ import annotations

import os
from pathlib import Path


def apply_env_file(path: Path, environ: dict[str, str] | None = None) -> None:
    """Read KEY=VAL lines into environ. Skips comments and keys already set. Disk read."""
    env = environ if environ is not None else os.environ
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in env:
            continue
        env[key] = value.strip().strip('"').strip("'")


def load_dotenv(root: Path) -> None:
    """Load cwd/.env then package-root/.env. Existing process env wins."""
    apply_env_file(Path.cwd() / ".env")
    apply_env_file(root / ".env")
