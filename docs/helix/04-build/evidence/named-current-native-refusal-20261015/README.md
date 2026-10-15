# Exact named-query source admission

The public PG18 workflow on native runtime 0.65 refused the unchanged owner source
with `unsupported_profile`. The catalog remained at revision zero with no accepted
documents. `receipt.json` preserves that result; its empty runtime-lock hash refers
to the disposable runtime lock, which is not archived here.

The source envelope and read scenarios are retained byte-for-byte. The extracted
core preserves object/list order and values in compact UTF-8 JSON. Its supplied
revision is `named-query-core-r1`; its content digest is a separate identity.
Neither the standalone signed64 `m.clear` transform-input Field nor the opaque
token value may be removed or rewritten to obtain acceptance.

The exporter includes a subsequent public apply/readback/native-binding path,
but that path has not run successfully. This evidence establishes the refusal,
not an accepted binding, installed security policy or protected query authority.

The new explicit support policy 0.17 and Python inventory branch are preparatory:
standalone singular scalar declarations retain their assertions without allocating
properties or claiming value enforcement. Public preparation and native admission
remain on their existing profiles pending the matching producer/native release.
The basic catalog-support suite passed 15 tests; its optional legacy native-driver
case was skipped. The focused addition covers the explicit inventory branch and
preserves historical standalone-field refusal.

The Truss-owned source-reference wrapper now recognizes the exact 0.17 pin; its
original UMF producer bundle is unchanged. The exact retained core passed a
focused preparation regression under 0.17, retained all original bytes and kept
`clear` out of storage declarations. The same source remained unavailable under
0.16. This is preparation evidence only; native 0.65 remains unchanged.
