/** Structural inventory and retained source correspondence; no semantic adoption. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const path='docs/helix/02-design/models/truss-layout-core-structural-0.4.proposal.umf.json';
const core=await Bun.file(path).json();const provenance=core.extensions['truss.layout.native'];
const hash=(bytes:Uint8Array)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
for(const [source,expected] of [[provenance.sourceModel,provenance.sourceSha256],[provenance.structuralSource,provenance.structuralSourceSha256]])if(hash(new Uint8Array(await Bun.file(source).arrayBuffer()))!==expected)throw Error('Retained source hash mismatch: '+source);
const native=readDocument(await Bun.file(provenance.sourceModel).text(),'json');
const nodes=JSON.parse(renderTree(getPostgresqlNode(native,'/stmts')));
const at=(pointer:string)=>pointer.split('/').slice(1).reduce((value:any,key:string)=>value[key.replaceAll('~1','/').replaceAll('~0','~')],nodes);
const module=core.modules.find((m:any)=>m.id==='truss-layout');
const records=module.elements.filter((e:any)=>e.kind==='record'),fields=module.elements.filter((e:any)=>e.kind==='field');
const observed=await Bun.file('docs/helix/04-build/evidence/design-audit/source-epoch-layout-native.json').json();
if(observed.sources[provenance.sourceModel]!==provenance.sourceSha256)throw Error('Native inventory captured different original model');
if(records.length!==observed.inventory.tableCount||fields.length!==observed.inventory.columnCount)throw Error('Core/native inventory size mismatch');
for(const table of observed.inventory.tables){
 const record=records.find((r:any)=>r.id===table.name);if(!record)throw Error('Missing core record '+table.name);
 if(BigInt(record.members.length)!==BigInt(table.columns))throw Error('Core/native column count mismatch '+table.name);
 const seen=new Set<string>();for(const member of record.members){const field=fields.find((f:any)=>f.id===member.element);if(!field||member.module!==module.id||!field.id.startsWith(table.name+'.')||seen.has(field.id))throw Error('Missing/duplicate/foreign core column '+member.element);seen.add(field.id);}
}
for(const column of observed.inventory.epochColumns){
 const field=fields.find((f:any)=>f.id===column.relname+'.'+column.attname);if(!field)throw Error('Missing native epoch column');
 const retained=field.extensions['truss.layout.native'];const source=at(retained.sourcePointer);
 if(source.colname!==column.attname||JSON.stringify(source.typeName)!==JSON.stringify(retained.nativeType)||JSON.stringify(source.constraints??[])!==JSON.stringify(retained.constraints))throw Error('Original epoch column source mismatch');
 if((field.nullability==='required')!==column.attnotnull)throw Error('Epoch native/core nullability mismatch');
}
const relationships=module.relationships.filter((r:any)=>r.id.startsWith('epoch-fk-'));
if(relationships.length!==observed.inventory.epochForeignKeys.length)throw Error('Epoch relationship inventory mismatch');
for(const relationship of relationships){const source=at(relationship.nativeCorrespondence.sourcePointer);if(JSON.stringify(source)!==JSON.stringify(relationship.nativeCorrespondence.definition))throw Error('Original FK definition mismatch');
 const target=records.find((r:any)=>r.id===relationship.target[0].element);const key=target.keys.find((k:any)=>k.id===relationship.target[0].key);if(!key)throw Error('Original target key missing');
 const projected=relationship.fieldCorrespondence.map((f:any)=>[f.source.element,f.target.element]);const expected=source.fk_attrs.map((f:any,i:number)=>[relationship.source[0].element+'.'+f.String.sval,source.pktable.relname+'.'+source.pk_attrs[i].String.sval]);if(JSON.stringify(projected)!==JSON.stringify(expected))throw Error('FK column order/correspondence mismatch');if(JSON.stringify(key.fields.map((f:any)=>f.element))!==JSON.stringify(expected.map((pair:string[])=>pair[1])))throw Error('Target key fields differ from native FK');
}
await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-core-correspondence.json',JSON.stringify({modelPath:path,modelSha256:hash(new Uint8Array(await Bun.file(path).arrayBuffer())),records:records.length,fields:fields.length,epochColumns:observed.inventory.epochColumns.length,epochRelationships:relationships.length,checks:['Both retained source files match exact declared hashes','Core record/member inventory matches observed native table/column counts','Every epoch column matches original AST type/constraints and observed nullability','Every epoch FK resolves original AST, target key and ordered field correspondence'],scope:'Structural source/native count and epoch declaration correspondence only; full baseline semantics, installed authority and DDL equivalence remain unqualified'},null,2)+'\n');console.log('48 records / 454 fields and three epoch relationships correspond to retained source and observed inventory.');
