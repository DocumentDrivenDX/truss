"""Private archive row correspondence; complete observation/authority external."""
from dataclasses import dataclass
from hashlib import sha256

COLUMNS = ('archive_row_id', 'installation_id', 'artifact_role', 'artifact_identity',
           'artifact_bytes', 'artifact_sha256', 'artifact_identity_sha256')
ROLES = ('bundle', 'expected_inventory', 'installed_inventory', 'input', 'marker')


@dataclass(frozen=True)
class ArchiveObservation:
    original_rows: tuple
    matches: bool


def compare_archive_rows(columns, rows, installation, expected, maximum_rows,
                         maximum_bytes):
    """Compare complete admitted rows without collapsing duplicate observations.

    Expected tuples are original (role, identity, immutable bytes). The caller
    independently admits release membership, original producer/descriptor/
    completion, coherent cut, rights and resources. Empty results prove neither
    absence nor prior attempt settlement. No public drift/unavailable is minted.
    """
    def refuse(): raise ValueError('installation-archive:unavailable')
    if any(type(v) is not int or v < 0 or v > 9007199254740991 for v in (maximum_rows, maximum_bytes)): refuse()
    if type(columns) not in (tuple, list) or tuple(columns) != COLUMNS: refuse()
    if type(installation) is not str or not installation or type(rows) not in (tuple, list) or len(rows)>maximum_rows or type(expected) is not tuple or len(expected)>maximum_rows: refuse()
    total=0; originals=[]
    # Preflight all retained rows before hashing any original bytes.
    for row in rows:
        if type(row) not in (tuple, list) or len(row)!=7: refuse()
        row_id, owner, role, identity, value, digest, identity_digest=row
        if (type(row_id) is not str or not row_id.isascii() or not row_id.isdigit()
                or len(row_id)>19 or row_id.startswith('0') or int(row_id)>9223372036854775807): refuse()
        if type(value) is not bytes or not value or type(digest) is not bytes or len(digest)!=32 or type(identity_digest) is not bytes or len(identity_digest)!=32: refuse()
        if any(type(v) is not str or not v or '\0' in v for v in (owner,role,identity)) or role not in ROLES: refuse()
        for cell in row:
            try: size=len(cell.encode('utf8')) if type(cell) is str else len(cell)
            except UnicodeError: refuse()
            if size>maximum_bytes-total: refuse()
            total+=size
        originals.append(tuple(row))
    registered=[]; seen_expected=set()
    for entry in expected:
        if type(entry) is not tuple or len(entry)!=3: refuse()
        role,identity,value=entry
        if type(role) is not str or role not in ROLES or type(identity) is not str or not identity or type(value) is not bytes or not value: refuse()
        key=(role,identity)
        if key in seen_expected: refuse()
        seen_expected.add(key);registered.append(entry)
    observed=[]; ids=set()
    for row_id,owner,role,identity,value,digest,identity_digest in originals:
        if row_id in ids or owner!=installation: refuse()
        ids.add(row_id)
        if sha256(value).digest()!=digest or sha256(identity.encode('utf8')).digest()!=identity_digest: refuse()
        observed.append((role,identity,value))
    # Sorting retains duplicate full identities and does not rely on route hashes.
    return ArchiveObservation(tuple(originals), sorted(observed)==sorted(registered))
