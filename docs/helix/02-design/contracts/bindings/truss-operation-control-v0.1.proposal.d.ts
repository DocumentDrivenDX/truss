/** Private CONTRACT-007/CONTRACT-001 OC binding. Design only; no public export.
 * Brands are static guidance. The actual adapter must recognize object identity
 * in its original physical issuer registry and reject copied/foreign entries.
 */
declare const reservationBrand: unique symbol;
declare const issuedBrand: unique symbol;
declare const boundBrand: unique symbol;
declare const confirmedBrand: unique symbol;
declare const recoveryBrand: unique symbol;

export interface OperationControlReservation {
  readonly [reservationBrand]: true;
}
/** Issued privately by the original shared counter after enclosing reservation.
 * This token is not reconstructed from the ordinal text or a registry row.
 */
export interface IssuedOperationOrdinal {
  readonly [issuedBrand]: true;
  readonly ordinal: string;
}
export interface BoundOperationControl {
  readonly [boundBrand]: true;
  readonly ordinal: string;
}
/** Original registered savepoint/native correspondence, not C/Z tags alone. */
export interface ConfirmedOperationControl {
  readonly [confirmedBrand]: true;
  readonly ordinal: string;
}
export interface OperationControlRecovery {
  readonly [recoveryBrand]: true;
}
export type ControlReservationResult =
  | { readonly status: 'reserved'; readonly reservation: OperationControlReservation }
  | { readonly status: 'refused'; readonly reason: 'custody' | 'closed' | 'resource' | 'cancelled' | 'profile';
      readonly reservation?: never };
export type OperationBindingResult =
  | { readonly status: 'bound'; readonly control: BoundOperationControl }
  | { readonly status: 'refused'; readonly reason: 'custody' | 'closed' | 'consumed' | 'cancelled' | 'profile';
      readonly control?: never };
export type SavepointControlResult =
  | { readonly status: 'confirmed'; readonly control: ConfirmedOperationControl }
  | { readonly status: 'refused_before_submission'; readonly control?: never;
      readonly reason: 'custody' | 'closed' | 'consumed' | 'cancelled' | 'profile' }
  | { readonly status: 'confirmed_failure'; readonly control?: never;
      readonly recovery: OperationControlRecovery }
  | { readonly status: 'unavailable'; readonly control?: never;
      readonly recovery: OperationControlRecovery };

/** Created by the original adapter after physical transaction adoption, with
 * its original account, profile, exclusivity and registered control definitions.
 * No application factory, caller connection replacement or supplied proof flag.
 */
export interface OperationControlProducer {
  /** Reserve forward and containment obligations; recheck before ticket publish.
   * Refusal submits nothing and does not consume an operation ordinal.
   */
  reserveOperationControl(): ControlReservationResult;
  /** Consume the original reservation and original issued token exactly once.
   * All failures after issuance leave that ordinal burnt. No refund/reset API.
   */
  bindIssuedOperation(reservation: OperationControlReservation,
    issued: IssuedOperationOrdinal): OperationBindingResult;
  /** Consume submission permission on entry. Only original correlated native
   * savepoint confirmation can return confirmed. Never retry on any outcome.
   * An escaped exception is unavailable, retaining the pre-registered recovery
   * association internally; it cannot authorize another submission.
   */
  submitOperationSavepoint(control: BoundOperationControl): Promise<SavepointControlResult>;
}

/** Only this confirmed registry entry can enter the existing native admission
 * dispatcher. It must additionally verify original issuer/native authority,
 * full actor/epoch/configuration context and inventory before registry effects.
 * This boundary does not expose ordinal-bearing SQL or grant an EXECUTE right.
 */
export interface ConfirmedOperationAdmission<OriginalAdmissionInput, NativeAdmissionResult> {
  admitConfirmedOperation(control: ConfirmedOperationControl,
    input: OriginalAdmissionInput): Promise<NativeAdmissionResult>;
}
