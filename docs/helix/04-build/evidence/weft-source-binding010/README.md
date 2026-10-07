# Layout 0.10 source binding review packet

Separate current-source packet; earlier 0.8/0.4 packets remain unchanged. Binding envelope retains actual 0.10 SQL, complete 43-table/420-column declaration map, exact original UMF 0.7.0 required-string fixture and concrete home/value/presence/codec/context profiles. Review010 physical identities are source-only; synthetic type/property IDs are 17/23.

Reproduce with build-weft-source-binding010.py, check-weft-source-binding010.py, check-weft-source-binding010.ts and check-weft-source-binding010-negatives.py in the sibling design-audit directory. The TypeScript check takes the local Ajv2020 module path as its argument. All six schema validations, full artifact/profile/source closure and four damaged-packet refusals pass. No compiler/native execution or profile registration is claimed.

This fixture maps one string property only. Keys, relationships, numeric/nullable/tree/compound capabilities require their own admitted original definitions/profiles. Complete declared storage coverage is not complete compiler capability coverage. Unregistered execution must refuse before SQL. Exact current layout binding/codec/executor review and owner adoption remain pending; no cross-chat delivery has occurred.
