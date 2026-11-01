---
ddx:
  id: truss.evidence.feed-source-custody-native-qualification-20261101
  type: evidence
  activity: build
  status: draft
  authoring:
    home: repo
---

# Feed source custody .75 candidate qualification — 2026-11-01

## Scope and result

This candidate adds a Truss-owned source custody handle for one feed consumer and one admitted page. PostgreSQL 18.6 persists the exact source selection and opaque destination-registration/ACK-scope bytes, and enforces the handle with a same-session advisory-lock marker and guarded custody routines. Truss does not interpret or authorize the external destination registration, protected ACK scope, or Ashlar destination ACK. The external Ashlar ACK remains outside this qualification.

The disposable native lifecycle passed on a fresh .75 fixture. It covered open followed by caller rollback and same-marker reopen; close rollback; wrong marker renewal refusal; legacy ACK refusal; consumer re-registration refusal; connection-loss stale-row prune and reopen; then one positive local Truss source ACK, a fresh read-only reconciliation, and committed close. The positive receipt is a fixture-owned Truss source ACK, not a protected destination ACK. The server reported PostgreSQL `180006`.

The corrected `.74 → .75-candidate` migration edge passes source generator `--check-only`, package integrity loading, and profile-pair validation against independent America/New_York and UTC captures. The corrected edge also passed one native upgrade on a fresh cold clone of the stopped R16b .74 source. The clone was byte-compared with the separately retained source backup; its source-copy receipt records tree SHA-256 `b1ab6a55…`, 1,255 files, and 65,754,852 bytes. `RuntimeMigrations.status()` admitted the exact `.74` source profile before preparation. The migration committed as `migrated`, `verify()` returned `current`, and the committed receipt binds target `5ecb599f…`. PostgreSQL reported 18.6. Its ordered-step evidence SHA-256 is `ebb685fefe3b455db9e8cffebd9178e385a6cc77c12db01399015d3ce4e4f80c`; preservation evidence SHA-256 is `a5f7d9658ccef52464936303c06d322821486340940a1215a1fc6730addf4185`.

The installed package replaces the unpublished candidate target `dab1a41aa534aa98df248fc0e4a8e939489f35c79eb93b4cd1218d0bc6849907` with the final advisory-lock target `5ecb599f65d64e6656bf6c83c30cea6e2aefd488cb3fe821b749458d5e9b3522`. The older unpublished `0b1c022e7b4079e1ceff1b02d36fccac08c8a185bbad18156d0a548a0b264915` target is retained only in the earlier ACL/preflight refusal receipts. None of these candidate endpoints was published; the packaged graph retains the accepted source history and one forward edge to the final target.

One separate fresh `.74` fixture attempt refused before prepare/apply because its `journal_runtime_horizon` reflected a Nov 1, 2026 initialization, outside the accepted source profile. A read-only forensic copy confirmed this as the only inventory difference: expected `2026-09-01 00:00Z` through `2027-11-01 00:00Z`, observed `2026-10-01 04:00Z` through `2027-12-01 05:00Z`. No migration SQL ran. The first corrected-edge R16b attempt rolled back on an omitted owner transfer for the private lock-witness helper; the generator now transfers ownership and revokes PUBLIC on that exact helper, and the next fresh exact source clone passed. Both refusal receipts are retained separately from the successful migration receipt.

## Artifact identities

Runtime version remains `0.75` with release identity `truss-catalog-runtime/0.75-candidate`; this evidence does not qualify a stable Truss `0.0.52` release.

| Artifact | SHA-256 |
|---|---|
| Runtime manifest | `5ecb599f65d64e6656bf6c83c30cea6e2aefd488cb3fe821b749458d5e9b3522` |
| Custody SQL source | `4c33f6d438c3f78de5fb6e5c1a628d42bd81309edae56dc74d83931bab549dc6` |
| NY target capture | `1dc9463d5cc3a658a6d4daa7194be4d71f4875270323541d9f0eee8eae57712c` |
| UTC target capture | `2d5a17f30424861b8477dbbc5ee8599aa5af86e21699815548d2ffbc33a87a70` |
| Migration manifest | `41bf1e3f688f78b56c74acc32a6b08126157a6d15000fc257925fa0f5884b77b` |
| `.74 → .75` edge | `7cfc8d8e025e3b30d39851e9918fe06a8487ec7a760307e6ed1f1890bf852d1b` |
| Target profile | `2d1a61cc2dc7187b64ac37fa8fcdfe10196be0a46cb1631ef38e0f6a47fc8b82` |
| Target exact ACL profile | `973684be56678e2be0f84497c9dc27496b3895dd97a909219bc7acd3d6da0b75` |
| Initialization profile | `6dfb2260f3816d5060e3cfa19d883f3e77eeb14fe547ae47d76f052b3f91918d` |

## Qualification receipts

- NY and UTC capture file hashes are listed above. Both bind the same runtime manifest digest. The generator check-only path passed against the authentic archived `.74` predecessor manifest restored in a temporary migration view; the installed package now contains only the replacement `.74 → current .75-candidate` edge, not the unpublished earlier candidate endpoint.
- `load_recipe()` passed with 32 pinned migration artifacts. The migration manifest digest is `09618637b390122d4ffb59e174c49d162f58a0fd9d80b42a9b667628e4d83f4f`.
- Fourteen focused source test functions passed: nine custody runtime/SQL-contract checks and five migration generator checks. They were invoked directly under the selected Python runtime because `pytest` is not installed in that environment.
- The local custody lifecycle receipt is retained in [`receipts/result.json`](feed-source-custody-native-qualification-20261101/receipts/result.json) (SHA-256 `5cc7fa8291aec7b4905743ed20c0aef2271357abb00826c3675e1d200160d480`). Its scope receipt is [`receipts/run-scope.json`](feed-source-custody-native-qualification-20261101/receipts/run-scope.json) (SHA-256 `40e2cb9d8f8d6aca7071a746aaf090ea854defda89225cf4ccbb81e5860bc833`).
- The successful migration receipt is [`receipts/r16b-migration-result-final.json`](feed-source-custody-native-qualification-20261101/receipts/r16b-migration-result-final.json) (SHA-256 `d8b6948813078d0d5b49be458978a1db57ff8e1226f9afc4d2c4de5dd90f6fba`); the cleanup receipt is [`receipts/cleanup.json`](feed-source-custody-native-qualification-20261101/receipts/cleanup.json).
- The source-only fresh-fixture refusal and its read-only forensic inventory are retained separately in [`receipts/forensic-inventory.json`](feed-source-custody-native-qualification-20261101/receipts/forensic-inventory.json) (SHA-256 `fa7b04bc105b249077a7b20e9fdd3c95282ce95ef10923468fe2c315c8c8604d`). The first corrected-edge migration rollback is retained as [`receipts/first-corrected-edge-refusal.json`](feed-source-custody-native-qualification-20261101/receipts/first-corrected-edge-refusal.json).

No cloud service, external destination ACK, publication, push, or tag was used.
