# Reference PostgreSQL actor custody

Status: design handoff under CONTRACT-005; no installed helper or native qualification. Preserve the existing native actor selection: selected role setting when it is not the native NONE sentinel, otherwise session_user. A helper's current_user is its definer owner and cannot replace this actor. The original public entry and every nested private dependency must share one admitted operation actor rather than accepting role strings from the request.

## Admission procedure

At the original public operation boundary, before any semantic effect or hidden collection, observe the native session identity, native role setting and the selected actor's exact native role identity. Retain the exact observed names and role identities together with the original operation/transaction context. Resolve through the trusted catalog under the selected policy/role exclusion; missing, ambiguous, unsupported or changed correspondence refuses. A name reused after role deletion cannot inherit the earlier role's operation custody. The selected server build, role settings grammar and adapter execution path are part of this admission, not inferred from a matching textual role.

The producer binding must specify where this boundary is observed. A pre-definer native observation may supply the original effective-role comparison when the actual mediated command path qualifies it. A definer entry can use the existing role-setting/session-user candidate only after its exact native behavior has been independently qualified against those original observations. An arbitrary invoker wrapper that forwards a role argument is not a trusted producer: ordinary callers can invoke the target independently or manufacture the argument unless the complete native call path prevents both. No new public actor-registration method, custom session GUC or client assertion is selected here.

Inside nested definers, retain the admitted actor while independently checking the native session/role context and original operation identity. Do not recapture current_user as a new actor or acquire fresh operation authority from the helper owner. Actor agreement does not replace current qualified module/owner checks. Recheck correspondence before protected effects and publication under the existing authority coordination; caller/role change invalidates the affected admission. Recovery retains the old attempt actor for attribution while separately admitting the actor requesting current disclosure. Commit by the supplied transaction owner remains independent of this capture.

The original actor producer and every reachable routine must exclude role/session-authorization changes and function-local settings that alter the admitted actor interpretation. Enumerate actual command routes, native routine settings and transitive calls before claiming this exclusion. Application SET ROLE outside a live admitted operation is supported only through fresh entry admission and its qualified membership graph; it cannot retroactively retag previous journal facts, receipts or pending effects. Administrative superuser/session-authorization paths remain outside ordinary-role enforcement and require their separate profile.

## Independent qualification cases

| Native schedule | Required outcome |
| --- | --- |
| Session A, native NONE, nested owners X then Y | A remains the actor; X/Y rights supply only the declared private responsibilities. |
| Session A with admitted SET ROLE B, nested owners X/Y | B remains the actor; native session A and original role-switch evidence remain retained. |
| A invokes a public entry with a request role string C | C creates no authority and does not alter native attribution. |
| Actor capture taken on another connection or earlier operation | Refuse before effects/disclosure, even if names match. |
| Role change between original admission and later mediated command | Invalidate the original admission; no publication under mixed actors. |
| Nested routine overrides the role interpretation or reconstructs from its owner | Refuse profile readiness; no helper-owner fallback. |
| Native role dropped/recreated with the same spelling | Old custody cannot identify the replacement role. |
| Role-setting grammar or sentinel correspondence cannot be distinguished exactly | Affected profile unavailable; do not normalize names or guess session fallback. |
| Recovery requester differs from the original operation actor | Preserve original attribution and require independent current disclosure authority. |

PostgreSQL 17 documents that current_user changes during SECURITY DEFINER execution in [system information functions](https://www.postgresql.org/docs/17/functions-info.html), and prohibits SET ROLE and SET SESSION AUTHORIZATION inside a definer in [SET ROLE](https://www.postgresql.org/docs/17/sql-set-role.html) and [SET SESSION AUTHORIZATION](https://www.postgresql.org/docs/17/sql-set-session-authorization.html). Those documented boundaries motivate the selected checks; they do not prove a specific hook, role-setting decoder, managed build or complete transitive path. Exact native producer/body/resource and role-change evidence remain required.
