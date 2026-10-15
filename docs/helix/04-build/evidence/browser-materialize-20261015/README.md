# Browser materialization and keyed seals

Basic actual Chromium 153/PGlite 0.5.10 workflow: registered original Products
catalog; independently issued action and complete-population read grant;
original Weft selection; original UMF Key receipts/manifest; three selected
rows in batches of two and one; persisted seal, identical replay, conflicting
attempt refusal, reopen recovery with a fresh capability and reordered reference
members, and missing-key unresolved outcome. Rows are administrative fixtures.
No production bootstrap, mutation execution, journal/feed or crash claim.

Astra Ultra reviewed the implementation and requested fencing the initial driver
read, hard-pinning executable JS as well as WASM, and retaining authored action
revision independently of content SHA. All three corrections precede this run.
Strict browser TypeScript compilation passed. Two builds from repository root
and /private/tmp emitted identical manifest/provider hashes:

- Manifest: f7008e85bb14bda4be714f2049be7e2811db06fed6d5f88680fc341a8b874168
- Provider: 0a621cc39375402e40f7c0774958858a8e063c203057dd2ce0ed8dc8cfff9081
- Weft source: 4f5b73df8b751b4291b84af3b59169c1a1b63ed0
- Original Weft wrapper: 2711256b057a90fa8a898f1d616b871a083f993177b6bbffcd6cbd17fcaa6119
- Original Weft WASM: e73e77d5dfbf2118a0452838f70c17ab17658caf7bca5841abc6f31a6e91f8e5

Retain pending request key/attempt/reference before dispatch. Known callback
rollback and not-dispatched failures remain distinct from ambiguous commit or
flush results, which fence the store. Missing recovery records are unresolved.
Original input/outcome artifact text is retained, not reconstructed from JSONB.
See packages/browser/README.md for API and limitations. Published Python/native66
and Weft wheels are unchanged by this private browser source tranche.
