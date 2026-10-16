# Combined stable-version compiler compatibility

The installed combined Weft 0.4.40 wheel and Truss adapter pass all 14 actual
PostgreSQL 18.6 schema/instance/read/page controls on Python 3.11.17. Bun is
explicitly pinned to 1.4.2. The owned native server stopped. The adapter requires
the original engine API for engine catalog execution and the page API for pages.
The existing Truss backend 0.4.39 / ABI 1.0 default remains unchanged; this is
compatibility evidence, not default migration to the Date ABI 1.1 profile.
Temporal qualification and snapshot-stream/protected-action gates remain held.
