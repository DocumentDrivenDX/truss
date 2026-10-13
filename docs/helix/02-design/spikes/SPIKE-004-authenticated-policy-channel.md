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
