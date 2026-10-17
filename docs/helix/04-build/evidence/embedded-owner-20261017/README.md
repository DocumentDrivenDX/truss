# Embedded owner delivery candidate

The owner selected embedded JavaScript for the immediate Bun-free Python release,
with a native UMF library as its subsequent replacement. ADR-003 and the
implementation plan retain that scope. Python deployment requires neither Bun,
Node nor an external JavaScript process. Bun remains development/build/oracle
infrastructure.

The candidate pins mini-racer 0.14.1 / V8 14.4.258.23. Module syntax is compiled
from the original packaged UMF assets; their source bytes and owner manifests
remain unchanged. The separately pinned delivery manifest covers the transformed
module archive, virtual host and bundled polyfills/licenses. The virtual host
exposes packaged files and invocation data only. Native SQL admission remains
outside this computation boundary.

Local Python 3.11 / macOS ARM observations:

- 45 preparation, catalog-observation, exact-key and host-control tests passed.
- The packaged disclosure graph component suite passed all four test methods,
  including its ordered population and parallel-edge cases.
- Complete acceptance output (179,910 bytes), current-core catalog observations
  (444,227 bytes), preparation-source output (61,329 bytes) and Subject-key output
  (1,028 bytes) matched the pinned Bun 1.4.2 producer byte for byte.
- Installed wheel execution passed with every subprocess launch forbidden for
  acceptance, catalog observations, keys and held disclosure initialization.
- Infinite execution was interrupted by the deadline. Duplicate request IDs
  permanently fenced the held isolate and completed cleanup. Unpackaged file
  access was refused.
- The installed protected current-policy query passed against PostgreSQL 18.6,
  psycopg 3.3.6 and checksum-verified released Weft 0.4.41 with `/missing/bun`.

Two old report-capacity tests expected preparation to succeed without required
report evidence. The current Python boundary refused both inputs under the
original Bun producer as well. Their assertions now require the existing
`evidence_unavailable` / `evidence_too_large` refusals; no producer behavior changed.
The obsolete missing-Bun test now requires successful embedded preparation.

Linux qualification, the complete installed release workflow, original atomic
capacity and 1,000-node/1,000-edge workload remain publication gates. Local
observations do not establish their success. Disclosure remains its separately
gated candidate; this packaging change does not enroll an unpublished presence
compiler in the default query dependency.
