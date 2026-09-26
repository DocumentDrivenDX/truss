#!/usr/bin/env bash
# Records the machine, engines, client and UMF commit used (out/00_environment.txt).
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
uname -a; grep PRETTY_NAME /etc/os-release
lscpu | grep -E "^Model name|^CPU\(s\)"; grep MemTotal /proc/meminfo
for v in 17 18; do ( export PGVER=$v; source "$SPIKE/env.sh"; psql -X -At -c 'select version()' -c 'show shared_buffers' -c 'show work_mem' -c 'show synchronous_commit' -c "select datcollate from pg_database where datname = current_database()" | paste -sd' ' ); done
git -C "$WORK/src/postgres17" log -1 --format='postgres17 source: %D %H' 2>/dev/null || true
echo "postgres18: SPIKE-001 build (REL_18_6, commit 724edf9), AGE not loaded"
echo "bun $($BUN --version)"
echo "UMF: origin/master $(git -C "${UMF_REPO:-/home/user/umf}" rev-parse origin/master 2>/dev/null) exported with git archive to \$UMF_DIR (umf package $(grep -m1 '"version"' $UMF_DIR/package.json | tr -d ' ,'))"
