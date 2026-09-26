#!/usr/bin/env bash
# Repeatable build: PostgreSQL 17 (latest REL_17_* tag) from the GitHub mirror.
# Sources and build tree go to $WORK; the install prefix is $PGRT-pg17/pg17 (traversable by the postgres user).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
TAG="${TAG:-REL_17_11}"
P="$PGRT-pg17/pg17"
mkdir -p "$WORK/src" "$P"
date -u +"start %FT%TZ"
cd "$WORK/src"
[ -d postgres17 ] || git clone -q --depth 1 --branch "$TAG" https://github.com/postgres/postgres.git postgres17
cd postgres17 && git log -1 --format="postgres $TAG %H %cd"
./configure --prefix="$P" --without-icu --silent
make -j4 -s >/dev/null 2>&1
make -s install >/dev/null
(cd contrib && make -s -j4 install >/dev/null)
date -u +"pg built %FT%TZ"
"$P/bin/postgres" --version
