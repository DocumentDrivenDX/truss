import type { OperationControlProducer, IssuedOperationOrdinal,
  ConfirmedOperationAdmission, ConfirmedOperationControl, SavepointControlResult }
  from './truss-operation-control-v0.1.proposal';

declare const producer: OperationControlProducer;
declare const issued: IssuedOperationOrdinal;
declare const admission: ConfirmedOperationAdmission<{ original: Uint8Array }, unknown>;
declare const result: SavepointControlResult;

const reserved = producer.reserveOperationControl();
if (reserved.status === 'reserved') {
  const bound = producer.bindIssuedOperation(reserved.reservation, issued);
  if (bound.status === 'bound') {
    producer.submitOperationSavepoint(bound.control);
    // @ts-expect-error Binding alone cannot authorize native admission.
    admission.admitConfirmedOperation(bound.control, { original: new Uint8Array() });
  }
}
if (result.status === 'confirmed') {
  admission.admitConfirmedOperation(result.control, { original: new Uint8Array() });
} else {
  // @ts-expect-error Refusal, failure and unknown outcomes carry no confirmation.
  admission.admitConfirmedOperation(result.control, { original: new Uint8Array() });
}
// @ts-expect-error Text spelling cannot construct original issuer custody.
const forged: IssuedOperationOrdinal = { ordinal: '0' };
// @ts-expect-error Safe JavaScript numbers still are not ordinal transport.
const numeric: IssuedOperationOrdinal['ordinal'] = 0;
// @ts-expect-error A caller boolean/ordinal cannot prove savepoint confirmation.
const confirmation: ConfirmedOperationControl = { ordinal: '0', confirmed: true };
void forged; void numeric; void confirmation;
