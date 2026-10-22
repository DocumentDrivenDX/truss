# Arras source557 producer-pin correction

This packet records a narrow repair to the active Hohfeld follow-up cohort map. The source557 corpus in commit `22ed333528a4f57a24edfca5d3df811269471faf` refreshed expected cohort literals for `test_current_disclosure_cohort.py`, but carried forward the preceding source digest. The strict HF runner therefore rejected archive `c08c88f9…` before executing a test. The original archive, extracted corpus, runner output, command, exit status, pre-22ed source and corpus, and reviewed corpus delta are preserved unchanged under this directory.

The active corpus correction changes only that one producer digest to the bytes in source commit `22ed333…`. The current corpus retains 62 cases, 363 producer pins, the same expected outcomes and `nativeManifestSha256` (`c4339ac7…`). The reviewed 22ed corpus delta remains separately preserved as a patch. The prior source-to-wheel-to-sdist correspondence records 455 runtime files; a current comparison found no missing or changed runtime payload files.

The refreshed archive is independently retained at `refreshed/archive.zip`; its corpus is also retained as `refreshed/corpus.json`. Archive CRC, exact corpus correspondence, all 62 cases, all 363 producers, and the corrected digest were checked. The native 62-case rerun is pending; this packet does not claim that gate passed. Its result and original output will be added here after the strict runner completes.

`producer-custody.json` inventories preserved-file lengths and SHA-256 values, and binds the failed and refreshed archive identities. The failed `c08` evidence is historical and remains unchanged.
