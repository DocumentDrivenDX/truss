/** Private query data only; CONTRACT-001 native/source/authority/settlement admission remains separate. */
export interface PrivateCustodySettlementSnapshotPg17 {
 readonly interfaceVersion:'truss-private-custody-settlement-snapshot-pg17/0.1.0-proposal';
 readonly kind:'original-xid-settlement';
 readonly fields:{
  /** Canonical full xid text; spelling/native range/original association are runtime obligations. */
  readonly original_writer_xid:string;
  /** SQL NULL and unrecognized original text remain explicit diagnostic data. */
  readonly transaction_status:string|null;
 };
}
