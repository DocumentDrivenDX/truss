# Native64 registration-owned rebinding addendum

Registrations with rebinding use `truss-catalog-registration-report/0.3`, or
report0.4 when they also own key effects. Native64 selects
`truss-native-catalog-rebind/0.4` when the registration introduces any nested
array/map property, including when its actual retained-cell effects are on
another flat property. Each item chain is acyclic,
contains required Fields, and ends in a supported exact scalar. The complete
original descendant definitions and module read dependencies are retained.
Definition depth is at most32; values admit at most32 levels and4096 nodes.
Maps preserve unique literal keys in C order; sequences preserve order and
repeated values. Empty containers still require a valid complete item chain.
Descendant meaning changes and record/composed ownership remain unsupported.

The report inventory, exact journal wrappers, one version increment per affected
object, original-byte replay and current disclosure authority follow the
historical v0.2 report contract. All original descendant dependencies participate
in disclosure checks. Invalid leaves refuse with `property.rebind_value`; missing
or null required values refuse with `property.required` and qualified counts.

Registrations without new nested definitions retain profile0.3 when adding a required
scalar key component with its alternate key, or profile0.2 for the prior flat
subset. Stored profile0.1 through0.4 reports retain their original bytes and
profile-specific meaning; the historical v0.2 document is not a current scope
claim. Key-backfill details remain in catalog-key-backfill-report-v0.1.md.


## Native71 development: owned-object rebinding

The ownership limitation above describes native64. Native71 development admits
retained-value rebinding on existing owned objects through the same public
registration call. Root IDs/types and edges remain unchanged; every affected
object advances once with the existing rebind and metadata journal events.
The before image interprets ownership at its original physical revision. The
after image resolves its root definition pin and owner through the planned
catalog basis for the new revision. Rootless history rendering is unchanged.

Candidate collection and closing diagnostic disclosure require root-module read
authority for every owned object contributing to a value or missing-required
count. Current root readers are also required before effects, for original
report/retry and at deferred commit, using each retained image's own revision.
Complete image, key/reservation, history digest and final graph checks remain.
New required scalar rebinding may compose with an alternate key under the
existing native63 rules. No new public carrier or report shape is introduced.
Record-valued cells, cyclic definitions and descendant meaning changes remain
unsupported. Managed-service and performance qualification are separate.
