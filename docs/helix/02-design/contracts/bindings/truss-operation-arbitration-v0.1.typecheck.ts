/** Private consumer boundaries only; no native/lifecycle support inference. */
import type {HostOperationArbitration, OperationAttempt, OperationLease,
 OperationArbitrationRegistration, OperationAdmissionResult} from './truss-operation-arbitration-v0.1';
declare const service:HostOperationArbitration;
declare const attempt:OperationAttempt;
declare const lease:OperationLease;
void service.acquire(attempt);
void service.observe(attempt);
void service.abandonPrepared(attempt);
// @ts-expect-error an attempt is not an acquired original lease
void service.release(attempt,{identity:'completion',bytesBase64:'e30=',sha256:'digest'});
// @ts-expect-error a lease cannot acquire another operation
void service.acquire(lease);
// @ts-expect-error ordinary metadata cannot mint an original acquisition attempt
const forgedAttempt:OperationAttempt={};
// @ts-expect-error ordinary metadata cannot mint a registry registration
const forgedRegistration:OperationArbitrationRegistration={};
// @ts-expect-error unresolved acquisition cannot disclose a usable lease
const confused:OperationAdmissionResult={status:'unresolved',recoveryReferences:['original'],lease};
// @ts-expect-error unresolved recovery must retain a nonempty original reference inventory
const emptyRecovery:OperationAdmissionResult={status:'unresolved',recoveryReferences:[]};
void [forgedAttempt,forgedRegistration,confused,emptyRecovery];
