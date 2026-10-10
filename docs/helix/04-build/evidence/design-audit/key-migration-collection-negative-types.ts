/** Source locator distinctions; exact native/cut correspondence remains semantic. */
import type {BucketMigrationCollectionEvidence,BucketMigrationSourceLocator} from '../../../02-design/contracts/bindings/truss-key-migration-collection-v0.1';
declare const collection:BucketMigrationCollectionEvidence;
declare const live:Extract<BucketMigrationSourceLocator,{readonly kind:'live_binding'}>;
declare const reservation:Extract<BucketMigrationSourceLocator,{readonly kind:'reservation'}>;
// @ts-expect-error Whole live-domain exhaustion cannot substitute for reservation-domain exhaustion.
const oneStream:BucketMigrationCollectionEvidence={...collection,exhaustion:{live:collection.exhaustion.live}};
// @ts-expect-error Source instance locator needs actual identity, not only projection storage ID.
const projected:BucketMigrationSourceLocator={kind:'live_binding',projection:live.projection};
// @ts-expect-error Reservation cannot acquire omitted-live membership.
const omitted:BucketMigrationSourceLocator={...reservation,projection:{state:'omitted',originalMissingComponentReport:reservation.originalReservation}};
// @ts-expect-error Native source and exclusion cannot be inferred from a count-only record.
const countOnly:BucketMigrationCollectionEvidence={interfaceVersion:'truss-key-migration-bucket-collection/0.1.0',entries:[]};
