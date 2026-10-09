# Conformance operation registry — authored method inventory

Companion to [case grammar](conformance-case-grammar.proposal.md). These entries bind existing declarations; they introduce no public methods. Status: proposed inventory, not a complete executable registry. Exact input/result schemas, identity paths, original profiles and semantic observation scope must be registered before execution.

| Family | Existing capability method | Original declaration | Transaction and comparison boundary |
| --- | --- | --- | --- |
| catalog | acceptInTransaction | truss-catalog-capability-v0.1 | Original supplied transaction; complete acceptance/report/head state, pending until confirmed termination |
| catalog | report | truss-catalog-capability-v0.1 | Supplied read context; complete immutable original accepted report |
| mutation | applyInTransaction | truss-mutation-capability-v0.1 | Supplied transaction; exact single-write result plus full applicable state/journal |
| group | applyInTransaction, request state none | truss-group-capability-v0.1 | No receipt/replay outcomes; complete ordered results and one atomic operation scope |
| group replay | applyInTransaction, request state present | truss-group-capability-v0.1 | Original request/namespace authority, full semantic input and receipt result; replay may observe already committed original work |
| import | runBatches | truss-import-capability-v0.1 | Explicit owned batches; complete report retains prior committed progress on interruption |
| import | applyInTransaction | truss-import-capability-v0.1 | Supplied scope; original per-record savepoint outcomes remain pending |
| direct read | lookup | truss-direct-read-capability-v0.1 | Supplied context; complete exact object/key/edge lookup and non-disclosure |
| direct read | page | truss-direct-read-capability-v0.1 | Supplied context; complete n+1 observation and exclusive continuation |
| catalog view | catalogView | truss-direct-read-capability-v0.1 | One consistent definition context; full inventory versus declared projection |
| traversal | traverse | truss-direct-read-capability-v0.1 | Original snapshot/stage/cumulative work; human output interpretation remains pending |
| traversal | resumeTraversal | truss-direct-read-capability-v0.1 | Original stage and expected work version; no resource reset |
| traversal | nextTraversalPage | truss-direct-read-capability-v0.1 | Sealed original membership and current publication authority |
| traversal | releaseTraversal | truss-direct-read-capability-v0.1 | Retained original cleanup facade; no transaction argument or graph operation |
| history | pageJournal | truss-history-capability-v0.1 | Supplied context; bounded raw journal page, not complete reconstruction/feed |
| history | reconstruct | truss-history-capability-v0.1 | Original definition/baseline/sibling horizon and exact logical version |
| history | historicalSource | truss-history-capability-v0.1 | Retained original creation/owner context with current authority |
| compiled execution | executeInTransaction | truss-compiled-execution-capability-v0.1 | Exact registered Weft artifact/bridge and supplied context; independent logical result |
| feed v0.2 | discoverNext | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Complete original manifest boundary under coherent safe watermark |
| feed v0.2 | readFragment | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Original ordinal fragment and prerequisites, not invented journal positions |
| feed v0.2 | observeFreshness | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Complete v0.2 source boundary, fact-clock and publishable/held/unavailable states |
| feed v0.2 | acknowledgeInTransaction | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Original verified application; pending source checkpoint until supplied transaction settles |

Declaration files live under `docs/helix/02-design/contracts/bindings/`, with the basename in column three plus `.d.ts`. Group overload accepting unresolved request union is a typing convenience, not a third behavior. Case admission must narrow request-none/present before deciding required receipt observations.

## Feed construction boundary

The existing ReferenceAssembly.feed accessor returns historical FeedCapability v0.1. It cannot supply FeedCapabilityV02 by renaming a profile or structural coercion. Current complete key-transition/freshness cases explicitly construct createFeedCapabilityV02 with the existing assembly, selected feed capability and admitted FeedProofVerifierRegistrationV02. Construction is inert and does not start feed work. Original registration, proof/application/checkpoint/resource/native procedures still require their independent admission.

Keep legacy v0.1 cases version-scoped if independently selected. They cannot satisfy a v0.2 required case by losing its complete application/boundary semantics. An unavailable v0.2 constructor/profile blocks that case/full selected qualification rather than falling back to assembly.feed. No change to historical public declarations is required to expose this distinction.

## Registry completion obligations

For every entry, the executable registry must pin exact original declaration and input/result schemas, full semantic contract inventory, capability selection, observer/profile/resource grammar, and generated identity paths. Symbolic step references must resolve before existing public input construction, never by modifying public wires. The registry must distinguish outer Outcome execution failure from inner business result, and import's distinct progress-bearing execution result.

Host transaction controls use trusted harness procedures, not Truss capability methods. Installation/status/explicit migrations, live provenance and administrative retention/tooling require their own exact existing declarations/procedures to be enumerated before claiming the full registry complete. Do not invent convenience methods to fill that inventory. Informative SQL is never dispatched as a substitute operation.

Independent controls must reject v0.1 feed masquerading as v0.2, request-free group expectations containing replay, import progress discarded inside a generic Outcome wrapper, release requiring an ended transaction, and a pending result labeled committed from savepoint release. These are required red integration controls, not passing runtime evidence.
