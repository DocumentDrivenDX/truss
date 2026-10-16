// Original public UMF ESM is emitted unchanged by the owned asset builder.
import * as owner from '@truss/umf-local-actions';
import {prepareDocument,type CatalogSnapshot,CATALOG_PROFILE} from './catalog';
import type {StoreInfo} from './store';
declare const actionBrand:unique symbol,grantBrand:unique symbol;
export interface LocalAction {readonly [actionBrand]:true}
export interface SelectionReadGrant {readonly [grantBrand]:true}
export interface ActionIdentity {module:string;action:string}
export interface BrowserActionRegistration {action:LocalAction;model:Artifact;modelPin:Record<string,string>;actionPin:Record<string,unknown>;preparation:Artifact}
export interface SelectionReadRegistration {grant:SelectionReadGrant;declaration:Record<string,unknown>}
interface Artifact {mediaType:string;utf8:string;sha256:string}
const PRODUCER='sha256:6b331c0b5118435a79eb19b3c66464b4ea1ed3e70134fc3b71e07913487a408b';
const copy=<T>(value:T):T=>JSON.parse(JSON.stringify(value));
const frozen=<T>(value:T):T=>{if(value&&typeof value==='object'){for(const child of Object.values(value))frozen(child);Object.freeze(value);}return value;};
export function captureAction(input:ActionIdentity):Readonly<ActionIdentity>{
 if(!input||Object.keys(input).sort().join(',')!=='action,module')throw Error('Exact qualified action identity required');
 const {module,action}=input;
 for(const value of [module,action])if(typeof value!=='string'||!value||value.length>256||value.includes('\0')
  ||new TextDecoder('utf-8',{fatal:true}).decode(new TextEncoder().encode(value))!==value)throw Error('Bounded original action identity required');
 return Object.freeze({module,action});
}
interface RetainedAction {cut:string;model:Artifact;modelPin:Record<string,string>;actionPin:Record<string,unknown>;preparation:Artifact;context:any;target:any;fields:any[]}
/** Per-open worker custody. A serialized declaration never issues a capability. */
export function createActionIssuer(info:StoreInfo,isOpen:()=>boolean){
 const actions=new WeakMap<LocalAction,RetainedAction>(),grants=new WeakMap<SelectionReadGrant,{action:LocalAction;cut:string;declaration:Record<string,unknown>}>();
 const open=()=>{if(!isOpen())throw Error('Current open store required');};
 const cut=(catalog:CatalogSnapshot|null)=>{
  if(!catalog||catalog.profile!==CATALOG_PROFILE)throw Error('Current registered browser catalog required');
  return JSON.stringify({info,catalog});
 };
 const retained=(catalog:CatalogSnapshot|null,action:LocalAction)=>{
  open();const value=actions.get(action);
  if(!value||value.cut!==cut(catalog))throw Error('Current original issued action required');
  return value;
 };
 return Object.freeze({
  async register(catalog:CatalogSnapshot|null,input:Readonly<ActionIdentity>):Promise<BrowserActionRegistration>{
   open();const originalCut=cut(catalog),doc=catalog!.document;
   const documentId=doc.documentId,documentRevision=doc.documentRevision,sourceUtf8=doc.sourceUtf8,sha256=doc.sourceSha256;
   if([documentId,documentRevision,sourceUtf8,sha256].some(v=>typeof v!=='string'))throw Error('Original catalog document required');
   // Reuse the existing closed, unprotected browser catalog subset before issuing reads.
   const admitted=await prepareDocument({documentId:documentId as string,documentRevision:documentRevision as string,sourceUtf8:sourceUtf8 as string});
   const model=frozen({mediaType:'application/json',utf8:sourceUtf8 as string,sha256:sha256 as string});
   const modelPin=frozen({documentId:documentId as string,revision:documentRevision as string,umfVersion:'0.8.0',sha256:sha256 as string});
   const actionPin=frozen({identity:{module:input.module,action:input.action},documentSha256:sha256,invocation:{id:'umf.actions.local-tx',version:'1'}});
   const context={registry:owner.createUmfRegistry(),models:[{pin:modelPin,artifact:model}],actions:[{pin:actionPin,artifact:model}],selections:[]};
   const preparation=frozen(owner.prepareActionPlanModel(modelPin,actionPin,context) as Artifact),prepared=JSON.parse(preparation.utf8);
   if(prepared.producer?.build!==PRODUCER||prepared.action.invocation.id!=='umf.actions.local-tx'||prepared.action.invocation.version!=='1')throw Error('Pinned original local preparation required');
   if(admitted.sourceSha256!==sha256)throw Error('Original document digest mismatch');
   const observations=admitted.documents[0]!.validation.observations.filter((o:any)=>o.operation==='inspectCoreRecordMembers'&&o.identity.module===prepared.target.module&&o.identity.element===prepared.target.element);
   if(observations.length!==1)throw Error('Original target membership observation required');
   const members=observations[0].result.meaning;
   if(members.state!=='known'||members.uninterpretedPaths.length||!members.members.length)throw Error('Complete original target membership required');
   const target=frozen(copy(prepared.target)),fields=frozen(copy(members.members));
   open(); // An admitted async request cannot issue a handle after close starts.
   const action=Object.freeze(Object.create(null)) as LocalAction;
   actions.set(action,{cut:originalCut,model,modelPin,actionPin,preparation,context,target,fields});
   return {action,model:copy(model),modelPin:copy(modelPin),actionPin:copy(actionPin),preparation:copy(preparation)};
  },
  grant(catalog:CatalogSnapshot|null,action:LocalAction):SelectionReadRegistration{
   const original=retained(catalog,action);
   const declaration=frozen({profile:{id:'umf.actions.local-store-read',version:'1'},target:copy(original.target),fields:copy(original.fields),view:'complete-canonical-target-population',disposition:'original'});
   const grant=Object.freeze(Object.create(null)) as SelectionReadGrant;
   grants.set(grant,{action,cut:original.cut,declaration});
   return {grant,declaration:copy(declaration)};
  },
  requireGrant(catalog:CatalogSnapshot|null,action:LocalAction,grant:SelectionReadGrant){
   const original=retained(catalog,action),issued=grants.get(grant);
   if(!issued||issued.action!==action||issued.cut!==original.cut)throw Error('Current separate issued selection-read grant required');
   return original;
  }
 });
}
