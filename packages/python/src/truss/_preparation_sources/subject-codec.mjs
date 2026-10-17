import {derivePreparationSubjectKey} from './producer.js';
const request=await Bun.stdin.json();
console.log(JSON.stringify(request.bindings.map(native=>({native,
 sourcePins:{subjectMapping:request.subjectMapping.sha256,coreClosure:request.coreClosure.sha256},
 original:derivePreparationSubjectKey(request.subjectMapping,request.coreClosure,native.principalHex)}))));
