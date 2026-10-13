# Conditional principal acquisition order

The model abstracts one pending checkout and one monotone source closure into integer event order. Initial gate, reset handling, final gate and lease publication are candidate program events. `reset_ok` is a host-success premise, not a proof of native outcome settlement. The modeled quarantine expression describes the successful-reset/final-closed branch only; it is not the whole runtime quarantine state machine.

Five UNSAT queries establish conditional no-publication after closure, during-reset refusal/quarantine, failed-reset refusal and future closed-source refusal. Three SAT queries retain the old pre-await-only escape, a check/publication-yield escape and nonvacuous open-source publication. Event positions are unbounded integers; this is not a bounded enumeration proof.

The same-event final gate/publication premise models the inspected single-isolate synchronous segment. Object construction and wrapping local methods contain no executed await or external callback before return. An async method's declaration is not execution of its body. Promise resolution is publication here; later receipt/use of an already published lease is outside this theorem. No general TypeScript refinement, native/helper authenticity, writer/subject authority, prior-lease revocation, crash recovery, native quarantine settlement or complete backend acceptance follows.

The source and model byte hashes are retained in proof.json. Native/protocol counterexamples and corrected runtime evidence remain separately scoped in ../principal-runtime-integration-20261013/. Required backend cases retain their original status.
