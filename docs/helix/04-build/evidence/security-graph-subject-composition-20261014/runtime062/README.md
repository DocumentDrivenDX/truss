# Runtime0.62 accepted-source dependency integration

The newly merged catalog report builder reads runtime_catalog_key_backfill. Native r6 fails on that missing private-reader SELECT permission. The source table is now included in the complete SOURCE_TABLES ShareLock census and fixed private cut issuer. The guarded reader derives its object/edge/source list from SOURCE_TABLES, eliminating the duplicate that native r7 correctly refused. The changed issuer SQL has a new explicit original-byte digest; r8 correctly refused before that digest was updated. All three failed runs are retained. Runtime0.61 passing evidence remains historical.

Runtime0.62 replay r9 is pending at this checkpoint. Boundary checks pass1066 imports; exact source checks remain enabled. Astra's additional review could not run because the reviewer reached its usage limit; no additional independent review is claimed. No acceptance promotion or public security activation is claimed.
