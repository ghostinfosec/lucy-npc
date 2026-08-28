#!/usr/bin/env python3
"""Download NetworkManager and dependencies for offline Pi first boot.

Side effects: writes .deb files to the output directory; may fetch Packages index from Debian.
"""
from __future__ import annotations

import gzip
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MIRROR = "https://ftp.debian.org/debian"
SUITE = "bookworm"
ARCH = "armhf"
COMPONENT = "main"
# dnsmasq: wifi-connect AP; iptables: routing; curl: connectivity probes.
SEEDS = ("network-manager", "curl", "dnsmasq", "iptables")


def fetch_packages_index() -> str:
    url = f"{MIRROR}/dists/{SUITE}/{COMPONENT}/binary-{ARCH}/Packages.gz"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return gzip.decompress(resp.read()).decode("utf-8", errors="replace")


def parse_packages(text: str) -> dict[str, dict[str, str]]:
    packages: dict[str, dict[str, str]] = {}
    block: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            if "Package" in block:
                packages[block["Package"]] = block
            block = {}
            continue
        key, _, value = line.partition(": ")
        block[key] = value
    if "Package" in block:
        packages[block["Package"]] = block
    return packages


def dep_names(depends: str) -> list[str]:
    if not depends:
        return []
    names: list[str] = []
    for part in depends.split(","):
        token = part.strip().split()[0]
        if token and token not in {"predepends", "|"}:
            names.append(re.sub(r"[|<>].*", "", token))
    return names


def resolve(index: dict[str, dict[str, str]], seeds: tuple[str, ...]) -> list[str]:
    resolved: set[str] = set()
    pending = list(seeds)
    while pending:
        name = pending.pop()
        if name in resolved or name.startswith("rpicam") or name == "debconf-2.0":
            continue
        if name not in index:
            print(f"warning: package not in index, skipping: {name}", file=sys.stderr)
            continue
        resolved.add(name)
        depends = index[name].get("Depends", "")
        for dep in dep_names(depends):
            if dep not in resolved:
                pending.append(dep)
    return sorted(resolved)


def download_debs(index: dict[str, dict[str, str]], names: list[str], out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name in names:
        meta = index[name]
        filename = meta.get("Filename", "")
        if not filename:
            print(f"warning: no Filename for {name}", file=sys.stderr)
            continue
        url = f"{MIRROR}/{filename}"
        dest = out_dir / Path(filename).name
        if dest.exists() and dest.stat().st_size > 0:
            count += 1
            continue
        print(f"fetch {name} -> {dest.name}")
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                dest.write_bytes(resp.read())
            count += 1
        except urllib.error.URLError as exc:
            print(f"error: failed to fetch {url}: {exc}", file=sys.stderr)
            raise
    return count


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} OUT_DIR", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1])
    print(f"index {SUITE}/{ARCH} from {MIRROR}")
    index = parse_packages(fetch_packages_index())
    names = resolve(index, SEEDS)
    print(f"resolved {len(names)} packages")
    count = download_debs(index, names, out_dir)
    print(f"downloaded {count} debs to {out_dir}")
    return 0 if count else 1


if __name__ == "__main__":
    raise SystemExit(main())
