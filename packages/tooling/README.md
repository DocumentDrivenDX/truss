# Truss administrative tooling components

`src/layout-migration-plan.ts` implements the pure candidate LM-01 manifest/route planner under CONTRACT-008. `planLayoutMigration(manifestBytes, observationBytes, targetVersion)` accepts closed numeric-free UTF-8 metadata and returns a frozen declared route, no steps, or a scoped refusal. It executes no SQL and opens no connection. No published package/export, installer, native observation, original artifact registration or migration application is available from this component.

The selected candidate metadata version uses three canonical decimal version components and exact lowercase SHA-256 text. Explicit routes carry complete ordered step IDs; no graph search, guessed intermediate path or generic inverse occurs. A cross-major route may be described explicitly, but runtime compatibility and actual upgrade qualification remain independently required. Default planning refuses a selected nontransactional route. An explicit reverse route describes metadata only and is not a qualification claim.

Run `bun test tests/layout-migration-plan.test.ts`. Native/admin/public-package migration schedules are LM-T01–08 in STP-045. Current tests qualify only metadata planning and refusal, not installed state, artifact authenticity, privileged execution, rollback or recovery.
