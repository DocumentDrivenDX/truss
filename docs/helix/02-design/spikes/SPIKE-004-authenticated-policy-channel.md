---
ddx:
  id: SPIKE-004
  type: tech-spike
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-007
      kind: informed_by
    - id: FEAT-008
      kind: informed_by
---

# Authenticated policy publication channel

This spike tests the transport boundary required by the mediated backend option
in UMF CONTRACT-063. It does not activate a protected Truss profile. The full
Weft query surface remains Truss's intended public query surface; this fixture
carries one previously authored invocation, rather than defining SQL coverage.

The shared semantic policy remains independent of transport and storage. An
original operation resolves the ontology and typed native Subject, captures the
actual accepted catalog, evaluates the existing UMF policy and constructs the
immutable safe decision. The channel receives no new policy interpretation or
flat/graph-specific permission vocabulary. Other storage adapters can publish
their qualified operation through the same conceptual boundary, but require their
own native admission and isolation evidence.

## Requirements and native boundary

| Requirement | Design and required observation | Acceptance prerequisite |
| --- | --- | --- |
| CH01 authenticated invocation | Owner-private 32-byte credential; actual wire comparison before any native dispatch. Unknown credential produces a fixed denial and zero operation calls. | US-056 AC2/AC8 |
| CH02 original identity | Trusted owner binds the operation to its original native caller/executor contexts. Peer body, route or headers cannot choose actor, source, model, executor or SQL. Native SESSION_USER remains consumer in the exercising fixture. | US-056 AC2/AC10 |
| CH03 closed invocation | Exact POST route, original request bytes, unique length/type/auth headers and identity encoding. Subject substitution, SQL route, unknown query strings and transfer encoding refuse before original operation entry. | US-056 AC5/AC7 |
| CH04 protected publication | Only the original guarded producer supplies immutable bounded bytes to the wire writer. Native source cuts are observed before the actual socket write. Native refusal sends a fixed error with no raw diagnostic or decision. | US-057 AC7 |
| CH05 no implicit reuse | The channel consumes the original operation before dispatch, including failure. A second valid request refuses without retrying native evaluation or publication. | US-057 AC2/AC7 |
| CH06 uncertain wire outcome | Once publication begins, an exception closes the channel without appending an error or repeating delivery. Original native outcome and channel failure remain available to the trusted owner. HTTP200/flush does not prove remote acknowledgment or successful producer settlement. | US-057 AC7 |
| CH07 resource scope | Fixed request body, 1MiB immutable publication limit and a five-second absolute header/body admission deadline, plus socket inactivity timeout; one serial server and one operation. Complete header/time/CPU/heap and slow-peer budgets need separate qualification. | US-056 AC10 |
| CH08 credential/topology isolation | Prove untrusted peers cannot obtain SQL credentials, reach a database endpoint, or access diagnostic/storage paths. Qualify TLS, issuer/rotation and principal binding. | US-056 AC5/AC8/AC10 |

CH08 is deliberately unfinished. Loopback and a secret wire token do not prove
native network or OS isolation. The owned PostgreSQL fixture retains excluded
administrative access and original local authentication premises. A bearer token
is not an issuer proof, a database credential or a reusable native capability.

## Protocol and lifetime

The trusted owner creates one local channel with one private credential and the
original guarded operation. The peer sends the fixed read-resource invocation.
Credential and closed request correspondence precede operation entry. The
original operation performs its own native Subject, source, fact and publication
checks; the HTTP writer runs as its synchronous receiver. Caller-owned outer
transactions and cuts remain with the embedding owner. This channel does not
commit, roll back, reopen, pool or renew them.

The operation is consumed before invoking the producer, so uncertainty cannot
cause an automatic retry. The owner must close this channel and settle its
original transactions; a future invocation requires independently admitted
contexts. The current channel does not serve streams, pages, writes, arbitrary
queries or an installation/readiness endpoint. Those capabilities remain required
by the backend test plan and must use their real compiler/native contracts.

Wire publication and producer settlement are distinct observations. The existing
native publication host supplies the conditional ordering and cut premises; this
spike adds actual credential routing and network delivery observations. Neither
unit substitution nor a successful socket flush proves native refinement,
cryptographic security, remote exactly-once delivery or total endpoint closure.

## Validation and next admission gates

The channel tests use actual loopback HTTP, independently authored expected
status/body observations and counts of operation calls. Native controls use the
actual source-guarded accepted-catalog operation: the peer receives only r1 with
salary Withheld while the original native caller remains consumer and both source
ShareLocks exist. A native event-trigger-setting refusal yields a generic error,
zero encoding and no retry. Failed initial controls retain the rejected standard
Accept-Encoding header defect and its correction.

Before backend activation, provide independent SQL/network/OS/credential route
inventory and adversarial access controls; actual issuer/TLS/principal rotation
and revocation; complete native writer/role/handler/config lifetime; recovery,
clock/stream/page behavior and all original B/L acceptance cases. The current
132-case inventory is unchanged. Evidence belongs in
`../../04-build/evidence/catalog-authenticated-channel-20261013/`.


## Local verified TLS subprofile — 2026-10-13

The owner may explicitly supply an exact stock server SSLContext with a TLS1.3
minimum. Each accepted socket has a five-second timeout before the stock SSL
handshake; the negotiated version must be TLSv1.3 before HTTP parsing or bearer
credential handling. A failed handshake closes without a plaintext fallback.
The existing absolute five-second header/body admission deadline is separate
from this preceding handshake phase. None retains the earlier explicit local
plaintext spike; it does not activate a protected production profile.

Owned test certificates declare IP SAN127.0.0.1, use a private0600 key in an
owned temporary directory and are removed after execution. The exercising peer
uses CA and hostname verification. Unknown CA and wrong hostname refuse before
operation entry; weakening the owner context and negotiating TLS1.2 still causes
zero HTTP/operation dispatch. Actual incomplete handshakes are bounded and allow
the queued verified peer to proceed. Certificate/key issuer authenticity,
revocation/rotation, deployment names, context/stdlib/admin lifetime, isolated
SQL/storage/diagnostic topology and complete CH08 remain unqualified.

Final runtime0.50 checks pass11/46.335s (nine channel controls, two native TLS
publication controls) on Python3.11.17/OpenSSL3.5.9/PostgreSQL18.6. Astra19
independent actual loopback TLS controls pass; they substitute the guarded
operation and do not independently execute PostgreSQL. No new backend case
promotion. Evidence: `../../04-build/evidence/catalog-tls-channel-20261013/`.


### Owned private SQL network domain — 2026-10-13

SPIKE-004 CH08 has a selected IPv4 topology prerequisite: exact PostgreSQL18.6
image on an internal backend network, peer on a separate internal frontend, and
trusted service domain on both. Native service_reader is non-super/non-bypass and
reads the independently seeded private fact count1. Peer DNS, known DB address
and selected service-facing/back-facing SQL addresses deny even with deliberately
compromised valid SQL credentials. Excluded Docker administrator attachment makes
the same peer/credential read succeed; detachment restores denial. Seven native
controls pass with all five owned resources confirmed absent after cleanup.

Astra23 independent harness controls pass after fixes: daemon/access inspection
failure is unknown rather than absent; every cleanup is attempted and recorded
without replacing the primary failure; auth/SQL/exec failures cannot qualify as
network denial. Exact nonce-labeled resource IDs are removed; shared resources
are not touched. Z3 4.15.4 yields one UNSAT and three SAT over an explicit network
membership model: direct private SQL exclusion is conditional, excluded topology
change restores access, and an arbitrary application relay can disclose private
facts despite direct network separation. This is not Docker/kernel refinement.

Trace CH08 and US-056 AC5/AC8/AC10/UMF CONTRACT-063/STP-056 prerequisites. The
service fixture is sleep plus trusted psql probes, not the composed TLS/guarded
producer. Credential/issuer nonexposure, app route inventory, daemon/OS/IPv6 and
continuous topology/authority lifetime remain open. No backend promotion; the
original132 cases remain required. Evidence:
`docs/helix/04-build/evidence/network-isolation-20261013/receipt.json`.

## Linux native runtime replay — 2026-10-13

The original guarded TLS tests pass on Linux AArch64 with actual PostgreSQL
18.6 and source-built Weft: 2 tests on merged Truss 0.51-candidate.
[Inputs, controls, setup failure and replay evidence](../../04-build/evidence/linux-guarded-channel-20261013/README.md)
qualify this portability prerequisite. CH08 external-peer composition and the
132-case backend inventory remain unfinished.


### External peer guarded TLS composition — 2026-10-13

An actual peer container calls the original source-guarded accepted-catalog
producer over verified TLS1.3. Unknown bearer and reuse refuse; the admitted
peer receives r1 with salary Withheld, with original consumer identity and both
source ShareLocks checked before wire publication. The peer has no mounts or
declared SQL credentials; a probe of the original service-local database port
is denied. All three nonce-owned resources are confirmed absent. Eleven channel
and listener tests pass; non-loopback plaintext refuses before socket binding.

This qualifies the service-private local database option, not separate remote
DB topology or complete endpoint/OS/issuer authority. CH01/CH02/CH04/CH05/CH08,
US-056 AC2/AC5/AC8/AC10 and US-057 AC7 remain prerequisites, with no promotion
of the original132 cases. [Evidence and limitations](../../04-build/evidence/external-peer-channel-20261013/README.md).

Concurrent owner layout1.0/runtime0.52 changes are preserved. The composed
external-peer controls pass on merged runtime0.52; both original native TLS
tests pass (2/12.452s), with separate runtime052 evidence retained.


### External peer native event-trigger drift — 2026-10-13

The composed ordinary peer observes generic503{} after the trusted owner changes
native event_triggers tooff. The original guarded operation runs once and refuses
at its native gate, with zero encoding calls; reuse and TCP SQL probes refuse.
All three owned resources are confirmed absent. The original positive composed
read also passes. This is US-056AC9/US-057AC7 and SPIKE-004 CH04/CH05/CH08
prerequisite evidence, not truss.B11 or backend admission. Other native authority
changes remain required. [Inputs, outcomes and scope](../../04-build/evidence/external-peer-drift-20261013/README.md).


### Exact direct helper ACL admission — 2026-10-13

Committed PUBLIC EXECUTE drift passed the previous helper snapshot comparison.
The private native verifier now requires the complete exact owner/caller direct
ACL on both helpers before Subject encoding and again before publication. Five
committed ACL mutations plus two original TLS cases pass (7/77.081s); a separate
late excluded-administrator committed grant is refused before publication
(1/11.700s). The external TLS peer sees generic denial, zero encoding and no
retry; positive read still passes, with owned cleanup confirmed. Conditional Z3
ACL equality has3UNSAT/2SAT, without native/effective-role refinement. US-056AC9,
US-057AC7 and SPIKE-004 prerequisites only, no truss.B11/case promotion.
[Counterexample, controls and limitations](../../04-build/evidence/helper-acl-drift-20261013/README.md).

Concurrent relationship-name/runtime0.53 owner work is preserved. Six native
ACL controls plus both TLS cases pass together (8/50.388s); positive and denial
external-peer paths pass with complete owned cleanup. Separate runtime053
evidence qualifies this merged replay; the earlier0.52 evidence is historical.


### Committed helper owner/definition drift — 2026-10-13

Four actual committed owner/SECURITY INVOKER/search_path/volatility mutations
refuse at the exact helper snapshot gate before encoding/publication (4/24.831s)
with event_triggers on and fresh executor custody. The external TLS peer also
observes the committed owner mismatch as generic denial; zero encoding, no
retry and all-three owned cleanup are confirmed. Positive external read still
passes. This is US-056AC9/US-057AC7 and SPIKE-004 CH04/CH05/CH08 prerequisite
coverage only, not truss.B11 or a new native refinement claim.
[Inputs, setup failure and outcomes](../../04-build/evidence/helper-definition-drift-20261013/README.md).


### Native accepted-catalog source installation — 2026-10-13

The positive guarded fixture now uses a private native initializer rather than
placeholder marker hashes. It recaptures accepted sources and archives exact
release-manifest/assessment bytes, verifies complete persisted readback, pins
installer resolution and refuses substituted/existing state. Native rollback,
ordinary refusal, hostile resolution and suppressed-insert controls pass. Its
native namespace target is consumed by source-epoch issuance. Pending commit
and security_ready=False remain explicit: this is one installed-profile factory
dependency, not complete issuer/current-authority or backend admission.
[Source installation and evidence](../../04-build/evidence/catalog-source-installation-20261013/README.md).

Owner binary-equality/runtime0.54 changes are preserved. The original target
is consumed by positive source-epoch issuance. Ten native controls pass together
(69.457s); external guarded delivery and all-three cleanup also pass. Separate
runtime054 records preserve this replay without promoting backend admission.


### Native guard generation coupling — 2026-10-13

Accepted preparation now retains its checked native guard tuple; guarded catalog
read checks exact descriptors/types and tuple under SHARE NOWAIT before/after
evaluation. Actual generation is transported losslessly to shared UMF instead
of a fixed label. Stale/NUMERIC/nativegeneration2 controls pass (3/20.502s),
late changed generation refuses after successful evaluation (1/9.767s), and
external guarded delivery/cleanup passes. This is comparison-only metadata;
trusted fixture facts and complete installed-profile authority remain unresolved.
No backend case is promoted. [Qualified controls](../../04-build/evidence/catalog-authority-generation-20261013/README.md).

### Installed mapping source correspondence — 2026-10-13

The selected epoch-backed producer now verifies the original installed mapping
request, compiler handoff and dependency mapping alongside release/catalog
sources before native Subject capture and again before publication. The archive
SHARE cut survives delivery. This advances CH04's source binding; exact byte
comparison does not authenticate the installer/compiler/issuer or establish
complete authority. Older three-record archives refuse this path pending explicit
migration. [Native source evidence](../../04-build/evidence/catalog-installed-mapping-20261013/README.md).

### Original packaged epoch infrastructure — 2026-10-13

Positive source setup now uses the versioned private installer rather than manual
SQL loading. Its original packaged sources and exact selected native readback
supply pending construction identity for CH04. Actual TLS publication/cleanup
still passes. Direct superuser installation, excluded handler ownership and
administrative quiescence remain premises; the result creates no protected
caller authority. [Installer evidence](../../04-build/evidence/source-epoch-installation-20261013/README.md).

### Initial source factory issuance — 2026-10-13

The protected publication fixture now consumes one initial source factory result,
which binds original marker/infrastructure, source archives and qualified facts
to actual native issuer/pointer readback. Pure profile0.4 pins packaged source
identity; pending construction does not authorize a caller. Actual post-issuance
pointer deletion refuses before factory handoff and preserves prior caller work.
[Factory evidence](../../04-build/evidence/catalog-source-factory-20261013/README.md)
advances CH04 source composition while complete authority/lifetime remains open.

### Installed native Subject helpers — 2026-10-13

Positive source setup now registers original native role/Staff-key bindings and
installs/readbacks helpers through the library. Native second-session observation
confirms own Subject, wrong-actor refusal and private map exclusion. Effective
helper-owner reads are required; an owner-only ACL is insufficient. TLS source
factory publication still passes. [Construction evidence](../../04-build/evidence/catalog-subject-installation-20261013/README.md)
advances CH02/CH04 without complete authority/lifetime or multi-role read admission.
