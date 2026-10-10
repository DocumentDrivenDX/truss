from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parents[3]
files = sorted(root.rglob('*.md'))
identities = {}
duplicates = []
missing_ids = []
broken_paths = []
for path in files:
    text = path.read_text()
    frontmatter = text.split('---', 2)[1] if text.startswith('---') else ''
    identity = re.search(r'^  id: (.+)$', frontmatter, re.M)
    if identity:
        key = identity[1].strip()
        if key in identities:
            duplicates.append([key, identities[key], str(path.relative_to(root))])
        identities[key] = str(path.relative_to(root))
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        local = target.strip('<>').split('#')[0]
        if local and not (path.parent / local).exists():
            broken_paths.append([str(path.relative_to(root)), target])
for path in files:
    text = path.read_text()
    frontmatter = text.split('---', 2)[1] if text.startswith('---') else ''
    for target in re.findall(r'^    - id: (.+)$', frontmatter, re.M):
        if target.strip() not in identities:
            missing_ids.append([str(path.relative_to(root)), target.strip()])
result = {'scope': 'local Markdown file targets and ddx identity references only; no anchor or semantic validation', 'artifactIds': len(identities), 'duplicateIds': duplicates, 'missingLinkIds': missing_ids, 'brokenFileTargets': broken_paths}
print(json.dumps(result, indent=2))
if duplicates or missing_ids or broken_paths:
    sys.exit(1)
