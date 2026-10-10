# Original row-group custody carrier — proposal 0.1

This closes the proposed original_group_custody_bytes body for CONTRACT-001's
existing operation registry. It supplies the previously prose-only address plus
complete original family-admission envelope, without adding a public token, native
operation, layout column or alternate UMF key encoder. The
[closed schema](truss-row-group-custody-v0.1.proposal.schema.json) is a candidate
codec input; no existing installed producer/profile is silently relabeled.

The immutable original strict-JSON bytes carry a registered body profile, exact
address domain, complete original operation address, native operation kind and
originalGroupAdmission exactArtifact. The artifact retains its original identity,
bytes and digest under the existing shared carrier. Its bytes are the complete
original family admission, not another operation context or a future result/seal.
The body contains no self-seal, commit result or future readiness digest.

Under the existing address proposal, operationIdentity is exactly the same original
four-string address as both identity fields in each contributing-operation manifest.
It denotes one native logical operation; ordered commands remain inside original
family admission. Local manifest position does not become a native ordinal and
cannot create a new group identity.

Before sealing or lookup-driven effects, compose these checks:

1. Admit original registered body/family codec and installed/current subject scope;
   then decode complete original bytes under finite original resource bounds.
2. Match the body address to the original context installation/xid/ordinal and the
   actual registry key, and match operationKind to the original native row. Compare
   complete address bytes using the existing exact encoder/decoder.
3. Match originalGroupAdmission identity, bytes and digest exactly to the operation
   context's originalGroupAdmission artifact and original family producer custody.
   Resolve the selected family's full semantics; nonempty bytes or matching hashes
   do not establish admission. Empty/unsupported content follows that profile's
   refusal rule rather than being treated as a no-op group.
4. Match every contributing manifest entry's address and original artifacts to that
   native operation, preserving complete ordered contributors and all no-touch/
   finalized operations in the separately observed transaction cohort.
5. Independently establish actual effect readiness, canonical attribution and seal;
   later finalization/host settlement owns result, journal/feed and acknowledgment.

The context embeds the original family-admission artifact, not this group wrapper;
this group wrapper references the same family artifact without embedding the
context. That avoids a producer cycle or future digest used as its own input.
Repeated artifact copies still count independently in complete native row framing,
retention/reservation and repeated verification work. An 8-MiB body syntax ceiling
does not mean its complete operation row fits the 8-MiB custody frame.

The current minimal native context0.2 and six-byte administrative family fixtures
remain separately scoped evidence. They do not produce this carrier and cannot
be converted by inventing missing profile, address or original admission facts.
Adoption requires an explicitly versioned complete original producer, registered
codecs/roles/callable closure, complete native correspondence and current authority.
UMF owns metadata/key interpretation and Weft owns compilation; Truss owns this
private registry composition, not a second resolver/compiler.

Independent planned controls must include substituted operation/group address,
wrong kind, context/group artifact identity or byte mismatch, replay from another
installation/xid, reordered native contributors, unknown codec, omitted/extra
members, future/self-seal fields, and work exhaustion before publication. A case
with a valid shape and no original family admission must refuse. These are
unexecuted semantic integration exits; shape checks do not pass them or any of the
seven mandatory native bodies, consumer corpus, installer or release gates.
