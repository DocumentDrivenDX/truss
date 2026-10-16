# Browser key source interning

Adopts the reviewed canonical UMF/Weft browser owner assets and the private seal input0.2 implementation. The model is stored once per sealed input; original UMF key receipts are reconstructed for unchanged verification. Existing input0.1 seals and jobs retain retry, recovery and execution behavior. No native runtime or portable batch-size contract changes.

Actual Chromium/PGlite18.6 lifecycle, old-provider upgrade and 1,024-row workflow reports pass. The latter uses eleven portable batches within the existing 100-operation limit, not one native atomic group. It verifies 1,024 loaded rows and 1,025 changed updates including the separate point update. Bulk elapsed6.338s and point326ms remain performance failures. The recorded provider is the reviewed staging build; a canonical build is recorded separately after integration.
