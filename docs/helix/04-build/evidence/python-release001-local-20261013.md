# Initial release local check — 2026-10-13

Built and installed Truss0.0.1 and Weft0.4.3 from their release-only source
checkouts, preserving unfinished numeric facet work separately. Distribution
metadata, weft.__version__ and Truss's installed site-packages origin agree.
The basic public PG18 adopter workflow passes: accepted catalog, committed
mutation/replay, included receipt, relationship query, rolled-back dry-run,
created import, three committed feed transactions and committed ACK.

The build frontend also creates the Truss wheel from its source distribution.
Local source-rebuilt wheel SHA256: `6cadbdba625d3ca38e0c357f79086c5205443cfd1352c155d67fc7d349feb04c`.
Local Weft wheel SHA256: `1ea3a94a9c19cda8f3edb86c35e9d71f2bd8f728a6d59896eb474a78ef12f00c`.
These are local verification bytes, not substitutes for the Actions-built assets.
Publication remains gated on installed Actions checks using the exact package
artifact and published dependency wheels. Bun1.4.2, PG18.6/pgserver-pg18==18.6.1
and psycopg3.3.6 are retained. No facet, stable-layout, managed-service or complete
protected-engine claim is introduced.
