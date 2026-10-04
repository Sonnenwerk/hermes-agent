#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REMOTE_PIPE = re.compile(r"(curl|wget)\b[^\n|]*\|\s*(bash|sh)\b", re.I)
WRITE_ALL = re.compile(r"^\s*permissions\s*:\s*write-all\s*$", re.M)
WORKFLOW_DISPATCH = re.compile(r"^\s*workflow_dispatch\s*:", re.M)
PULL_REQUEST_TARGET = re.compile(r"^\s*pull_request_target\s*:", re.M)
DYNAMIC_CHECKOUT = re.compile(r"\bref\s*:\s*\$\{\{[^}]+\}\}", re.M)
DIRECT_CACHE = re.compile(r"uses\s*:\s*actions/cache(?:/save)?@", re.M)
SETUP_PM = re.compile(r"uses\s*:\s*\./\.github/actions/setup-pm\b", re.M)
CACHE_FALSE = re.compile(r"^\s*cache\s*:\s*['\"]?false['\"]?\s*$", re.M)
CACHE_PY_FALSE = re.compile(r"^\s*cache-python\s*:\s*['\"]?false['\"]?\s*$", re.M)
CACHE_NODE_FALSE = re.compile(r"^\s*cache-node\s*:\s*['\"]?false['\"]?\s*$", re.M)


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise SystemExit(p.stderr or p.returncode)
    return p.stdout


def workflow_trust_failures(path: str, text: str) -> list[str]:
    failures: list[str] = []
    dynamic = bool(DYNAMIC_CHECKOUT.search(text))
    if not dynamic:
        return failures

    if PULL_REQUEST_TARGET.search(text):
        failures.append(f"{path}: pull_request_target with dynamic checkout ref")

    if WORKFLOW_DISPATCH.search(text):
        cache_writes = bool(DIRECT_CACHE.search(text))
        setup_pm_cache_enabled = bool(SETUP_PM.search(text)) and not (
            CACHE_FALSE.search(text) and CACHE_PY_FALSE.search(text) and CACHE_NODE_FALSE.search(text)
        )
        if cache_writes or setup_pm_cache_enabled:
            failures.append(
                f"{path}: workflow_dispatch + dynamic checkout can write reusable caches"
            )

    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    a = ap.parse_args()

    mb = git("merge-base", a.base, a.head).strip()
    changed = [
        x
        for x in git("diff", "--name-only", "--diff-filter=AM", mb, a.head, "--").splitlines()
        if x
    ]

    failures: list[str] = []
    advisory: list[str] = []

    if not Path("SECURITY.md").is_file():
        failures.append("SECURITY.md missing")

    for path in changed:
        try:
            text = git("show", f"{a.head}:{path}")
        except SystemExit:
            continue

        if path.startswith(".github/workflows/"):
            if WRITE_ALL.search(text):
                failures.append(f"{path}: workflow uses permissions: write-all")
            failures.extend(workflow_trust_failures(path, text))

        if path.startswith(("skills/", "optional-skills/", "plugins/", "scripts/")) and REMOTE_PIPE.search(text):
            failures.append(f"{path}: remote download piped directly to shell")

        if path.startswith(("gateway/", "plugins/", "skills/", "optional-skills/", "hermes_cli/")):
            advisory.append(path)

    print(f"security-contract: {len(failures)} blocking, {len(advisory)} sensitive file(s)")
    for item in failures:
        print(f"BLOCKING: {item}")
    for item in advisory[:50]:
        print(f"ADVISORY: review against SECURITY.md: {item}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
