# Batched browser admission reads

Batches object admission locks/reads and exact key-custody reads. Per-item UMF, guard, custody, effect and journal verification remain in their original order. The rejected first candidate delayed effect verification; corrected r2 restores it verbatim and adds a first-bad-effect versus later-failure regression.

Astra reviewed the exact source and actual Chromium lifecycle,1,024-row/eleven-batch workflow and old-provider recovery. The first bad effect returns EFFECT_VERIFICATION at item0, rolls back effects and recovers the same original outcome. Recorded r2 bulk elapsed5.299s and point295ms remain unqualified performance observations. No single1,024-operation portable batch or native release claim. Raw runtime reports are retained as gzip JSON.
