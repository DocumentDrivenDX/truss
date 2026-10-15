# Browser persistent submission/control checkpoint

Actual Chromium153/PGlite0.5.10, PostgreSQL18.6, Bun1.4.2. The existing public
load/materialize/seal workflow now submits one retained seal into a persistent
queued job. Basic observations: exact original control replay; fresh control
with same submission key returns the same JobRef/current state; distinct genuine
seals of the same frozen work identify the same job; changed control input
conflicts; semantic missing-seal refusal is retained and recovered unchanged;
reopen recovery returns the original sampled submit outcome; review returns
retained manifest bytes/current authorized state. Existing physical object/key/
reservation/journal counts remain four, proving submission did not execute work.

Strict TypeScript passes. Two-CWD asset builds match the exact Chromium bundle:

- Manifest 07030e7b3f8e73c3f18a6b809fc536453a574562b87f7a655dc63339d74d9718
- Provider 25cca4c9b0876d834f2b162857283b1666dab6ca6015cc6d7ae90e59f6191a5e

Astra Ultra plan/source review requires current action/model/cut authorization
before original-control lookup, lookup before fresh seal admission, frozen intent
equality independent of sealing control IDs, semantic refusal distinct from
confirmed control rollback, and exact retained source correspondence for review.
Those finite corrections, including damaged job/route custody reporting unknown
and fencing rather than confirmed noncommit, precede the final run. Caller retains exact control
input before RPC. Unknown result-persistence/commit/flush fences; recovery does
not repeat mutation, and missing remains unresolved. Completed empty work is a
code path rather than an additional observed fixture here.

This is private browser source delivery with queued jobs. Claim, actual frozen
batch effects, cancellation, feed and retention remain unfinished; no full
local-bulk/1 or native904 qualification, Python wheel or native66 change follows.
