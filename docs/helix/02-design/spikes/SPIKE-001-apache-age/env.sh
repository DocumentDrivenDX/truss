# Source me. Runtime copy of the PG18+AGE build lives in the postgres home because the
# scratchpad is not traversable by the postgres OS user.
export SPIKE="${SPIKE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
export PGRT=/var/lib/postgresql/age-spike
export PGHOST=$PGRT PGPORT=54318 PGUSER=postgres PGDATABASE=postgres
export PATH=$PGRT/pg18/bin:$PATH
# -X: ignore psqlrc; -e: echo queries; errors do not stop the script (we want to record them)
export PSQL="psql -X -e -v ON_ERROR_STOP=0"
