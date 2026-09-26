#!/usr/bin/env bash
# Fetch by primary key three ways, same run: A PK, C partial expression index, C UMF key-tuple bytea table
# (requires harness/key_tuple.ts to have built c.object_key). Key bytes computed in SQL here; a runtime would bind them.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
W=$WORK/bench/keytuple; rm -rf $W; mkdir -p $W; N=${N:-3000}; REPS=${REPS:-3}
echo '\set k random(1, 20000)' > $W/h
{ cat $W/h; echo 'SELECT * FROM sales.customers WHERE id = :k;'; } > $W/a_pk.sql
{ cat $W/h; echo "SELECT id, props::text, retained::text FROM c.object o WHERE o.type_id = 1 AND ((o.props->>'1')::bigint) = :k;"; } > $W/c_expr.sql
{ cat $W/h; echo "SELECT o.id, o.props::text, o.retained::text FROM c.object_key k JOIN c.object o ON o.id = k.object_id WHERE k.type_id = 1 AND k.key_id = 'identity' AND k.key_bytes = convert_to('UMFK1','UTF8') || '\\x0102'::bytea || decode(lpad(to_hex(length(:k::text)),2,'0'),'hex') || convert_to(:k::text,'UTF8');"; } > $W/c_tuple.sql
echo "== $(psql -X -At -c 'select version()'); prepared; N=$N REPS=$REPS"
echo "parity: $(for k in 1 77 19999; do psql -X -At -c "SELECT count(*) FROM c.object_key k JOIN c.object o ON o.id = k.object_id WHERE k.type_id = 1 AND k.key_id = 'identity' AND k.key_bytes = convert_to('UMFK1','UTF8') || '\\x0102'::bytea || decode(lpad(to_hex(length('$k')),2,'0'),'hex') || convert_to('$k','UTF8')"; done | paste -sd,)"
printf "%-10s %4s %8s %8s %8s\n" query run p50 p95 p99
for q in a_pk c_expr c_tuple; do
  pgbench -n -M prepared -c 1 -t 300 -f $W/$q.sql >/dev/null 2>&1
  for r in $(seq 1 $REPS); do rm -f $W/log.*; (cd $W && pgbench -n -M prepared -c 1 -t $N -f $W/$q.sql -l --log-prefix=log >/dev/null 2>&1)
    cat $W/log.* | awk '{print $3/1000.0}' | sort -n > $W/$q.lat; n=$(wc -l < $W/$q.lat)
    p() { awk -v n=$n -v p=$1 'NR==int((n*p)+0.999999){printf "%.3f", $1; exit}' $W/$q.lat; }
    printf "%-10s %4s %8s %8s %8s\n" $q $r $(p 0.50) $(p 0.95) $(p 0.99); done
done
psql -X -At -c "EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT o.id, o.props::text FROM c.object_key k JOIN c.object o ON o.id = k.object_id WHERE k.type_id = 1 AND k.key_id = 'identity' AND k.key_bytes = convert_to('UMFK1','UTF8') || '\\x0102'::bytea || decode(lpad(to_hex(length('4242')),2,'0'),'hex') || convert_to('4242','UTF8')"
psql -X -q -c "DROP TABLE IF EXISTS c.object_key"   # experiment table only (its ON DELETE CASCADE FK has no object_id index)
