/** Inventory shape distinctions only; no native completeness proof. */
import type {MigrationSourceEntry,MigrationTargetEntry,KeyMigrationSourceInventory,KeyMigrationConflictClass} from '../../../02-design/contracts/bindings/truss-key-migration-inventory-v0.1';
import type {ExactArtifact} from '../../../02-design/contracts/bindings/truss-acceptance-input-v0.1';
declare const artifact:ExactArtifact;
declare const source:Extract<MigrationSourceEntry,{readonly kind:'reservation'}>;
declare const fullKey:typeof source.fullKey;
declare const inventory:KeyMigrationSourceInventory;
// @ts-expect-error Reservation requires original full bytes; omitted live membership is not equivalent.
const omittedReservation:MigrationSourceEntry={...source,fullKey:undefined,membership:{state:'omitted',originalMissingComponentReport:artifact}};
// @ts-expect-error Preserved components require their original artifact.
const missingComponents:MigrationSourceEntry={...source,components:{state:'preserved'}};
// @ts-expect-error Held target requires derivation evidence rather than a caller success flag.
const unprovedTarget:MigrationTargetEntry={sourceEntryId:'original',state:'held',fullKey};
// @ts-expect-error Empty raw observation cannot constitute independent complete collection.
const countOnly:KeyMigrationSourceInventory={...inventory,collection:{...inventory.collection,rawEvidence:[]}};
// @ts-expect-error One member does not constitute an equality conflict class.
const singleton:KeyMigrationConflictClass={fullKey,sourceEntryIds:['one'],policy:fullKey.encoding,evidence:artifact};

const {entryIdentityProfile:removedProfile,...missingProfileInventory}=inventory;
// @ts-expect-error Address grammar must be explicitly pinned; inventory profile alone cannot select it.
const implicitAddress:KeyMigrationSourceInventory=missingProfileInventory;
