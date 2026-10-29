# Truss typed-SDK consumer candidate

Source and artifact inspection plus cold fixture controls only. No installation,
real SDK/compiler import, native process, Actions run or release was performed.
Accessdev8 is byte-identical between the SDK owner handoff and the public SDK0.5.7
asset. SDK0.5.8 generic cohort proof is not Truss consumer acceptance.

`public-metadata.json` retains actual PyPI metadata summaries and artifact hashes:
umf-truss0.0.51 exists; umf-accessdev5 and dev8 both returned404. Original fetched
metadata and both inspected Access wheels remain under
`/private/tmp/truss-typed-sdk-upgrade-20261029` and are not copied into this tree.
The source hash/name inspection is static; it establishes no behavior or support.
The canonical function AST is unchanged after its move. Conditional MISSING
re-exports were inspected in a byte-identical module.

Eight cohort controls and fourteen registry-workflow/publisher controls passed.
The cohorts use inert fixture packages and the workflow tests execute the actual
inline gate bodies with mocked metadata/modules; their passed status is local
control evidence, not an actual installed consumer or registry execution.
The closed native/installed gate and its required original cleanup are specified
in the existing Python consumer integration plan.
