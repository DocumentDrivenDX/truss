#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Print the CHANGELOG.md section for one version (used for GitHub Release notes)."""
from pathlib import Path
import re
import sys

version = sys.argv[1].removeprefix('v')
text = (Path(__file__).resolve().parents[1] / 'CHANGELOG.md').read_text()
match = re.search(rf'^## \[?{re.escape(version)}\]?[^\n]*\n(.*?)(?=^## |\Z)', text, re.S | re.M)
if not match or not match.group(1).strip():
    raise SystemExit(f'CHANGELOG.md has no section for {version}')
print(match.group(1).strip())
