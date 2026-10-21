# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit named fixture revisions; the frozen original archive stays intact.

This is test authoring, not a Truss name fallback. Each added authored name is
the fixture element ID; the revised bytes receive their own source revision.
"""
from hashlib import sha256
import json
from truss import CatalogDocument


def named_revision(fixture):
    original=fixture['sourceText'].encode()
    assert sha256(original).hexdigest()==fixture['sha256']
    source=json.loads(original)
    missing=[]
    for module in source['modules']:
        for element in module['elements']:
            if element['kind'] in ('record','field') and not element.get('name'):
                missing.append((module['id'],element['id']))
                element['name']=element['id']
    revised=json.dumps(source,indent=2,ensure_ascii=False).encode()
    return CatalogDocument(source['id'],sha256(revised).hexdigest(),revised),tuple(missing)
