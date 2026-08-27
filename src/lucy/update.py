"""Pull-only updater. Lucy phones the origin for code, never for orders.

Side effects: git fetch/clone (if consented), optional HTTPS GET to GitHub
releases, writes a slot directory, flips a symlink. Never overwrites STATE_DIR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

log = logging.getLogger("lucy.update")

DEFAULT_ORIGIN = os.environ.get("LUCY_UPDATE_ORIGIN", "")
SLOT_ROOT = Path(os.environ.get("LUCY_SLOT_ROOT", "/opt/lucy/slots"))
CURRENT_LINK = Path(os.environ.get("LUCY_CURRENT_LINK", "/opt/lucy/current"))
STATE_DIR = Path(os.environ.get("LUCY_STATE_DIR", "/etc/lucy"))
ORIGIN_CACHE = Path(os.environ.get("LUCY_ORIGIN_CACHE", "/var/lib/lucy/origin"))

_ORIGIN_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_COPY_IGNORE = shutil.ignore_patterns(
    ".venv", "logs", ".env", "node_modules", ".git", ".dress", ".next"
)


def parse_github_origin(value: str) -> str:
    """Normalize owner/repo from a slug or GitHub URL. No I/O."""
    text = value.strip()
    if not text:
        raise SystemExit("empty update origin")
    if text.startswith("git@"):
        _, _, rest = text.partition(":")
        text = rest
    if text.endswith(".git"):
        text = text[: -len(".git")]
    if "://" in text or text.startswith("github.com/"):
        parsed = urlparse(text if "://" in text else f"https://{text}")
        host = (parsed.hostname or "").lower()
        if host not in {"github.com", "www.github.com"}:
            raise SystemExit(f"update origin host not permitted: {host}")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise SystemExit(f"could not parse owner/repo from {value}")
        text = f"{parts[0]}/{parts[1]}"
    if not _ORIGIN_RE.match(text):
        raise SystemExit(f"origin must be owner/repo, not {value!r}")
    return text


def auto_update_mode(raw: str | None = None) -> str:
    """Return '', 'git', or 'signed'. No I/O."""
    text = (raw if raw is not None else os.environ.get("LUCY_AUTO_UPDATE", "")).strip().lower()
    if text in {"", "0", "false", "no", "off"}:
        return ""
    if text in {"1", "true", "yes", "on", "git"}:
        return "git"
    if text in {"signed", "release", "cosign"}:
        return "signed"
    raise SystemExit(f"unknown LUCY_AUTO_UPDATE={text}")


def git_url_for_origin(origin: str) -> str:
    """HTTPS GitHub URL, or a test file URL. No network."""
    slug = parse_github_origin(origin)
    override = os.environ.get("LUCY_UPDATE_GIT_URL", "").strip()
    if override:
        if os.environ.get("LUCY_UPDATE_ALLOW_FILE") != "1":
            raise SystemExit("LUCY_UPDATE_GIT_URL is only for tests")
        return override
    return f"https://github.com/{slug}.git"


def lucy_source_root(tree: Path) -> Path:
    """Prefer a nested lucy/ if this is the zine monorepo. Reads pyproject.toml."""
    nested = tree / "lucy" / "pyproject.toml"
    if nested.is_file():
        return tree / "lucy"
    pyproject = tree / "pyproject.toml"
    if pyproject.is_file():
        return tree
    raise SystemExit("origin tree has no lucy project (missing pyproject.toml)")


def _get(url: str) -> bytes:
    host = urlparse(url).hostname or ""
    if host not in {
        "github.com",
        "api.github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    }:
        raise ValueError(f"update origin host not permitted: {host}")
    req = Request(url, headers={"User-Agent": "lucy-ghost-zero-updater"})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 — host pinned above
        return resp.read()


def latest_release(origin: str) -> dict:
    """origin is 'owner/repo'. Fetches GitHub release JSON."""
    slug = parse_github_origin(origin)
    url = f"https://api.github.com/repos/{slug}/releases/latest"
    return json.loads(_get(url).decode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sums(source: Path) -> None:
    """Fail closed unless SHA256SUMS exists and matches. Side effect: reads files."""
    sums = source / "SHA256SUMS"
    if not sums.is_file():
        raise SystemExit("refusing slot without SHA256SUMS")
    for line in sums.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        if not name:
            digest, _, name = line.partition(" ")
        rel = Path(name.strip())
        if rel.is_absolute() or ".." in rel.parts:
            raise SystemExit(f"illegal path in SHA256SUMS: {name}")
        target = source / rel
        if not target.is_file():
            raise SystemExit(f"missing file listed in SHA256SUMS: {rel}")
        actual = sha256_file(target)
        if actual != digest.strip().lower():
            raise SystemExit(f"checksum mismatch: {rel}")


def install_from_dir(source: Path, tag: str) -> Path:
    """Copy a verified tree into the next slot. Does not touch STATE_DIR."""
    verify_sums(source)
    SLOT_ROOT.mkdir(parents=True, exist_ok=True)
    dest = SLOT_ROOT / tag
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, ignore=_COPY_IGNORE)
    CURRENT_LINK.parent.mkdir(parents=True, exist_ok=True)
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    CURRENT_LINK.symlink_to(dest)
    log.info("current -> %s", dest)
    return dest


def _git(args: list[str], cwd: Path | None = None) -> str:
    """Run git with a fixed argv. Side effect: subprocess."""
    git = shutil.which("git")
    if not git:
        raise SystemExit("git is required for auto-updates")
    result = subprocess.run(
        [git, *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "git failed").strip()
        raise SystemExit(err)
    return (result.stdout or "").strip()


def resolve_ref(cache: Path, requested: str) -> str:
    """Pick a tag or an explicit extra-consent ref. Side effect: git."""
    if requested:
        return requested
    tags = _git(["tag", "-l", "v*", "--sort=-v:refname"], cwd=cache)
    first = next((line for line in tags.splitlines() if line.strip()), "")
    if not first:
        raise SystemExit(
            "no v* tags on origin; tag a release or set LUCY_UPDATE_REF=main "
            "(extra consent to follow a floating branch)"
        )
    return first


def write_git_trust(source: Path, meta: dict[str, str]) -> None:
    """Record TOFU provenance and checksums for the copy step. Writes files."""
    version = source / "VERSION"
    if not version.is_file():
        raise SystemExit("origin tree missing VERSION")
    (source / "SOURCE.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    sums = [
        f"{sha256_file(version)}  VERSION",
        f"{sha256_file(source / 'SOURCE.json')}  SOURCE.json",
    ]
    (source / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")


def pull_git(origin: str, ref: str = "") -> Path:
    """Clone/fetch origin and flip a slot. Git TOFU, not cosign. Skips STATE_DIR."""
    slug = parse_github_origin(origin)
    url = git_url_for_origin(slug)
    ORIGIN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if (ORIGIN_CACHE / ".git").is_dir():
        _git(["remote", "set-url", "origin", url], cwd=ORIGIN_CACHE)
        _git(["fetch", "--tags", "--force", "origin"], cwd=ORIGIN_CACHE)
    else:
        if ORIGIN_CACHE.exists():
            shutil.rmtree(ORIGIN_CACHE)
        _git(["clone", url, str(ORIGIN_CACHE)])
    requested = ref or os.environ.get("LUCY_UPDATE_REF", "").strip()
    resolved = resolve_ref(ORIGIN_CACHE, requested)
    _git(["checkout", "--force", resolved], cwd=ORIGIN_CACHE)
    commit = _git(["rev-parse", "HEAD"], cwd=ORIGIN_CACHE)
    source = lucy_source_root(ORIGIN_CACHE)
    stage = ORIGIN_CACHE.parent / ".lucy-stage"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(source, stage, ignore=_COPY_IGNORE)
    write_git_trust(
        stage,
        {
            "origin": slug,
            "ref": resolved,
            "commit": commit,
            "trust": "git-tofu",
        },
    )
    tag = resolved if resolved.startswith("v") else f"git-{commit[:12]}"
    meta_path = CURRENT_LINK / "SOURCE.json"
    if CURRENT_LINK.exists() and meta_path.is_file():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if existing.get("commit") == commit:
            log.info("already at %s (%s)", tag, commit[:12])
            shutil.rmtree(stage, ignore_errors=True)
            return CURRENT_LINK.resolve()
    dest = install_from_dir(stage, tag)
    shutil.rmtree(stage, ignore_errors=True)
    return dest


def report_status(origin: str) -> None:
    """Log slot + consent. No network."""
    current = str(CURRENT_LINK.resolve()) if CURRENT_LINK.exists() else "none"
    mode = auto_update_mode() or "off"
    log.info(
        "current=%s origin=%s auto_update=%s state=%s",
        current,
        origin or "(unset)",
        mode,
        STATE_DIR,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Lucy pull-only updater")
    parser.add_argument("--origin", default=DEFAULT_ORIGIN, help="GitHub owner/repo")
    parser.add_argument("--from-dir", type=Path, help="Install a local tree (tests / first flash)")
    parser.add_argument("--from-git", action="store_true", help="One-shot git pull (human consent)")
    parser.add_argument("--tag", default="local")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    origin = args.origin.strip() if args.origin else ""

    if args.check:
        report_status(origin)
        return

    if args.from_dir:
        install_from_dir(args.from_dir, args.tag)
        return

    if args.from_git:
        if not origin:
            raise SystemExit("set LUCY_UPDATE_ORIGIN=owner/repo or pass --origin")
        pull_git(origin)
        return

    mode = auto_update_mode()
    if not mode:
        log.info("auto-update off (no consent). pass --from-git or set LUCY_AUTO_UPDATE=git")
        report_status(origin)
        return

    if mode == "signed":
        raise SystemExit(
            "signed GitHub-release updates are not implemented. "
            "use LUCY_AUTO_UPDATE=git (TOFU, same trust as git clone) or --from-dir"
        )

    if not origin:
        raise SystemExit("consent is on but LUCY_UPDATE_ORIGIN is empty")
    pull_git(origin)


if __name__ == "__main__":
    main()
