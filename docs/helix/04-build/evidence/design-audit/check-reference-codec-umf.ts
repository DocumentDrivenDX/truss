import {schemaCoefficient} from '/Users/erik/Projects/umf/src/model/schema-literals.ts';
const valid: [string,string][]=[['9007199254740993.000','9007199254740993000'],['0.00','0'],['-0.01','-10'],['1e2','100000'],['100.00','100000'],['1.2300','1230'],['-0.000','0']];
for(const [token, expected] of valid) if(schemaCoefficient(token,3,21).toString()!==expected) throw Error(token);
const invalid=['+1','01','.1','1.','NaN','Infinity','1e','1\n','1e-4','1e18'];
for(const token of invalid){let refused=false;try{schemaCoefficient(token,3,21)}catch{refused=true}if(!refused)throw Error('unexpected admission: '+token)}
console.log(JSON.stringify({scope:'Existing UMF schemaCoefficient compatibility for proposed reference decimal vectors; no native, public-package, resource or compiler qualification',accepted:valid.map(([token,coefficient])=>({token,coefficient})),refused:invalid},null,2));
