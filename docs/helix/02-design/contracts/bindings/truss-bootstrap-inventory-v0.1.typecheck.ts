import type {BootstrapNativeInventory} from './truss-bootstrap-inventory-v0.1';
declare const inventory:BootstrapNativeInventory;
// @ts-expect-error An empty observation cannot certify the complete fixed layout.
const empty:BootstrapNativeInventory={...inventory,entries:[]};
// @ts-expect-error Committed inventory requires actual original commit evidence.
const marker:BootstrapNativeInventory={...inventory,observation:{phase:'committed',installationId:'fixture'}};
// @ts-expect-error Ordinary table counts omit full installed policy/raw scope observations.
const count:BootstrapNativeInventory={...inventory,collection:{tables:'10'}};
void [empty,marker,count];

import type {BootstrapInventoryBasis} from './truss-bootstrap-inventory-v0.1';
declare const basis:BootstrapInventoryBasis;
// @ts-expect-error Original immutable basis excludes commit-dependent observation identity.
const commitBasis:BootstrapInventoryBasis={...basis,commitEvidence:inventory.collection.procedure};
// @ts-expect-error Actual observer session identity cannot alter immutable installed meaning.
const observerBasis:BootstrapInventoryBasis={...basis,policyMeaning:{...basis.policyMeaning,observer:{sessionRole:'observer',currentRole:'observer'}}};
void [commitBasis,observerBasis];

import type {BootstrapInventoryEntry} from './truss-bootstrap-inventory-v0.1';
declare const entry:BootstrapInventoryEntry;
// @ts-expect-error OID-only routine identity does not identify native overload semantics.
const oid:BootstrapInventoryEntry={...entry,objectKind:'routine',nativeIdentity:'12345'};
// @ts-expect-error Named routine identity must retain native argument identity.
const overload:BootstrapInventoryEntry={...entry,objectKind:'routine',nativeIdentity:{schema:'truss',name:'write'}};
// @ts-expect-error Column identity belongs to a qualified relation and exact ordinal.
const column:BootstrapInventoryEntry={...entry,objectKind:'column',nativeIdentity:{name:'id'}};
void [oid,overload,column];

const {ownership:omittedOwnership,...withoutOwnership}=entry;
// @ts-expect-error Physical identity requires full original expected-layout manifest provenance.
const unowned:BootstrapInventoryEntry=withoutOwnership;
void [omittedOwnership,unowned];

import type {RoutinePolicyInventory} from './truss-installed-policy-v0.1';
declare const routinePolicy:RoutinePolicyInventory;
const {grants:omittedGrants,...oldRoutineProjection}=routinePolicy;
// @ts-expect-error Effective execute roles do not substitute for grant provenance.
const legacyRoutine:RoutinePolicyInventory=oldRoutineProjection;
// @ts-expect-error Bootstrap immutable policy meaning requires routine grant facts too.
const legacyBasis:BootstrapInventoryBasis={...basis,policyMeaning:{...basis.policyMeaning,routines:[oldRoutineProjection]}};
const publicGrant:RoutinePolicyInventory['grants'][number]={grantor:'owner',grantee:{kind:'public'},privilege:'EXECUTE',grantOption:false};
const namedPublicGrant:RoutinePolicyInventory['grants'][number]={...publicGrant,grantee:{kind:'role',name:'public'}};
// @ts-expect-error A routine grant cannot silently omit original grantor.
const missingGrantor:RoutinePolicyInventory['grants'][number]={grantee:{kind:'public'},privilege:'EXECUTE',grantOption:false};
// @ts-expect-error The selected routine privilege subset cannot accept table SELECT.
const unsupportedGrant:RoutinePolicyInventory['grants'][number]={...publicGrant,privilege:'SELECT'};
void [omittedGrants,legacyRoutine,legacyBasis,publicGrant,namedPublicGrant,missingGrantor,unsupportedGrant];

import type {InstalledPolicyInventory,NamespacePolicyInventory} from './truss-installed-policy-v0.1';
declare const policyInventory:InstalledPolicyInventory;
const {namespaces:omittedNamespaces,...oldPolicyProjection}=policyInventory;
// @ts-expect-error Administrative capability strings do not replace namespace policy meaning.
const legacyPolicy:InstalledPolicyInventory=oldPolicyProjection;
// @ts-expect-error Deployment/reached namespace scope cannot be represented by an empty tuple.
const emptyNamespaceBasis:BootstrapInventoryBasis={...basis,policyMeaning:{...basis.policyMeaning,namespaces:[]}};
declare const schemaGrant:NamespacePolicyInventory['grants'][number];
// @ts-expect-error Schema privileges cannot be decoded using routine EXECUTE meaning.
const wrongSchemaPrivilege:NamespacePolicyInventory['grants'][number]={...schemaGrant,privilege:'EXECUTE'};
void [omittedNamespaces,legacyPolicy,emptyNamespaceBasis,wrongSchemaPrivilege];

import type {RelationGrant,RelationPolicyInventory,SequencePolicyInventory} from './truss-installed-policy-v0.1';
declare const relationPolicy:RelationPolicyInventory;
const {grants:omittedRelationGrants,...oldRelationProjection}=relationPolicy;
// @ts-expect-error Effective relation rights cannot replace grant provenance.
const legacyRelation:RelationPolicyInventory=oldRelationProjection;
// @ts-expect-error Column grants cannot carry relation-only DELETE privileges.
const columnDelete:RelationGrant={grantor:'owner',grantee:{kind:'public'},grantOption:false,column:{kind:'column',name:'id'},privilege:'DELETE'};
declare const sequencePolicy:SequencePolicyInventory;
const {grants:omittedSequenceGrants,...oldSequenceProjection}=sequencePolicy;
// @ts-expect-error A sequence grant inventory is mandatory.
const legacySequence:SequencePolicyInventory=oldSequenceProjection;
// @ts-expect-error Sequence grants cannot carry table INSERT privileges.
const sequenceInsert:SequencePolicyInventory['grants'][number]={grantor:'owner',grantee:{kind:'public'},privilege:'INSERT',grantOption:false};
void [omittedRelationGrants,legacyRelation,columnDelete,omittedSequenceGrants,legacySequence,sequenceInsert];

import type {RelationEffectivePrivilege} from './truss-installed-policy-v0.1';
// @ts-expect-error Relation-only MAINTAIN cannot be projected as a column right.
const columnMaintain:RelationEffectivePrivilege={role:'writer',column:{kind:'column',name:'id'},privilege:'MAINTAIN',grantOption:false};
// @ts-expect-error Unknown privilege strings cannot enter stable relation meaning.
const unknownRight:RelationEffectivePrivilege={role:'writer',column:{kind:'relation'},privilege:'UNRECOGNIZED',grantOption:false};
const stableAdmin:BootstrapInventoryBasis['policyMeaning']['administrativeCapabilities'][number]={role:'writer',capability:'schema_create',permitted:false};
// @ts-expect-error Stable administrative triples exclude volatile evidence artifacts.
const volatileAdmin:BootstrapInventoryBasis['policyMeaning']['administrativeCapabilities'][number]={...stableAdmin,evidence:inventory.collection.procedure};
void [columnMaintain,unknownRight,stableAdmin,volatileAdmin];

const publicPolicyRoles:RelationPolicyInventory['policies'][number]['roles']=[{kind:'public'},{kind:'role',name:'public'}];
// @ts-expect-error Plain role strings cannot preserve PUBLIC versus real-role identity.
const oldPolicyRoles:RelationPolicyInventory['policies'][number]['roles']=['public'];
void [publicPolicyRoles,oldPolicyRoles];

declare const rlsPolicy:RelationPolicyInventory['policies'][number];
// @ts-expect-error Native polcmd codes must be decoded to selected public command meaning.
const rawRlsCommand:RelationPolicyInventory['policies'][number]={...rlsPolicy,command:'r'};
// @ts-expect-error RLS policy command domain excludes TRUNCATE.
const truncatePolicy:RelationPolicyInventory['policies'][number]={...rlsPolicy,command:'TRUNCATE'};
void [rawRlsCommand,truncatePolicy];

import type {RowSecurityPolicyInventory} from './truss-installed-policy-v0.1';
const selectPolicy:RowSecurityPolicyInventory={name:'read',definition:inventory.collection.procedure,command:'SELECT',permissive:true,roles:[{kind:'public'}],usingExpression:'true',checkExpression:null};
// @ts-expect-error SELECT policies cannot contain WITH CHECK.
const selectWithCheck:RowSecurityPolicyInventory={...selectPolicy,checkExpression:'true'};
// @ts-expect-error INSERT policies cannot contain USING.
const insertWithUsing:RowSecurityPolicyInventory={name:'write',definition:inventory.collection.procedure,command:'INSERT',permissive:true,roles:[{kind:'public'}],usingExpression:'true',checkExpression:'true'};
const updateFallback:RowSecurityPolicyInventory={name:'change',definition:inventory.collection.procedure,command:'UPDATE',permissive:true,roles:[{kind:'role',name:'writer'}],usingExpression:'allowed',checkExpression:null};
void [selectPolicy,selectWithCheck,insertWithUsing,updateFallback];

const {definition:omittedPolicyDefinition,...textOnlyPolicy}=selectPolicy;
// @ts-expect-error Deparsed expression strings do not substitute for full admitted definition.
const incompletePolicy:RowSecurityPolicyInventory=textOnlyPolicy;
void [omittedPolicyDefinition,incompletePolicy];

declare const triggerMeaning:RelationPolicyInventory['triggers'][number];
const {definition:omittedTriggerDefinition,...displayOnlyTrigger}=triggerMeaning;
// @ts-expect-error Trigger display SQL does not replace complete definition meaning.
const incompleteTrigger:RelationPolicyInventory['triggers'][number]=displayOnlyTrigger;
declare const constraintMeaning:RelationPolicyInventory['constraints'][number];
const {definition:omittedConstraintDefinition,...displayOnlyConstraint}=constraintMeaning;
// @ts-expect-error Constraint display SQL does not replace complete definition meaning.
const incompleteConstraint:RelationPolicyInventory['constraints'][number]=displayOnlyConstraint;
void [omittedTriggerDefinition,incompleteTrigger,omittedConstraintDefinition,incompleteConstraint];

const relationConstraint:BootstrapInventoryEntry={...entry,objectKind:'constraint',nativeIdentity:{name:'positive',owner:{kind:'relation',relation:{schema:'truss',name:'object'}}}};
const domainConstraint:BootstrapInventoryEntry={...entry,objectKind:'constraint',nativeIdentity:{name:'positive',owner:{kind:'domain',domain:{schema:'external',name:'positive_integer'}}}};
// @ts-expect-error Domain constraint must retain its qualified domain owner.
const absentDomain:BootstrapInventoryEntry={...entry,objectKind:'constraint',nativeIdentity:{name:'positive',owner:{kind:'domain'}}};
// @ts-expect-error A constraint cannot conflate relation and domain ownership.
const mixedConstraintOwner:BootstrapInventoryEntry={...entry,objectKind:'constraint',nativeIdentity:{name:'positive',owner:{kind:'domain',domain:{schema:'external',name:'positive_integer'},relation:{schema:'truss',name:'object'}}}};
// @ts-expect-error Relation-only draft constraint shape cannot silently infer owner kind.
const untaggedConstraint:BootstrapInventoryEntry={...entry,objectKind:'constraint',nativeIdentity:{name:'positive',relation:{schema:'truss',name:'object'}}};
// @ts-expect-error Row-security policy remains relation-owned, not domain-owned.
const domainPolicy:BootstrapInventoryEntry={...entry,objectKind:'policy',nativeIdentity:{name:'positive',owner:{kind:'domain',domain:{schema:'external',name:'positive_integer'}}}};
void [relationConstraint,domainConstraint,absentDomain,mixedConstraintOwner,untaggedConstraint,domainPolicy];

import type {TypePolicyInventory,LanguagePolicyInventory} from './truss-installed-policy-v0.1';
declare const typePolicy:TypePolicyInventory;
declare const languagePolicy:LanguagePolicyInventory;
const {grants:omittedTypeGrants,...legacyTypePolicy}=typePolicy;
// @ts-expect-error Type effective rights cannot replace actual grant provenance.
const missingTypeGrants:TypePolicyInventory=legacyTypePolicy;
// @ts-expect-error Language facts require actual native trust classification.
const missingLanguageTrust:LanguagePolicyInventory={language:'plpgsql',owner:'owner',grants:[],effectivePrivileges:[]};
// @ts-expect-error Type USAGE cannot accept routine EXECUTE privilege.
const invalidTypeGrant:TypePolicyInventory['grants'][number]={grantor:'owner',grantee:{kind:'public'},privilege:'EXECUTE',grantOption:false};
const {types:omittedTypes,...legacyWithoutTypes}=policyInventory;
// @ts-expect-error Installed policy must explicitly account for reached types.
const absentTypeInventory:InstalledPolicyInventory=legacyWithoutTypes;
void [languagePolicy,omittedTypeGrants,missingTypeGrants,missingLanguageTrust,invalidTypeGrant,omittedTypes,absentTypeInventory];
