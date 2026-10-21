Original Hohfeld embedder schemas used for Truss registration regressions.

The gzip JSON archive records repository, commit, original paths and SHA-256 hashes.
`sourceText` preserves each source byte-for-byte as UTF-8. Tests verify the hashes
before testing their element-specific unnamed-source registration refusal.
The archive remains unchanged. Positive registration/replay/read/write cases
use explicit named revisions authored by `embedder_fixture_sources.py`: each
missing Record/Field name is authored as its element ID, and the new exact bytes
receive their own SHA-256 revision. Custody checks compare those revised bytes.
This is fixture authoring; Truss does not fill in names automatically. Historical
qualification of the unnamed originals retains its original release scope.
