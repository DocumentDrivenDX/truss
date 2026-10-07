import type {PrivateCustodySettlementSnapshotPg17 as Snapshot} from './truss-private-custody-settlement-snapshot-pg17.proposal';
const base={interfaceVersion:'truss-private-custody-settlement-snapshot-pg17/0.1.0-proposal',kind:'original-xid-settlement'} as const;
const unavailable:Snapshot={...base,fields:{original_writer_xid:'123',transaction_status:null}};
const diagnostic:Snapshot={...base,fields:{original_writer_xid:'123',transaction_status:'unrecognized-original-text'}};
// @ts-expect-error Native xid transport cannot be a host Number.
const numberXid:Snapshot={...base,fields:{original_writer_xid:123,transaction_status:'committed'}};
// @ts-expect-error Boolean is not an original native text/null status observation.
const booleanStatus:Snapshot={...base,fields:{original_writer_xid:'123',transaction_status:true}};
// @ts-expect-error Missing observation is not SQL NULL.
const missingStatus:Snapshot={...base,fields:{original_writer_xid:'123'}};
// @ts-expect-error Parent custody is a distinct data envelope.
const parent:Snapshot={...base,kind:'operation',fields:{original_writer_xid:'123',transaction_status:null}};
export {unavailable,diagnostic};
