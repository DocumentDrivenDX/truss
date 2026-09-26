# Source me. SPIKE-002 storage bake-off environment.
# SPIKE: this directory (resolved from this file's location).
# WORK:  scratch area for sources, build trees, datasets and per-transaction logs (not committed).
# PGRT:  runtime root under the postgres home (the postgres OS user cannot traverse most scratch areas).
export SPIKE="${SPIKE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
export WORK="${WORK:-${TMPDIR:-/tmp}/truss-spike-002}"
export PGRT="${PGRT:-/var/lib/postgresql/bakeoff}"
# PGVER selects the cluster: 17 (default; UMF generator qualified for a PostgreSQL 17.4 subset) or 18 (repeat suites).
export PGVER="${PGVER:-17}"
if [ "$PGVER" = 18 ]; then
  export PGBIN="${PGBIN18:-/var/lib/postgresql/age-spike/pg18/bin}"   # PostgreSQL 18.6 built by SPIKE-001 (AGE not loaded)
  export PGDATA="$PGRT-pg18/data" PGPORT=54328
else
  export PGBIN="$PGRT-pg17/pg17/bin"
  export PGDATA="$PGRT-pg17/data" PGPORT=54317
fi
export PGHOST=/tmp PGUSER=postgres PGDATABASE="${PGDATABASE:-bakeoff}"
export PATH="$PGBIN:$PATH"
export BUN="${BUN:-/root/.bun/bin/bun}"
export UMF_DIR="${UMF_DIR:-$WORK/umf-master}"
export PSQL="psql -X -e -v ON_ERROR_STOP=0"
