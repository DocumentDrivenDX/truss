# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual additive profile bytes; no source-version inference or authority."""
from hashlib import sha256
from importlib.resources import files
import json


def profiles():
    root=files('truss').joinpath('_catalog_runtime')
    raw=root.joinpath('temporal-profiles.json').read_bytes()
    manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    if manifest['files'].get('temporal-profiles.json')!=sha256(raw).hexdigest():
        raise ValueError('Exact enrolled temporal profile definitions required')
    value=json.loads(raw)
    pins={}
    for entry in value['profiles']:
        if sha256(entry['definition'].encode()).hexdigest()!=entry['pin']['sha256']:
            raise ValueError('Actual temporal profile definition bytes required')
        if entry['name'] in pins:raise ValueError('Unique temporal profile selection required')
        pins[entry['name']]=entry['pin']
    return pins


def abi():
    root=files('truss').joinpath('_catalog_runtime')
    raw=root.joinpath('query-temporal-abi.json').read_bytes()
    manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    if manifest['files']['query-temporal-abi.json']!=sha256(raw).hexdigest():
        raise ValueError('Exact enrolled ABI1.3 descriptor required')
    return {'identity':'truss-postgresql-logical-query','version':'1.3','sha256':sha256(raw).hexdigest()}
