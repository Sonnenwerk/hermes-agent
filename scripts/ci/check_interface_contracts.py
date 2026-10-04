#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys

def call(cmd: list[str]) -> int:
    return subprocess.run(cmd).returncode

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    a=ap.parse_args()
    rc=call(["python","scripts/ci/check_public_surface.py","--base",a.base,"--head",a.head])
    if rc:
        return rc
    print("interface-contracts: public-surface diff complete (advisory)")
    print("NOTE: TypeScript/Python type checks remain the blocking proof for changed call signatures.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
