# Ordinary read-only executor table cut

Original native SQL locks only the six selected existing truss tables through a no-input, pinned-path SECURITY DEFINER function. PUBLIC access is revoked. The native fixture uses actual populated accepted graph tables, not relational shadows, and grants one dedicated ordinary executor SELECT on object plus helper EXECUTE. Direct SHARE lock and UPDATE refuse42501. Exact held-lock readback and independent RowExclusive DELETE WHERE false controls establish the selected table cuts; rollback release is witnessed by successful same writer statements. No data is deleted.

The helper must be source/owner/ACL qualified and installer-bound before producer use. It covers selected object, Subject map, archive, epoch pointer/registry and generation guard; broader metadata/callable/config/authority closure is separate. A private executor can read the selected data; it receives no direct catalog/resource mutation grant. This is not full backend admission.
