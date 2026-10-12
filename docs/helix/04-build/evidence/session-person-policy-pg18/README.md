# Session-person policy selection evidence

The two native tests pass against actual `server_version_num=180006`.
They establish that role settings retain exact role names, `none` is reserved,
and a cached role setting can resolve to a replacement role OID after an
administrator renames and recreates a role. They do not qualify a protected
catalog facade or public acceptance implementation.

Run `check.py` with psycopg installed and `TRUSS_CENSUS_POSTGRES_BIN` pointing
to the released PostgreSQL 18.6 binary directory. The probe owns a temporary
cluster, registers cleanup before startup, and retains its directory when
shutdown is unconfirmed.
