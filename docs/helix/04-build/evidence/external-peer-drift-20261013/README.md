# External peer native authority drift — 2026-10-13

The actual composed TLS peer observes native event-trigger admission refusal on
Truss0.52-candidate/PostgreSQL18.6. The owner-only fixture option
`--refuse-event-triggers` executes native `SET LOCAL event_triggers=off` after the
original mapping/source-cut setup. The same original guarded producer runs once;
it returns Error with the exact native event-trigger gate diagnostic. A patched
encoding observer is never invoked. No evaluation/output is substituted.

The external peer independently asserts unknown-bearer401, admitted503 with
exact body {}, and subsequent403. It receives no decision or native diagnostic.
Its probe of the original selected SQL port is denied. Both containers and the
network are confirmed absent after cleanup. The unchanged positive mode also
passes: exact r1/salaryWithheld, native consumer identity and both source cuts
before delivery, one operation and denied reuse/SQL probe.

The mode is controlled by the trusted test owner; peer requests cannot choose
it or alter the native connection. Both orchestration and service refuse unknown
mode arguments. The complete prior private fixture premises, source-built Weft
candidate, fixed certificate identity and service-local database limitations from
../external-peer-channel-20261013/README.md still apply. This is a selected
SPIKE-004 CH04/CH05/CH08, US-056AC9/US-057AC7 prerequisite. It does not close
all inventory drift classes, establish native authority lifetime, or promote
truss.B11 or any of the 132 required backend cases. No new formal/refinement
or production readiness claim is made.
