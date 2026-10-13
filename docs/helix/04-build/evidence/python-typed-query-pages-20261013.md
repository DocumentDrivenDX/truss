# Typed SQL-page feature tranche — 2026-10-13

Public query_page_in_transaction supports required string/boolean/integer/
decimal(18,4) authored primary keys under native0.46/layout0.16 and
Weft0.4.11/backend0.4.16. The statically selected typed entrypoint uses wrapper
weft-sql-page/0.2 and cursortruss-query-page/0.2. Legacy resolve_page/wrapper0.1
and ordinary explicit string-only entity-page/related-entity-page admission
remain unchanged; generic compile/IR/application-read shapes are reused.

Typed ROW comparison/order matches full-source validated mathematical numeric,
boolean and exact string tuple equality. Numeric projections keep original
lexical tokens; after keys are JSON-safe strings. Integer conversion uses
str(Decimal(value)), decimal fixed-point without quantize/float, exact booleans
true/false. Existing1,024 page component admission is retained separately from
128 relationship list components. Lookahead and last-returned-key positioning,
current authority, logical byte/scan bounds and generated continuation origins
remain unchanged. No nested/binary/timestamp/unfaceted-decimal key support claim.

Astra Ultra reviewed plan and completed source. Corrected cursor version admission,
CPython integer conversion, page component limit and public function inventory.
Normal Cargo edges and11-package source boundaries pass. Existing committed
Databricks compatible-profile declarations were inventoried without code changes.
Original .45 archive and prior helpers/ACLs are preserved for additive upgrade.

Final installed Truss0.0.9.dev0/Weft0.4.11: four tests passed65.151 seconds,
covering original UMF0.7/0.8 typed pages/read-only continuations, preserved decimal
scale and bool tie ordering, existing string page facade and .45→.46 upgrade.
Initial typed-only pair passed20.964 seconds. Focused Python mypy and933-import
module boundaries pass. Managed targets/full corpus remain unqualified.
