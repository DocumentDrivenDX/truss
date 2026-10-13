# Original consumer grouped count — 2026-10-13

The unchanged read.count-group-by case now runs through the public Python interface. The original basic fixture and additional uc-3 are created through public CreateObject groups, followed by actual original-request committed replay and receipt visibility. The original query is compiled through Weft's default profile, not the narrower explicitly ordered count-summary profile:

```sql
SELECT u.name, COUNT(*) FROM catalog.UseCase u GROUP BY u.name
```

The installed Truss0.34/Weft0.4.7 execution returns columns name/count and exact Python integer counts: NDA review2, Lease abstraction1. The original expected list is Lease abstraction1, NDA review2. The original consumer comparator requires positional row equality, so this case fails and is not added to the passing eleven-case aggregate. No SQL rewrite, result sorting, oracle alteration or unsupported outcome hides the discrepancy.

This is a consumer expectation issue: SQL without ORDER BY does not promise output order. The consumer should either compare the grouped result as an unordered bag or author an ORDER BY when order is part of its contract. No Truss interface/compiler change is needed to produce these counts. Until the consumer chooses and updates its original corpus, the original case remains failing.

Evidence command used the installed current Truss package, Weft extension, DocumentDrivenDX pgserver-pg18==18.6.1/PostgreSQL18.6 and psycopg3.3.6:

```sh
python packages/python/examples/run_consumer_reads.py docs/helix/04-build/evidence/consumer-revision-2026-10-09/corpus.json NEW_DIRECTORY --bun /opt/homebrew/bin/bun --case read.count-group-by
```

The runner adds required-string record seed support and accepts only an exact True count capability requirement. It preserves existing edge seeds and original actual row ordering. Astra Ultra reviewed the plan; the source/evidence review precedes commit. Full original corpus and interchange remain open.

The existing eleven selected original workflows still pass in one basic test (23.256seconds). Astra Ultra approved the final source/evidence scope with the original count discrepancy retained as failing.
