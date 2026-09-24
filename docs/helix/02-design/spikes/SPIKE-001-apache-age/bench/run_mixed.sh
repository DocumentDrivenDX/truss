#!/usr/bin/env bash
# C12 addendum: 1..3-hop variable-length reads mixed with 10% single-property writes, single client.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
export PGOPTIONS='-c search_path=ag_catalog,public'
N=${N:-1000}; W=$SPIKE/bench/work_mixed; rm -rf $W; mkdir -p $W; cd $W
H='\set u random(1, 100000)'
printf '%s\n%s\n' "$H" "SELECT * FROM cypher('bench', \$\$ MATCH (a:Person)-[:KNOWS*1..3]->(d:Person) WHERE a.uid = :u RETURN d.uid \$\$) AS (u agtype);" > age_read.sql
printf '%s\n%s\n' "$H" "SELECT * FROM cypher('bench', \$\$ MATCH (p:Person) WHERE p.uid = :u SET p.touched = :u \$\$) AS (x agtype);" > age_write.sql
printf '%s\n%s\n' "$H" "WITH RECURSIVE r(node, depth) AS (SELECT id, 0 FROM rel.person WHERE uid = :u UNION ALL SELECT k.dst, r.depth + 1 FROM r JOIN rel.knows k ON k.src = r.node WHERE r.depth < 3) SELECT p.uid FROM r JOIN rel.person p ON p.id = r.node WHERE r.depth > 0;" > rel_read.sql
printf '%s\n%s\n' "$H" "UPDATE rel.person SET age = age WHERE uid = :u;" > rel_write.sql
for sys in rel age; do
  pgbench -n -M simple -c 1 -j 1 -t 50 -f ${sys}_read.sql -d postgres >/dev/null 2>&1   # warm the session-independent caches
  pgbench -n -M simple -c 1 -j 1 -t $N -f ${sys}_read.sql@9 -f ${sys}_write.sql@1 -l --log-prefix=$sys -d postgres > $sys.out 2>&1
  for script in 0 1; do
    cat $sys.[0-9]* | awk -v s=$script '$4==s {print $3/1000.0}' | sort -n > $sys.$script.lat
    n=$(wc -l < $sys.$script.lat)
    p50=$(awk -v n=$n 'NR==int(n*0.50+0.999999){print; exit}' $sys.$script.lat); p95=$(awk -v n=$n 'NR==int(n*0.95+0.999999){print; exit}' $sys.$script.lat)
    mean=$(awk '{s+=$1} END {printf "%.3f", s/NR}' $sys.$script.lat)
    echo "$sys $( [ $script = 0 ] && echo 'vle1..3 read' || echo 'write      ' ) n=$n p50=${p50}ms p95=${p95}ms mean=${mean}ms"
  done
done
psql -X -q -c "SELECT * FROM cypher('bench', \$\$ MATCH (p:Person) WHERE p.touched IS NOT NULL REMOVE p.touched \$\$) AS (x agtype);"
