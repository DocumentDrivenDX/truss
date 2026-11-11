#!/usr/bin/env bash
# Fail if the committed tree contains a file over 1 MiB that is not matched by
# .size-allowlist (shell glob patterns), or if the tree exceeds the total budget.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
MAX_FILE=$((1024 * 1024))
MAX_TREE=$((80 * 1024 * 1024))
status=0
total=0
while IFS=$'\t' read -r -d '' meta f; do
  size=${meta##* }
  total=$((total + size))
  if [ "$size" -gt "$MAX_FILE" ]; then
    allowed=0
    while IFS= read -r pat; do
      case "$pat" in ''|'#'*) continue ;; esac
      # shellcheck disable=SC2254
      case "$f" in $pat) allowed=1; break ;; esac
    done < .size-allowlist
    if [ "$allowed" -eq 0 ]; then
      echo "size-guard: $f is $size bytes (> 1 MiB) and not in .size-allowlist" >&2
      status=1
    fi
  fi
done < <(git ls-tree -r -l -z HEAD)
if [ "$total" -gt "$MAX_TREE" ]; then
  echo "size-guard: tracked tree is $total bytes (> $MAX_TREE)" >&2
  status=1
fi
echo "size-guard: committed tree $total bytes"
exit "$status"
