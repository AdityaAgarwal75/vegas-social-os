#!/usr/bin/env python3
"""Migrate the Vegas-owned Caddy route, leaving other sites untouched."""
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

def repair(text: str, domain: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9.-]+", domain):
        raise ValueError("Invalid hostname")
    first, last = "# BEGIN VSO " + domain, "# END VSO " + domain
    start = text.find(first + "\n")
    if start < 0:
        return text
    end = text.find(last, start)
    if end < 0:
        raise ValueError("Unterminated Vegas-owned Caddy block")
    block = text[start:end]
    pattern = r"(?m)^([ \t]*(?:header[ \t]+)?Referrer-Policy[ \t]+)no-referrer([ \t]*)$"
    changed, count = re.subn(pattern, r"\g<1>origin\2", block)
    if not count:
        if re.search(r"(?m)^\s*(?:header\s+)?Referrer-Policy\s+origin\s*$", block):
            return text
        raise ValueError("Unexpected Vegas Caddy Referrer-Policy; configure origin explicitly")
    return text[:start] + changed + text[end:]

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: repair-caddy-referrer.py Caddyfile domain")
    path = Path(sys.argv[1])
    before = path.read_text()
    after = repair(before, sys.argv[2])
    if after != before:
        backup = path.with_name(path.name + ".vso-oauth-backup-" +
                                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        shutil.copy2(path, backup)
        path.write_text(after)
        print("Repaired Vegas-owned OAuth response policy; Caddy backup created")
