# Original preparation-program enrollment

Truss now has a private administrative registration path for original Weft mutation programs. `compile_preparation_program` invokes the configured compiler and lowering implementation, retaining the exact configuration and request, original compile response containing the plan Artifact, exact binding Artifact, selection-registration request, lowering request and lowering response. It supplies the plan's own `maxItems` and requires the matching `maxItems + 1` fetch bound. It never executes the returned SQL.

`register_preparation_program_in_transaction` binds those bytes to the existing issued action store and its original receipt. UMF exports the immutable native storage. Registration runs under trusted administrative quiescence in the caller's PostgreSQL 18.6 READ COMMITTED transaction. It returns a pending native UUID identity encoded as JSON string bytes; the caller owns commit. A fresh transaction with the same store and registration key returns that identity only when all original bytes agree. Changed bytes refuse. Ordinary callers receive no home, allocator or execution privileges.

The original products workflow uses Weft source `c0c6449481a87eed38d3f7a6ebebc1f4ab4beeb4` and the retained tested native module SHA256 `2f91cbd5de07f04492d6fdbd964bf86cce84245adc18cd6debe3c17f61ef6843`. The older `demo1` model revision correctly refused against the accepted native digest revision; the unchanged original owner packet supplies the matching revision. The basic native repository test covers actual compilation, registration, commit, exact readback, idempotent retry, changed-byte refusal and ordinary read denial. It requires the matching mutation Python bridge; the previously published bridge lacks this class.

This is byte custody through a trusted compiler and installer, not compiler authentication or native program admission. A supplied source pin is retained evidence, not proof of provenance. Storage checks cover owner/private grants and the immutable trigger; complete installed definition/dependency/DDL custody remains part of future admission. No anchor resolves the issued program identity yet. Current Subject/action/owner permission, source and compiler provenance, original anchor/nonce/data transaction binding, guarded selection/finalization, seal persistence and original commit/recovery composition remain required. No protected execution or public release capability is enabled by this tranche.

## Original native producer replay

The private `replay_preparation_program` helper now invokes the retained exact
Weft native build in a fresh isolated Python process. It checks the original
binary before load, calls its actual mutation compiler and renderer, and
compares all five original artifacts byte for byte. It accepts no compiler
factory or alternate claimed source profile. This strengthens the old byte
enrollment boundary; the original arbitrary-factory enrollment does not itself
authenticate a producer. Future source association must call replay directly,
not accept a serialized replay receipt.

One basic test reproduces the original fixture and refuses changed SQL or a
different binary. Astra Ultra approved this private checkpoint. The engine
executable, Truss sources and immutable native installation remain trusted
deployment premises; hashing alone does not establish a build's provenance.
This helper performs no database or SQL execution and issues no authority.
The [receipt](evidence/preparation-compiler-replay-20261015.json) retains the
exact source/build pins and result.
