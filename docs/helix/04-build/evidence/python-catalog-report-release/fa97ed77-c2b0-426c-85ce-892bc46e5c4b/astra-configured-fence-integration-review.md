# Configured archive fence integration — independent review

Disposition: **no blocker found for the stated private component scope**. This is a read-only source and retained-evidence review; no native tests, producers, or implementation edits were performed. Saved SMT queries were independently replayed in fresh Z3 contexts.

The configured wrapper checks the installed fence before archive selection and again after catalog effects. The verifier checks the unique routine, exact signature (including non-SETOF), owner correspondence, language/settings/security attributes, effective catalog ACL, original body length/hash, and the single exact ALWAYS statement trigger. The retained original body is 694 bytes with SHA-256 `9880d745800a1eb0e61f341053c04fdad219172815e95bbad20da369f50eefc9`.

The revised controls resolve the review findings. Both altered-body controls preserve original settings/signature and byte length; disabling only the body hash reproduces exactly those two failures. The default-ACL control independently observes native `proacl IS NULL` before refusal. The SETOF recreation preserves the original body and tests signature drift. Twenty-one pre-effect drift cases retain the original source after rollback and verify the first-effect sequence remains unused. The late-source and actual-stage archive change/restore controls exercise post-effect refusal and rollback separately.

## Final native evidence

All six packets have identical, current 274-input maps and exact ZIP contents, with no missing, additional, duplicate, or mismatched entries. All 1,614 retained native binary digests match. The five Python dependency distributions and 21 declared resource artifacts are retained; the latter total 101,453 bytes. Executed SQL digests and each exact marker-only mutant were verified. Raw test identities match the frozen AST inventories, and all applicable 14 dispatch regressions pass. Every packet records owned shutdown exit 0, status 3, absent socket, and removed temporary directories.

| Packet | Retained result |
|---|---|
| `fa97ed77-c2b0-426c-85ce-892bc46e5c4b` | 22 release/configured + 14 dispatch + 15 incoming tests pass: 51 total |
| `f8c0cabd-08bf-47fc-9c0c-a8fce0380a9e` | Exactly two verifier call sites omitted; 21 drift subcases + late-source case produce 22 intended non-refusals |
| `4fb3bf2e-f812-44eb-9a83-249cb074e5e6` | Only body hash comparison omitted; exactly two isolated body-change non-refusals |
| `50c1ff15-08ee-4b64-9083-ef0c94d53304` | Resource digest omission: one intended pre-cut non-refusal; late writes remain independently fenced |
| `d54640f1-c4f3-41d1-b0d7-cc093bc16e38` | Archive table lock omission: four intended non-refusals among 12 raw release methods |
| `9b421857-df35-45e3-be72-fb2fc0d51ac1` | Standalone fence predicate disabled: ten intended non-refusals across eight methods; configured dispatch and auxiliary groups deliberately not run |

All negative failures are the intended `DatabaseError not raised` assertions, with no incidental test errors. Negative auxiliary groups are explicitly absent. All six boundary logs report 499 imports. The positive receipt SHA-256 is `6fe57fbba0da97d2811f1d5aee302c3dfd47097a7815284b8e5c85c56ee88cc5`; the machine audit retains every receipt, archive, log, variant, and source hash.

## Conditional formal evidence

Packet `e6d9a719-d884-464c-a633-aa7a87258040` has four matching current source preimages and seven saved, digest-matching SMT queries. Independent fresh-context replay reproduces **four UNSAT and three SAT** results. Receipt SHA-256: `212dad572e38252cce7a60a445e9782f936255f20cc96218edb09e1abe8cbcd2`.

The model proves opaque-state one-step preservation under its fence premises, supporting finite-history induction only if those premises hold at every step. Its ABA counterexample models both change and restoration. The rollback-named counterexample stipulates loss of the live cut; it does not derive savepoint ancestry. This is not a refinement proof of the new installed verifier, PostgreSQL triggers/locks, or the configured native call.

## Qualification and history

The result is point-in-time correspondence to the selected original fence plus the tested archive-write exclusion. It does not authenticate the verifier, language implementation, owner or role reachability; checking catalog ACL grantees is not proof of exclusive effective actor authority. Two observations do not establish a continuously held function/configuration/source cut, prevent privileged source change/restore, or cover final host disclosure. Other source/configuration lock waits, full resource/CPU/deTOAST bounds, transitive installed-body meaning, public installer readiness, complete accepted-report authority, and backend acceptance remain open. The early length check is not a whole-allocation proof. No case promotion is supported.

Earlier setup failures and pre-isolation/pre-default-ACL passes remain historical. In particular, `9a80b46f`/`3b145e17` do not qualify the final default-ACL sources. The older standalone algebra and native packets are not substituted for these final integration controls.

Retained independent audit files:

- `/private/tmp/astra-configured-fence-integration-native-audit.json`
- `/private/tmp/astra-configured-fence-integration-formal-replay.json`
