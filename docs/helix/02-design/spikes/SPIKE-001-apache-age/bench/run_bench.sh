#!/usr/bin/env bash
# C12 (indicative only): single-vertex fetch by key and fixed 1/2/3-hop traversals,
# AGE 1.8.0 Cypher vs a hand-designed relational schema, same data (bench/00_load.sql).
# Single client, simple query protocol for both (each statement parsed and planned per call),
# random start key per transaction, WARM runs discarded, per-transaction latencies from pgbench -l.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
export PGOPTIONS='-c search_path=ag_catalog,public'   # age is in shared_preload_libraries, so no LOAD needed
N=${N:-3000}; WARM=${WARM:-300}
W=$SPIKE/bench/work; rm -rf $W; mkdir -p $W
H='\set u random(1, 100000)'

# property indexes the AGE side needs (created by sql/03_indexes.sql; recreated here to be self-contained)
psql -X -q -c "CREATE INDEX IF NOT EXISTS person_uid_btree ON bench.\"Person\" (agtype_access_operator(VARIADIC ARRAY[properties, '\"uid\"'::agtype]));" -c "ANALYZE bench.\"Person\"; ANALYZE bench.\"KNOWS\";"

declare -A Q
Q[rel_fetch]="SELECT id, uid, name, age FROM rel.person WHERE uid = :u;"
Q[age_fetch]="SELECT * FROM cypher('bench', \$\$ MATCH (p:Person) WHERE p.uid = :u RETURN p \$\$) AS (p agtype);"
Q[rel_hop1]="SELECT b.uid FROM rel.person a JOIN rel.knows k1 ON k1.src = a.id JOIN rel.person b ON b.id = k1.dst WHERE a.uid = :u;"
Q[age_hop1]="SELECT * FROM cypher('bench', \$\$ MATCH (a:Person)-[:KNOWS]->(b:Person) WHERE a.uid = :u RETURN b.uid \$\$) AS (u agtype);"
Q[rel_hop2]="SELECT c.uid FROM rel.person a JOIN rel.knows k1 ON k1.src = a.id JOIN rel.knows k2 ON k2.src = k1.dst JOIN rel.person c ON c.id = k2.dst WHERE a.uid = :u;"
Q[age_hop2]="SELECT * FROM cypher('bench', \$\$ MATCH (a:Person)-[:KNOWS]->()-[:KNOWS]->(c:Person) WHERE a.uid = :u RETURN c.uid \$\$) AS (u agtype);"
Q[rel_hop3]="SELECT d.uid FROM rel.person a JOIN rel.knows k1 ON k1.src = a.id JOIN rel.knows k2 ON k2.src = k1.dst JOIN rel.knows k3 ON k3.src = k2.dst JOIN rel.person d ON d.id = k3.dst WHERE a.uid = :u;"
Q[age_hop3]="SELECT * FROM cypher('bench', \$\$ MATCH (a:Person)-[:KNOWS]->()-[:KNOWS]->()-[:KNOWS]->(d:Person) WHERE a.uid = :u RETURN d.uid \$\$) AS (u agtype);"
# variable-length 1..3 hops: recursive CTE vs AGE VLE
Q[rel_vle13]="WITH RECURSIVE r(node, depth) AS (SELECT id, 0 FROM rel.person WHERE uid = :u UNION ALL SELECT k.dst, r.depth + 1 FROM r JOIN rel.knows k ON k.src = r.node WHERE r.depth < 3) SELECT p.uid FROM r JOIN rel.person p ON p.id = r.node WHERE r.depth > 0;"
Q[age_vle13]="SELECT * FROM cypher('bench', \$\$ MATCH (a:Person)-[:KNOWS*1..3]->(d:Person) WHERE a.uid = :u RETURN d.uid \$\$) AS (u agtype);"

ORDER="rel_fetch age_fetch rel_hop1 age_hop1 rel_hop2 age_hop2 rel_hop3 age_hop3 rel_vle13 age_vle13"

echo "== result-size parity check (sum of result rows over start keys 1..200)"
for q in rel_hop1 age_hop1 rel_hop2 age_hop2 rel_hop3 age_hop3 rel_vle13 age_vle13; do
  body=$(echo "${Q[$q]}" | sed 's/;$//')
  cnt=$(for u in $(seq 1 200); do psql -X -At -c "SELECT count(*) FROM ($(echo "$body" | sed "s/:u/$u/")) s"; done | paste -sd+ | bc)
  echo "$q rows=$cnt"
done

echo "== latency (ms), single client, simple protocol, N=$N after $WARM warm-up"
printf "%-10s %8s %8s %8s %8s %8s\n" query p50 p95 p99 mean tps
for q in $ORDER; do
  f=$W/$q.sql; printf '%s\n%s\n' "$H" "${Q[$q]}" > $f
  pgbench -n -M simple -c 1 -j 1 -t $WARM -f $f -d postgres >/dev/null 2>&1
  (cd $W && pgbench -n -M simple -c 1 -j 1 -t $N -f $f -l --log-prefix=$q -d postgres > $W/$q.out 2>&1)
  fails=$(grep -E "number of failed" $W/$q.out | awk '{print $5}')
  tps=$(grep -E "^tps" $W/$q.out | awk '{print $3}')
  cat $W/$q.[0-9]* | awk '{print $3/1000.0}' | sort -n > $W/$q.lat
  n=$(wc -l < $W/$q.lat)
  p() { awk -v n=$n -v p=$1 'NR==int((n*p)+0.999999){printf "%.3f", $1; exit}' $W/$q.lat; }
  mean=$(awk '{s+=$1} END {printf "%.3f", s/NR}' $W/$q.lat)
  printf "%-10s %8s %8s %8s %8s %8s  (n=%s failed=%s)\n" $q $(p 0.50) $(p 0.95) $(p 0.99) $mean ${tps%.*} $n $fails
done
