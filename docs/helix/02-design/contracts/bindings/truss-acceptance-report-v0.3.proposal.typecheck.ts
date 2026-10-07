import type {CatalogReactivation,ReactivatedCatalogIdentity,ProposedComposedAcceptanceReport} from './truss-acceptance-report-v0.3.proposal';
import type {ProposedAcceptanceReport} from './truss-acceptance-report-v0.2.proposal';
const key:ReactivatedCatalogIdentity={kind:'key',typeId:'2',keyNumber:'1'};
// @ts-expect-error Key identity requires its original owner type.
const unowned:ReactivatedCatalogIdentity={kind:'key',keyNumber:'1'};
// @ts-expect-error A global key ID cannot replace owner-local number.
const global:ReactivatedCatalogIdentity={kind:'key',keyId:'k'};
// @ts-expect-error Native identifiers cannot be host numbers.
const numeric:ReactivatedCatalogIdentity={kind:'type',typeId:2};
declare const transition:CatalogReactivation;
// @ts-expect-error Original before definition is required.
const missing:CatalogReactivation={identity:key,owner:transition.owner,lineage:transition.lineage,beforeRetiredRevision:'1',afterDefinition:transition.afterDefinition};
declare const old:ProposedAcceptanceReport;
// @ts-expect-error Previous report version lacks lifecycle inventory and discriminator.
const upgraded:ProposedComposedAcceptanceReport=old;
void [key,unowned,global,numeric,missing,upgraded];
