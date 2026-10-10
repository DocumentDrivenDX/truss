# S3 reference history archive candidate

Status: proposed provider realization of the [durable handoff](reference-history-archive-handoff.proposal.md), not a selected provider, provisioned deployment or qualified durability claim. CONTRACT-002 remains governing. Source review date: 2026-10-08. Preserve the existing archive v0.2 bytes and retention tooling; this proposal adds provider obligations, not a second archive format.

## Candidate scope

Use a versioned S3 general purpose bucket, S3 Standard storage and Object Lock compliance retention. Pin account, region, bucket, endpoint, permitted prefix, encryption mechanism, SDK/build and recovery identity in the eventual qualified profile. Exclude directory buckets, transformed retrieval endpoints and automatic transition to restore-required storage from this initial candidate. These are proposed scope limits, not claims about alternatives.

Compliance retention protects an individual version until its retention date, whereas governance retention permits privileged bypass. A simple deletion may still insert a delete marker. [AWS Object Lock documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html). Consequently, the recovery locator is the exact bucket/key/version tuple, never just the current key. Admit retention long enough for every obligation being discharged; an unbounded advertised horizon cannot be satisfied by a finite retention date without a separately qualified continuing protection procedure.

## Original submission and uncertain outcomes

Allocate a stable export key under the admitted installation namespace before submission. Its original protected record retains complete archive bytes, byte length, digest, source/coverage context and attempt identity. Neither a digest-derived key nor user-supplied metadata proves original correspondence.

Propose bounded single-request PutObject with `If-None-Match: *` and explicit compliance retention. Enforce conditional creation through the eventual bucket policy. AWS documents 412 on existing current objects and possible 409 conflicts; a current delete marker allows creation again. [Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html), [policy enforcement](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes-enforce.html). Therefore 412 is an observation trigger, not an idempotent-success receipt. A 409, timeout or lost response does not authorize local cleanup or blind replacement.

The proposed writer policy denies deletion, unconstrained overwrite and alternate copy paths. Exact policy and privileged administrative assumptions need qualification. If acknowledgment is lost, use bounded original-key observation to identify the candidate version and compare its complete bytes and lock evidence with original custody. Only an unambiguous match may establish a recovery locator. Changed contents conflict; ambiguous version history, inaccessible evidence or exhausted observation budget stays unresolved. Do not issue a replacement key merely to escape uncertainty. Multipart submission is outside this first candidate and requires its own upload-ID, part, completion and orphan protocol before admission.

## Independent recovery admission

Read the full original version through the actual recovery identity, without local cache or byte transformation. Verify returned locator, exact length, complete bytes and archive interpretation against original custody. A HEAD result, provider checksum or ETag is insufficient evidence of full recovery. Version-specific retrieval needs `s3:GetObjectVersion`; some archive storage classes need restoration before GET. [GetObject API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html).

Observe version-specific compliance mode and retention deadline separately. Admit actual recovery authorization and encryption lifetime. Object Lock does not preserve access to deleted encryption keys, and lifecycle can add delete markers while retaining locked versions. [Object Lock considerations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html). These facts motivate explicit key custody and version retrieval; they do not establish operational availability.

Carry the verified locator and complete coverage evidence into the handoff's fresh native protection admission. S3 observation never classifies the database COMMIT outcome. Only confirmed outer commit publishes local horizon advancement.

## Required qualification outputs

Before activation, supply exact SDK transport hooks and cumulative byte/copy/request/deadline bounds, policy and role closure, encryption lifetime, retention calculation and renewal procedure if needed, provider observation producer and protected locator persistence. Run STP-019 AH-01–06 against the actual provider, adding delete-marker/key-recreation, wrong-version retrieval, retention expiry, privileged policy change and encryption-loss schedules. Verify native settlement independently. All remain unexecuted. No bucket or credentials were accessed for this proposal.
