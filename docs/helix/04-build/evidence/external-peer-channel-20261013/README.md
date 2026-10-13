# External peer guarded native TLS composition — 2026-10-13

This owned Linux AArch64 fixture composes an actual external peer with the
original accepted-catalog/typed Subject/shared UMF policy producer. Truss runtime
0.51-candidate, PostgreSQL 18.6, psycopg 3.3.6/libpq 18.6, Bun 1.4.2 and the
source-built Weft wheel match the earlier Linux replay inputs. The underlying
requirements remain SPIKE-004 CH01/CH02/CH04/CH05/CH08 and US-056 AC2/AC5/AC8/AC10,
US-057 AC7 prerequisites. This does not admit a protected backend or promote any
of the original 132 required cases.

The trusted owner supplies an explicit wildcard IPv4 listener, which the channel
accepts only with its original TLS1.3 server context. Literal addresses/ports are
validated before binding; non-loopback plaintext refuses. Eleven actual listener
and channel tests pass, including wildcard verified delivery and pre-bind refusal.

The external peer lives in a distinct container on an owned internal network.
It has a read-only root, all capabilities dropped, no mount, no published port
and no declared SQL credential. The service runs the original native fixture as
UID 1000, with read-only source mounts and its private local pgserver database.
Its SQL port is derived from the original connection URI. The peer probes that
port at the service address and must observe connection refusal or timeout;
authentication or SQL errors cannot qualify as network denial.

The owner hands the admitted peer only its one-operation bearer and public
certificate through private process stdin; the handoff is not persisted.
The peer verifies TLS1.3 and certificate identity 127.0.0.1 while routing to the
service network address. This fixed fixture identity is not production issuer or
DNS/service-identity admission. Unknown bearer refuses; the admitted invocation
returns only r1 with salary Withheld; reuse refuses. The service independently
checks original consumer SESSION_USER/CURRENT_USER and both native source
ShareLocks before the actual wire write. Exactly one original operation runs.

The first run's controls succeeded but strict cleanup recognition rejected
Docker's lowercase absent-object response. Independent inspection confirmed both
containers and the network were absent. The parser now accepts only the exact
observed absent forms; each nonce-labelled original resource ID is independently
removed and confirmed absent. Unknown inspections fail. Service responses have
60-second/16KiB bounds. Native fixture cleanup return values and class exceptions
are terminal. Final successful results and setup failure are retained.

The database remains inside the trusted service container. This is a composed
local-database custody option, not the earlier separate database-network topology.
The database's Unix socket/data files are private to the service; the peer has no
mounts. The writable service root, excluded Docker administrator, source mounts,
private bearer delivery and trusted callbacks remain explicit fixture premises.
Complete OS/diagnostic/endpoint closure, credential issuer/revocation/rotation,
continuous topology and handler authority, remote DB composition, recovery,
transport acknowledgment and every remaining backend case are unproved.
No Docker/kernel, cryptographic or native refinement theorem is claimed.

## Merged runtime 0.52 replay

Owner main9b7c5206 adds parallel-edge layout1.0 and runtime0.52-candidate.
Integration merge1e10db7b preserves those changes. The unchanged composed
external-peer controls pass again, with all three owned resources confirmed
absent. runtime052-* retains the separate replay; the earlier0.51 records
and independent review remain historical. No acceptance cases are promoted.

Both original native TLS tests also pass on0.52 (2 tests/12.452 seconds),
including event-trigger refusal with zero encoding and generic wire denial.
