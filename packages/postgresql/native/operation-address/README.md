# Private operation-address codec

`encoder.sql` supplies a candidate `operation_address_original(text,xid8,bigint)`
bytea encoder for the existing four-string address proposal. It requires native
UTF8 text, rejects null/empty/negative inputs, preflights the complete escaped
8-MiB output bound, and uses the original native JSON string spelling. It never
reads or writes an operation registry or authenticates installation/transaction
inputs. PUBLIC EXECUTE is revoked; actual private role and complete native
closure qualification are installer responsibilities.

UMF retains the source and guarded export in
[the native artifact](../../../../docs/helix/02-design/contracts/operation-address-v0.1.proposal.umf.json).
Its declaration inventory is partial: no interpreted function/body semantics are
claimed. [The native receipt](../../../../docs/helix/04-build/evidence/design-audit/operation-address-encoder-native.json)
records 19 PostgreSQL16.15 observations, including Python byte parity, actual
fixture identity/attributes/ACL, native maximum domains, exact output ceiling and
ordinary direct-call denial. Native text NUL remains unsupported.

This helper is separate from the seventeen capacity routines and seven required
semantic bodies. It does not qualify an installed address profile, protected
admission, resource-account/deadline containment, managed targets or a public API.
Consume it only through an explicitly qualified original installed profile.
