# Reference Item.note presence binding proposal

This supplies the explicit Truss interpretation for the existing M00–M07 Item.note fixture; it changes no UMF core declaration or original fixture bytes. Original source: document truss.integration.account-items.v1, module integration, field Item.note, source pointer /modules/0/elements/3 in the [retained field inventory](reference-account-items-field-inventory.proposal.json). UMF's core ideal is absent-allowed value availability; physical absence and explicit null are bound here under CONTRACT-010 rather than inferred from that label.

The proposed logical field admits three distinct states: absent; present null; and present string, including the empty string. Preserve exact Unicode string content without normalization. Undefined, a missing observation, hidden rows, an unsupported decoder or a failed query cannot become any of these admitted states. A null transition changes presence/value meaning and is journaled under the selected complete history profile.

| Meaning | Required representation and observation |
| --- | --- |
| Absent | No property occurrence in the selected admitted home. A row-home zero-state observation establishes absence only after complete authorized owner/property visibility and applicability checks. Do not create a null node or materialize a default. |
| Present null | One explicit property occurrence carrying the selected public null value. In a qualified row home this is a null root node with no scalar payload, under full state/node/source correspondence. In props it is an explicitly present JSON member with JSON null. SQL NULL, missing JSON member and a lost state row are not substitutes. |
| Present string | One explicit property occurrence using the original string codec; empty text remains present string. Qualified row-home scalar/null/container and unused-slot checks remain mandatory. A nonstring present value refuses this field binding. |

Select one original storage home and exact value/presence/codec definitions before activation. The table describes supported candidate realizations, not a props fallback or evidence that either is installed. Preserve original source pointers/profile bytes and independent native inventory; native driver SQL NULL stays a transport observation requiring the selected projection grammar, never an automatic public null.

M03's absent B note, present-null C note and empty-string D note, M05's pending present-null update/rollback, and M06's confirmed present-null update exercise the three states independently. Expected public presence/token and complete native state/journal effects are authored before execution. M07 must project all required fixture fields under complete authority and the same independently qualified committed cut.

The accepted Weft B-005 candidate expressly excludes native-null semantics. It cannot qualify M07's complete compiled note projection through this Truss proposal alone. Retain an explicit unsupported/null-binding prerequisite until an exact compiler-owned presence/decoder/obligation registration is admitted and qualified. Do not omit Item.note, reinterpret null as absence, change the schema or add local SQL lowering to obtain a passing reduced milestone. Direct-read support and compiled-query support remain separate capabilities.

Native binding, encoder/decoder, domain admission, protected writer/collector, exact Weft registration, bounded transport/account and independent tests remain open. This proposal resolves the intended interpretation for review; it does not advertise installed support.

## Related owner capability and compatibility boundary

Weft 3facc649’s Ashlar candidate adds optional-scalar `value.presence`, with absent/value tagged output and explicit `native_null: false`. Present null remains a pre-query integrity refusal there. This provides related compiler-owned machinery, not the required three-state Truss binding. Keep old two-state registrations refusing C’s null; any new registration must retain complete state/root/payload provenance, independent owner-wide integrity and publication authority checks. Exact string, empty string and explicit null must survive whole-Record as well as scalar projection. Backend-specific JSON/presence-column lowering cannot substitute for the proposed Truss row-home realization. See the [updated owner review packet](weft-reference-note-presence-review.proposal.md).
