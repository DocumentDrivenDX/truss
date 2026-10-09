"""Selected Draft 2020-12 static reference collector, not a schema validator."""
MAP_SCHEMAS = {'$defs', 'properties', 'patternProperties', 'dependentSchemas'}
ARRAY_SCHEMAS = {'allOf', 'anyOf', 'oneOf', 'prefixItems'}
SINGLE_SCHEMAS = {'items', 'contains', 'additionalProperties', 'propertyNames',
                  'unevaluatedItems', 'unevaluatedProperties', 'not', 'if', 'then', 'else',
                  'contentSchema'}


def static_refs(schema, *, root=True):
    if type(schema) is bool:
        return
    if type(schema) is not dict:
        raise ValueError('Original schema object/boolean required')
    if not root and '$id' in schema:
        raise ValueError('Nested original schema identity requires a scoped resolver')
    if '$dynamicRef' in schema or '$recursiveRef' in schema:
        raise ValueError('Dynamic reference scope requires separate original admission')
    if '$ref' in schema:
        reference = schema['$ref']
        if type(reference) is not str:
            raise ValueError('Non-string original reference')
        if reference and not reference.startswith('#'):
            yield reference.split('#', 1)[0]
    for keyword in MAP_SCHEMAS:
        if keyword in schema:
            mapping = schema[keyword]
            if type(mapping) is not dict:
                raise ValueError('Original schema map required')
            for child in mapping.values():
                yield from static_refs(child, root=False)
    for keyword in ARRAY_SCHEMAS:
        if keyword in schema:
            children = schema[keyword]
            if type(children) is not list:
                raise ValueError('Original schema array required')
            for child in children:
                yield from static_refs(child, root=False)
    for keyword in SINGLE_SCHEMAS:
        if keyword in schema:
            yield from static_refs(schema[keyword], root=False)
