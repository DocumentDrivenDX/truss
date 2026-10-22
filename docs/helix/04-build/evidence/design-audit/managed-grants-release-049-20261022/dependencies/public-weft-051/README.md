# Public Weft 0.4.51 input verification

All nine actual public assets were downloaded and verified against the public API SHA-256 digests. The original SHA256SUMS covers the three wheels; it remains unchanged. All three ZIP/RECORD/native payloads were checked. Only Mac ARM64 and Linux x86_64 match Truss consumer cohorts; Linux aarch64 remains packaging-only and was never executed locally.

The published tag commit is d4b0b98507ae15bd98180a2ea2030ea92ce11d96. The distinct compiler/build freeze is 557153731e9f5d0583193a1189a07c6ed485d3d3. Original release-pins and platform packaging reports bind that freeze to the observed wheel and native hashes. The owner handoff and strict build guard establish build provenance; checksum or RECORD verification alone does not establish a source build.

Original metadata, the exact producer and cohort input, the successful raw log and verification receipt are retained here. Wheel binaries remain at their checksum-addressed public URLs and in the private qualification capsule. Download those three named wheel assets into all/ before replaying the producer. The producer records the initial inspection's incorrect checksum-coverage assumption and its tool-only retention limit. This packet establishes dependency integrity, not final Truss v0.0.49 qualification or Lakebase acceptance.
