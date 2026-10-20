#!/usr/bin/env python3
"""Validate Truss model-primary source policy without needing a signing key.

This is the pull-request gate. Main-branch publication separately seals the
same exact inventory with the registered build key and runs `verify --all`.
"""
import json
import re
from pathlib import Path

ROOT = Path.cwd()
EXPECTED = {
    "website/content/_index.md",
    "website/content/model.md",
    "website/content/evidence.md",
    "website/content/start.md",
}


def fail(message: str) -> None:
    raise SystemExit(f"model-primary source policy: {message}")


def main() -> None:
    config = json.loads((ROOT / ".innsigle/config.json").read_text())
    colo = json.loads((ROOT / ".innsigle/colo.json").read_text())
    if config.get("kind_from_frontmatter") != {"field": "composition"}:
        fail("config must select the composition frontmatter field")
    if colo.get("composition") != "model-primary":
        fail("default colophon must be model-primary")
    patterns = config.get("content_globs")
    if not isinstance(patterns, list) or not patterns:
        fail("content_globs must be configured")
    discovered = {
        path.relative_to(ROOT).as_posix()
        for pattern in patterns
        for path in ROOT.glob(pattern)
        if path.is_file()
    }
    if discovered != EXPECTED:
        fail(f"source inventory differs: expected {sorted(EXPECTED)}, found {sorted(discovered)}")
    for rel in sorted(discovered):
        text = (ROOT / rel).read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
        if not match:
            fail(f"{rel} has no YAML frontmatter")
        values = []
        for line in match.group(1).splitlines():
            if line.startswith("composition:"):
                values.append(line.split(":", 1)[1].strip().strip("\"'"))
        if values != ["model-primary"]:
            fail(f"{rel} must declare composition: model-primary exactly once")
    print(f"PASS: {len(discovered)} configured sources declare model-primary")


if __name__ == "__main__":
    main()
