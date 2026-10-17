# Explicit stream-bound refusal

The installed candidate passes five focused adapter lifecycle tests and 16 basic
native checks on PostgreSQL18.6, psycopg3.3.6 and Bun1.4.2. A two-row prefix ends
with `QueryStreamRefused` carrying `limits` / `stream_row_limit` after successful
cleanup. A short final-bound fetch returns three rows against a four-row bound
and completes normally. Cleanup failure and deadline precedence are covered by
the adapter tests; native early close, idle transaction and no-portal checks pass.

`native-basic.json` reports the actual scope and stopped owned server. The
2,500-row campaign and SDK generated-query catalog checks did not run. The
original full `--streams` selector still includes both; `--streams-basic` selects
only direct native typed read/page/stream controls and records the narrower scope.
`pins.json` binds the source and installed wheel; `cohort.json` identifies the
retained explicit local SDK/Weft cursor cohort. Ordinary queries remain pinned to
published Weft0.4.40. This does not qualify public SDK dependency availability,
protected-policy/temporal behavior or the separate release performance gate.

The first attempt stopped at SDK CLI regeneration with
`CATALOG_STALE: query lacks generated source`: its copied generated fixture lacked
the source metadata required by the retained SDK. `earlier-cli-failure.json`
retains the nine checks completed before that failure and confirms server stop;
it is not a stream pass. The targeted retry exercises original native bindings
and DTOs directly, without altering generated source or bypassing native admission.
