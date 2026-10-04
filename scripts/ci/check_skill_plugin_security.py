#!/usr/bin/env python3
from __future__ import annotations
import argparse, re, subprocess, sys

EXEC_PATTERNS = [
    (re.compile(r"\bos\.system\s*\("), "os.system"),
    (re.compile(r"\bsubprocess\.(Popen|run|call|check_output)\s*\("), "subprocess execution"),
    (re.compile(r"(curl|wget)\b[^\n|]*\|\s*(bash|sh)\b", re.I), "remote pipe-to-shell"),
    (re.compile(r"\beval\s*\("), "eval"),
    (re.compile(r"\bexec\s*\("), "exec"),
]

def git(*args: str) -> str:
    p=subprocess.run(["git",*args],capture_output=True,text=True,encoding="utf-8",errors="replace")
    if p.returncode: raise SystemExit(p.stderr or p.returncode)
    return p.stdout

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default="origin/main")
    ap.add_argument("--head",default="HEAD")
    a=ap.parse_args()
    mb=git("merge-base",a.base,a.head).strip()
    changed=[x for x in git("diff","--name-only","--diff-filter=AM",mb,a.head,"--").splitlines()
             if x.startswith(("skills/","optional-skills/","plugins/"))]
    findings=[]
    for path in changed:
        text=git("show",f"{a.head}:{path}")
        for rx,label in EXEC_PATTERNS:
            if rx.search(text):
                findings.append((path,label))
    print(f"skill-plugin-security: {len(changed)} changed file(s), {len(findings)} executable-risk finding(s)")
    for path,label in findings:
        print(f"BLOCKING: {path}: {label}")
    if changed:
        print("ADVISORY: inspect SKILL.md instructions, installers, hooks, lifecycle scripts, network and credential access without executing unknown targets.")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
