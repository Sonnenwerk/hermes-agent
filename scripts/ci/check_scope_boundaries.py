#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys

def run(*args: str) -> int:
    return subprocess.run(list(args)).returncode

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    a=ap.parse_args()
    # Reuse Hermes' own validated advisory profile-scope detector.
    rc=run("python","scripts/check_profile_scope_patterns.py","--base",a.base,"--head",a.head)
    if rc:
        return rc
    print("scope-boundaries: profile-scope checker completed (advisory)")
    print("ADVISORY: manually review async completions that can outlive profile/gateway/connection changes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
