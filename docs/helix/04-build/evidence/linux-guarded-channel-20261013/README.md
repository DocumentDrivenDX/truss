# Linux guarded native TLS replay — 2026-10-13

The original `test_security_catalog_channel_native` tests pass in an owned Linux
AArch64 Docker runtime: 2 tests / 18.008 seconds on current Truss main
`bd8ad3da` (catalog runtime 0.51-candidate). The earlier 0.50 replay also passed
2 tests / 20.682 seconds. This is portability evidence for the SPIKE-004
CH01/CH02/CH04/CH05 prerequisites linked to US-056 AC2/AC8/AC9 and US-057 AC7.
It does not admit a backend or change the 132-case required inventory.

The runtime uses Python 3.11.17, Bun 1.4.2, psycopg 3.3.6/libpq 18.6 and the
original pgserver-pg18 18.6.1 Linux release wheel, verified against its release
SHA256SUMS. Weft's original Rust source at 6fc0a279 was compiled with Rust
1.90.0/maturin 1.9.6, locked dependencies and truss-postgresql-pg18. Its wheel
reports 0.1.0; it is a source candidate, not the public Weft 0.4.16 release.
Source-file and wheel hashes are retained. Truss and UMF are mounted read-only;
the PostgreSQL process and tests run under a declared UID/GID 1000 account.

Observed controls: unknown CA and bearer refusal precede native dispatch;
caller/SQL substitutions refuse; the consumer receives only r1 with salary
Withheld; both source ShareLocks exist before wire publication; disabling
native event triggers yields a generic refusal with zero encoding and no retry.

The first attempted run omitted Docker stdin and executed no test. The next
run failed initdb because UID 1000 lacked a passwd entry; its full failure is
retained in native-channel.log. Declaring the owned test account corrected the
fixture. Subsequent logs contain actual test execution and success.

This replay uses container loopback with a local database, not an external
untrusted peer on the isolated frontend/backend networks. Source roots in the
runner are local inputs, and the Docker bases are tags rather than an immutable
rebuild recipe. Retained image and input hashes identify this run. Composed
peer reachability, credential custody, OS/diagnostic closure and full backend
admission remain unverified. No native refinement theorem is claimed.
