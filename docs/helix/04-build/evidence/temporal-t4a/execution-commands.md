# T4A-P focused execution

The local macOS PostgreSQL bootstrap attempts are retained in
`current054-local-native-attempt/`. Both ended before a test ran. Use one
focused `ubuntu-24.04` hosted job with Python 3.11 and Bun; do not dispatch the
full release workflow or its matrix for this probe.

From the repository root, prepare separately verified wheels in the hosted job:

```sh
set -euo pipefail
WHEELHOUSE="$RUNNER_TEMP/t4a-wheels"
mkdir -p "$WHEELHOUSE/weft" "$WHEELHOUSE/runtime"
python -m pip download --only-binary=:all: --no-deps --dest "$WHEELHOUSE" \
  --index-url https://pypi.org/simple umf-truss==0.0.54
TRUSS_WHEEL="$WHEELHOUSE/umf_truss-0.0.54-py3-none-any.whl"
test "$(shasum -a 256 "$TRUSS_WHEEL" | cut -d ' ' -f 1)" = \
  4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52
python -m pip download --only-binary=:all: --no-deps --no-index \
  --find-links https://github.com/DocumentDrivenDX/weft/releases/expanded_assets/v0.4.51 \
  --dest "$WHEELHOUSE/weft" weft-sql==0.4.51
WEFT_WHEEL="$(find "$WHEELHOUSE/weft" -maxdepth 1 -name 'weft_sql-0.4.51-*.whl' -print -quit)"
test -n "$WEFT_WHEEL"
python scripts/verify-weft-release-wheel.py "$WEFT_WHEEL"
python scripts/install-local-runtime.py --wheelhouse "$WHEELHOUSE/runtime" --download-only
PGSERVER_WHEEL="$(find "$WHEELHOUSE/runtime" -maxdepth 1 -name 'pgserver_pg18-18.6.1-*.whl' -print -quit)"
test -n "$PGSERVER_WHEEL"
PGSERVER_SUMS="$WHEELHOUSE/runtime/SHA256SUMS"
```

Install the old public cohort and exact native runtime into a fresh environment.
The wheelhouse contains the checksum-verified pgserver artifact; the remaining
dependencies resolve from PyPI under the repository's exact constraints:

```sh
python -m venv "$RUNNER_TEMP/t4a054"
VENV="$RUNNER_TEMP/t4a054/bin/python"
"$VENV" -m pip install --constraint packages/python/isolated-runtime-constraints.txt \
  --find-links "$WHEELHOUSE/runtime" \
  "$TRUSS_WHEEL" "$WEFT_WHEEL" "$PGSERVER_WHEEL" \
  'psycopg[binary]==3.3.6'
```

Run only the existing cursor baseline and authentic capture companion. Both
tests share their single class-owned local PostgreSQL cluster:

```sh
CAPTURE="$RUNNER_TEMP/t4a-public054-capture.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/python/tests \
TRUSS_BUN_EXECUTABLE="$(command -v bun)" \
"$VENV" scripts/probe-weft-abi12-cohort.py capture \
  --output "$CAPTURE" \
  --truss-wheel "$TRUSS_WHEEL" \
  --weft-wheel "$WEFT_WHEEL" \
  --pgserver-wheel "$PGSERVER_WHEEL" \
  --pgserver-checksums "$PGSERVER_SUMS" \
  2>&1 | tee "$RUNNER_TEMP/t4a-public054-capture.log"
```

Replay the retained bytes in the existing separate 0.4.56 probe environment.
This phase only invokes raw compiler/checker APIs and never executes SQL:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/python/src \
/private/tmp/truss-temporal-owner-probe/bin/python \
  scripts/probe-weft-abi12-cohort.py replay \
  --capture "$CAPTURE" \
  --output "$RUNNER_TEMP/t4a-weft056-replay.json" \
  2>&1 | tee "$RUNNER_TEMP/t4a-weft056-replay.log"
```

Retain both JSON outputs and logs as the job artifacts. A structured raw Weft
refusal is an expected diagnostic finding; it blocks adoption and does not
count as a passed T4A gate. The existing Truss `compiler()` refusal remains a
separate recorded result.
