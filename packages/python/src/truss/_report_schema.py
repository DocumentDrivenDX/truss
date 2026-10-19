# SPDX-License-Identifier: MIT OR Apache-2.0
"""Offline governing report schema validation; no acceptance authority."""
from hashlib import sha256
from importlib.resources import files
import json
from ._report_schema_pins import SCHEMA_PINS


def validate_complete_report(report):
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError
    from referencing import Registry, Resource
    registry=Registry()
    selected=None
    identities=set()
    for name,expected in SCHEMA_PINS.items():
        raw=files('truss').joinpath('_report_schemas',name).read_bytes()
        if sha256(raw).hexdigest()!=expected:
            raise ValueError('Original complete report schema pin mismatch')
        schema=json.loads(raw)
        Draft202012Validator.check_schema(schema)
        identity=schema.get('$id')
        if type(identity) is not str or not identity or identity in identities:
            raise ValueError('Unique original report schema identity required')
        identities.add(identity)
        registry=registry.with_resource(identity,Resource.from_contents(schema))
        if name=='acceptance-report-v0.3.proposal.schema.json':selected=schema
    if selected is None:raise ValueError('Complete report schema required')
    try:Draft202012Validator(selected,registry=registry).validate(report)
    except ValidationError as error:
        raise ValueError('Closed complete report wire required') from error
