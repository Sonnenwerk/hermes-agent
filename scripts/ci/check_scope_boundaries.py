#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys

SCOPE_RX = re.compile(r"\b(profile|scope|scopeKey|connection|connectionId|gateway|requestGateway)\b", re.I)
ASYNC_RX = re.compile(r"\b(await|Promise|then\s*\(|catch\s*\(|finally\s*\()", re.M)
STATE_RX = re.compile(r"\bset[A-Z][A-Za-z0-9_]*\s*\(|\$[A-Za-z0-9_]+\.set\s*\(", re.M)
DESKTOP_SUFFIXES = (".ts", ".tsx")


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout


def run_profile_checker(base: str, head: str) -> int:
    return subprocess.run(
        ["python", "scripts/check_profile_scope_patterns.py", "--base", base, "--head", head]
    ).returncode


def changed_files(base: str, head: str) -> list[str]:
    merge_base = git("merge-base", base, head).strip()
    return [
        p for p in git("diff", "--name-only", "--diff-filter=AM", merge_base, head, "--").splitlines()
        if p.startswith("apps/desktop/src/") and p.endswith(DESKTOP_SUFFIXES) and ".test." not in p
    ]


def async_scope_hotspots(base: str, head: str) -> list[str]:
    hotspots: list[str] = []
    merge_base = git("merge-base", base, head).strip()
    for path in changed_files(base, head):
        patch = git("diff", "--unified=20", merge_base, head, "--", path)
        added = "\n".join(
            line[1:] for line in patch.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        if SCOPE_RX.search(added) and ASYNC_RX.search(added) and STATE_RX.search(added):
            hotspots.append(path)
    return hotspots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument(
        "--scope-baseline",
        default=None,
        help="Optional common feature baseline used only for scope-pattern/advisory deltas.",
    )
    a = ap.parse_args()

    scope_base = a.scope_baseline or a.base

    rc = run_profile_checker(scope_base, a.head)
    if rc:
        return rc

    hotspots = async_scope_hotspots(scope_base, a.head)
    print(f"scope-boundaries: {len(hotspots)} async scope hotspot(s) (advisory)")
    for path in hotspots:
        print(
            "ADVISORY: async-scope hotspot: "
            f"{path} — verify late completions cannot mutate state after profile/scope/gateway changes"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
