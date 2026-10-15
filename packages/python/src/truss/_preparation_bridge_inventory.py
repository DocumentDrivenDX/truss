"""Private bridge source adjunct; no installer, permission or allocator proof."""
from importlib.resources import files
from ._security_source_epoch_installation import _sources


def preparation_bridge_inventory_source():
    # Reuse the original checked owner barrier source. Never take a caller body.
    source = dict(_sources())['routine-ddl-barrier.sql']
    body = source.split('AS $$', 1)[1].split('$$;', 1)[0]
    template = files('truss').joinpath('_security_bootstrap', 'preparation-bridge-inventory.sql').read_text()
    if template.count('__ORIGINAL_DDL_BODY__') != 1:
        raise ValueError('Original bridge source template required')
    return template.replace('__ORIGINAL_DDL_BODY__', "'" + body.replace("'", "''") + "'")
