# Canonical S resource adoption — source review only

The nine JSON resources are exact Git blobs from public canonical UMF commit
e3f38ef6f05ae636d2837f9d69f8d6805222664b, tree
a21368a92df488882ef9771e4a1d92205267ddd3. Their actual hashes also match the
reviewed Weft attempt494 nine-resource closure. Five differ from the original
PR95/f629 resources: three generated $comment leaves and two generated
provenance.compilerSha256 leaves. The remaining four are byte-identical.
Original bytes were copied without normalization or metadata edits. Independent
parsed-leaf comparison agrees with the Weft receipt; this is explanatory evidence,
not a replacement for the exact Git-blob and SHA256 comparison.

original-pr95/ retains the previous source.json and all nine original resource
files verbatim. Existing PR95 receipts, native failure/pass histories and frozen
profiles are untouched. receipt.json records each old/new digest, canonical Git
blob, source path, exact changed leaves and the new actual candidate manifest
digest. That digest is a source identity, not a qualified native inventory.

Nine pure public-API enrollment controls pass. Five authentic original resource
byte substitutions each refuse before engine construction; source-only resource
files still cannot establish compiled capability. The unit engine fixtures are
explicitly UNIT-not-a-release and do not impersonate compiled owner evidence.

Core manifest.json and Weft compiler.json remain absent. No binary hash, wheel,
compiled capability, capture, baseline, native acceptance or publication is
asserted. Genuine Linux artifact enrollment/admission must precede the two serial
raw inventories and the separately reviewed final baseline/strict119 campaign.
