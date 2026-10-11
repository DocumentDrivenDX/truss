# Manifest artifact codec PostgreSQL 18.6 component

Eight focused native controls passed on the owner-selected pgserver-pg18 18.6.0
runtime and psycopg 3.3.6. The harness checks actual server_version_num 180006,
installs exact UMF owner-export bytes, uses a rollback-only fixture and savepoints,
and checks shutdown before releasing its temporary directory. Cleanup is registered
before startup. Statement timeout is 30 seconds; semantic refusals check SQLSTATE.

The initial two logs cover six original controls and two added document-count/malformed
UTF8/key/tag controls. The final log covers all eight native controls plus one
mocked cleanup-failure control, with corrected owned cleanup that preserves the
data directory when stop is unconfirmed. Wide artifact bytes agree with independently serialized
expected numeric-free JSON. The tested strings include NUL, quote, backslash and
Unicode; they contain no shorthand-escaped controls. This is codec evidence only:
no complete finalizer, accepted catalog, ordinary-person authority or public
capability is established. Hidden allocation and cumulative backend work are not
claimed. Owner UMF model/source/export are pinned by the new v0.4 definition;
older v0.3 definitions and parents are not reinterpreted.

Reproduce from repository root with the selected Python environment:

```sh
PYTHONPATH=packages/python/src python docs/helix/04-build/evidence/manifest-codec-pg18/check.py
```
