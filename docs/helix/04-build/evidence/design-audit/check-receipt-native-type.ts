/** Synthetic metadata projection probe; no native SQL/exporter qualification. */
import {derivePostgresqlColumns} from '/Users/erik/Projects/umf/src/adapters/postgresql/column-metadata';
import {parseNativeJson,renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const names=['xid8','bytea','int8'];
const columns=names.map((name,i)=>({name:'column_'+i,nativeType:{schema:'pg_catalog',name,kind:'b',category:name==='int8'?'N':'U',dimensions:0,modifier:-1},retainedUnknown:{nativeMeaning:'original '+name}}));
const root=parseNativeJson(JSON.stringify({snapshot:{relations:[{schema:'truss',name:'request_receipt',kind:'r',columns}]}}));
const projected=derivePostgresqlColumns(root),failures:string[]=[];
if(projected.length!==3)failures.push('complete synthetic column count');
for(let i=0;i<columns.length;i++)if(!Bun.deepEquals(JSON.parse(renderTree(projected[i].nativeColumn)),columns[i]))failures.push('preserved complete original column '+i);
if(projected[0].element.scalarType!==undefined)failures.push('xid8 must not be guessed as core integer');
if(projected[1].element.scalarType!=='binary')failures.push('known bytea binary projection');
if(projected[2].element.scalarType!=='integer')failures.push('known int8 integer projection');
const receipt={scope:'Synthetic native-column projection only; xid8 original bytes retained without core family; no native SQL/DDL/exporter/full-layout support',cases:7,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/receipt-native-type.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
