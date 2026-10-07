# Complete-feed recovery storage allocation

Companion to CONTRACT-006 and CONTRACT-012. This proposal allocates remaining source-side durable homes; they are absent from the historical 0.6 DDL and now declared in the unqualified [0.7 SQL](../models/truss-layout-weft-review-0.7.proposal.sql). Downstream active-copy, application dedup and activation storage belong to the registered downstream adapter. Weft owns query compilation.

## Administrative receipt home

Allocate `complete_feed_administration_receipt` separately from the consumer. Logical identity is the complete canonical tuple `(trusted sourceEpoch, administrativeNamespace, requestId)`. Retain full identity bytes, exact canonical input and profile, original successful receipt and profile, actual database role, original verified authorization artifact and producing-transaction/commit-observation correspondence. A surrogate and nonunique digest index may route lookup; serialized full-byte comparison establishes uniqueness and input equality.

Under retention-administration exclusion, verify current administrative authorization, then look up the receipt before validating the expected worker generation. Equal input returns the original result; different input conflicts. An absent receipt proceeds to full worker/boundary validation and writes receipt and transition in one transaction. Store successful reseed/removal outcomes only. Pending durability, commit_unknown, conflict and unavailable remain observation/response classifications.

Receipt lifetime must not cascade with consumer deletion. Preserve original registration, prior/final generations, boundary, removal mode and evidence after removal/name reuse. A receipt visible within a supplied transaction is pending; independent original-transaction observation establishes committed durability. Retention preserves the selected retry/recovery horizon and receipt dependencies. No expiry duration or trimming authorization is introduced here.

## Seed attempt and artifact homes

Allocate `complete_feed_seed_attempt` with original SeedAttemptIdentity bytes and activation profile, source context, registration/generation, current complete activation-state bytes, inclusive replay floor and protection evidence. Retain terminal attempts for identity-reuse rejection and original recovery. Use surrogate/digest routing with full-byte equality. State transitions compare the complete expected state under worker/retention exclusion.

Allocate `complete_feed_seed_artifact` as an immutable collection retaining role, complete identity/profile bytes, payload bytes, digest and original production/custody evidence. Roles cover baseline, inventory, visibility/classifier, binding anchor, extraction, stage validation, downstream activation, source confirmation, invalidation and abandonment/containment. The selected procedure defines cardinality/order; preserve multiple ordered artifacts where required. A role or hash cannot confer authority.

Visibility retains original snapshot xmin/xmax/in-progress. Baseline/inventory retain original catalog/configuration/key-binding/transition/archive closure. Admit every artifact against original attempt, epoch, worker and profile. Persist neither exported-snapshot connection tokens nor serialized live verifier authority.

Composition remains originals → baseline → visibility/inventory → stage pins → activation → source confirmation. Earlier artifacts cannot reference later hashes. Register protection before extraction and write stage pins only after complete validation. Downstream activation commits independently. Source confirmation verifies original committed activation evidence and atomically updates attempt, consumer boundary and protection. Reconcile original artifacts rather than today's catalog or a fresh attempt.

Retire the classifier only after complete verified coverage through its original uncertainty interval, never after the first transaction or merely because no event occurs at xmax. Invalidation is not cleanup proof; abandonment requires original containment evidence. Reseed preserves the old boundary/protection until qualified replacement confirmation. Removing a consumer cannot cascade away independent pending-seed protection.

## Composition acceptance

The next profile must add all three homes with explicit columns, sequence/index/constraint identities and full canonical-byte/profile fields through existing UMF APIs. Selected native profiles define finite aggregate artifact/arbitration limits; do not truncate originals or invent a wire limit. Distinguish self-contained receipt retention from dependent journal/archive protection.

Deliver protected native producers/readers, role/grant/dependency inventory, independent lifecycle schedules and conversion preserving original bytes/commit correspondence. A generic archive alone cannot satisfy fencing, equality or retention. Missing originals require unavailable/reseed recovery, not reconstruction from JSONB/current state. Version the source layout, downstream adapter and Weft binding separately after composition.
