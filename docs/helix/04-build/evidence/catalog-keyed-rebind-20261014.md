# Native63 keyed-rebind implementation evidence

Truss0.0.27/native63 with Weft0.4.28/backend33 was exercised on the local
DocumentDrivenDX PG18.6 runtime and psycopg3.3.6. Four basic UMF0.7/0.8 public
workflows passed in75.076s: successful field/key acceptance, exact lookup/query,
one version increment, postcommit history reconstruction, and qualified duplicate
refusal without catalog effects. One populated native62→63 upgrade passed
in14.708s using the original previously tested SDK26 candidate wheel; original
registration report bytes remained exact before and after the new acceptance.

The Truss candidate wheel SHA256 is
`d99fae8903db6c024c300905f50c82cf5ed884a09819090f69b27df98dbb400e`.
Bundled source hashes/archive062 and paired dependency metadata were verified.
Weft cargo check and ABI3 wheel build passed; installed paired compiler loads.
Astra Ultra reviewed semantic paths, migration and fixtures; two guard issues and
predecessor-provenance/authority-placement issues were corrected before execution.

The checksum-verified published SDK26 predecessor run is still pending its
publication. No managed-database qualification or publication claim follows from
these local tests. Concurrent security owner changes were retained in Weft main.

The selected catalog capability now mirrors the assembly's `source_version`
keyword, preserving the0.7.0 default and explicit Bun selection. The existing
UMF0.8 successful workflow through that capability passed1/16.085s against current
source with the matching built Weft28 wheel; lookup/query/postcommit history are
included. This follow-up is source execution, distinct from the earlier installed
candidate wheel whose checksum is recorded above. Module boundaries pass1072.

Final published-predecessor verification passed1/10.939s using the checksum-verified
published SDK26 wheel `cbeb21fda06b21f5452a24ac8ec21f4a7aa108597893d86df33c00baf549ee85`
and published Weft28 ARM wheel
`497f70e0bd9481463182b058c1cf674cd17484e303dc35146e78efb645e227a2`.
The rebuilt installed SDK27 candidate is
`9839511db661827d5c3e84a184f82f65f12e0b6dc114ca2b4156816b2bce8a77`.
Original reports, real predecessor import/native version, upgrade disposition,
new profiles, key lookup and query passed. Truss26 workflow38513465205 and Weft28
workflow38514022606 both succeeded. Astra Ultra approves SDK27 tagging after final
main boundary verification; its existing workflow remains the publication gate.
