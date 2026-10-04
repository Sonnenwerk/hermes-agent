#!/usr/bin/env python3
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path

REMOTE_PIPE = re.compile(r"(curl|wget)\b[^\n|]*\|\s*(bash|sh)\b", re.I)
WRITE_ALL = re.compile(r"^\s*permissions\s*:\s*write-all\s*$", re.M)

def git(*args: str) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise SystemExit(p.stderr or p.returncode)
    return p.stdout

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    a=ap.parse_args()
    mb=git("merge-base",a.base,a.head).strip()
    changed=[x for x in git("diff","--name-only","--diff-filter=AM",mb,a.head,"--").splitlines() if x]
    failures=[]
    advisory=[]
    if not Path("SECURITY.md").is_file():
        failures.append("SECURITY.md missing")
    for path in changed:
        try:
            text=git("show",f"{a.head}:{path}")
        except SystemExit:
            continue
        if path.startswith(".github/workflows/") and WRITE_ALL.search(text):
            failures.append(f"{path}: workflow uses permissions: write-all")
        if path.startswith(("skills/","optional-skills/","plugins/","scripts/")) and REMOTE_PIPE.search(text):
            failures.append(f"{path}: remote download piped directly to shell")
        if path.startswith(("gateway/","plugins/","skills/","optional-skills/","hermes_cli/")):
            advisory.append(path)
    print(f"security-contract: {len(failures)} blocking, {len(advisory)} sensitive file(s)")
    for item in failures: print(f"BLOCKING: {item}")
    for item in advisory[:50]: print(f"ADVISORY: review against SECURITY.md: {item}")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
