# T4A-P selected Linux execution

The dedicated `weft-abi12-probe` job in `.github/workflows/python-runtime.yml`
uses one Ubuntu 24.04 runner with Python 3.11 and Bun 1.4.3. The dispatch input
`weft_abi12_probe` defaults to false. Selecting true skips `released-runtime`
and runs only the probe job. It has no matrix or publication step.

The job obtains the exact public Truss 0.0.54 wheel, frozen Weft 0.4.51 wheel,
and PostgreSQL 18.6.1 runtime wheel. It verifies Truss against the audited public
hash, Weft wheels against their official release SHA256SUMS, and pgserver with
the existing checksum-verifying runtime installer. It creates fresh runner
virtual environments at `$RUNNER_TEMP/t4a054` and `$RUNNER_TEMP/t4a056`.

After Sol's wiring approval is relayed, select this workflow on the reviewed
branch. This command has not been dispatched as part of the wiring patch:

```sh
gh workflow run python-runtime.yml --ref codex/temporal-completion \
  -f weft_abi12_probe=true
```

The capture invocation uses the runner's old-cohort interpreter and the exact
verified input paths produced by the setup step:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/python/tests \
TRUSS_BUN_EXECUTABLE=bun \
"$T4A_OLD_PYTHON" scripts/probe-weft-abi12-cohort.py capture \
  --output "$T4A_ROOT/evidence/public054-capture.json" \
  --truss-wheel "$T4A_TRUSS_WHEEL" --weft-wheel "$T4A_WEFT051_WHEEL" \
  --pgserver-wheel "$T4A_RUNTIME_WHEEL" \
  --pgserver-checksums "$T4A_ROOT/inputs/runtime/SHA256SUMS"
```

The two native cases are the inherited original three-row cursor baseline and
its capture companion. They share one class-owned PostgreSQL cluster. Cleanup
observes the original postmaster PID, stops the runtime, requires actual
`pg_ctl status` exit code 3 and that PID's absence, and only then deletes owned
data. Uncertain cleanup fails the probe and retains the data. The cleanup proof
and test-run receipt are independent files, including on failure.

Replay runs in the fresh runner environment containing only the candidate Weft
cohort. Every captured payload's UTF-8/base64/hash/length and original argument
correspondence are checked before importing or calling the candidate. Existing
output, temporary-output, cleanup or run receipts refuse reuse.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/python/src \
"$T4A_REPLAY_PYTHON" scripts/probe-weft-abi12-cohort.py replay \
  --capture "$T4A_ROOT/evidence/public054-capture.json" \
  --output "$T4A_ROOT/evidence/weft056-replay.json" \
  --weft-wheel "$T4A_WEFT056_WHEEL" \
  --weft-checksums "$T4A_ROOT/inputs/weft056/SHA256SUMS"
```

The replay receipt records the actual Linux wheel and official checksum file,
and binds its native archive member to the loaded installed module. It records
the unchanged Truss cohort guard refusal separately from raw compiler/page/
checker results. A structured Weft refusal is retained diagnostic evidence and
blocks adoption. Candidate SQL is never executed.

The job always uploads the input wheels/checksums, captures, raw replay output,
logs, environment inventories and cleanup receipts. Historical local startup
failures remain under `current054-local-native-attempt/`; neither ran a test.
