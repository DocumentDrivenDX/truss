# Reuse local checked object-effect context

Three existing helper calls now receive the exact plan and attempt already loaded and checked in the object-effect function. No helper signature, source, identity, authority, effect or deadline contract changes. Fresh writer/value checks and independent sealed-create identity checks remain intact.

Astra reviewed the plan and generated-source change. Eight basic native mutation, ownership, authority and incident-inventory workflows pass. Both real1,024-operation capacity tests pass: creation/commit, changed updates/commit, original replay/full readback, and late-fault rollback preserving caller work. These local results do not resolve the separately retained CI timeout. This is a narrow duplicate-read cleanup, with no claim of material performance improvement or release qualification.
