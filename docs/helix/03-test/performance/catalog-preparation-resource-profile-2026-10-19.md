# Current UMF catalog preparation resource profile

The current preparation bridge uses UMF's opt-in synchronous
`withCatalogResourceProfile` for original-document parsing and semantic
validation. The pinned owner profile allows up to 1,000,000 JSON values per
document. Its ordinary global limit remains 100,000 values; maximum depth (128)
and maximum text length (4,000,000 characters) are unchanged. Truss continues to
limit each source document to 4 MiB, the complete source set to 16 MiB and 512
documents, the encoded preparation request to 16 MiB, and the response to 64
MiB. Preparation runs in the existing embedded V8 14.4.258.23 / MiniRacer 0.14.1
isolate with a 128 MiB soft and 512 MiB hard memory limit and a 10 second call
deadline. These are independent safeguards: the UMF value allowance is not a
measured memory allowance, and the isolate limits do not bound the Python host
or PostgreSQL server.

The unchanged `many-types` matrix source contains 1,000 record types, 12,000
properties, 13,000 element declarations and 1,000 relationships. Its compact
JSON is 2,528,639 bytes and contains 179,012 JSON values (including the root and
containers, excluding object member names): about 18% of the per-document value
allowance and 60% of its byte allowance. The existing 100,000-value default
rejected it at `/modules/0/elements/8228/members/10`; with the bounded catalog
profile it prepared successfully in 2.256 seconds in a focused local run. The
timing is an observation, not a release performance gate.

The separate Python schema cache retains at most two revisions and uses its
existing 128 MiB estimated-resident-byte budget. That cache budget applies to
retained compiled schema metadata; it does not replace or add to the per-call
UMF parse/validation profile. No V8 heap measurement was collected for this
workload.

The producer bundle is pinned to UMF commit
`b24e07abae445414c41d2f122deae596915c6bd5`. Focused pure preparation tests
passed (3 tests); PostgreSQL registration and the full workload matrix remain
separate qualification gates.
