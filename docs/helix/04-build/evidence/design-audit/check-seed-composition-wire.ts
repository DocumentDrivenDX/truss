/** Published composition bytes versus schema only; no authenticated/native evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const names=['acceptance-input','exact-value','history-record','import-report','seed-baseline-inventory','seed-snapshot-evidence','seed-baseline','seed-visibility'];
const schemas=new Map<string,any>();
for(const name of names){const schema=await Bun.file(`docs/helix/02-design/contracts/${name}-v0.1.schema.json`).json();ajv.addSchema(schema);schemas.set(name,schema);}
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/seed-composition-v0.1.vectors.json').json();
const mapping:{[key:string]:string}={snapshot:'seed-snapshot-evidence',baseline:'seed-baseline',visibility:'seed-visibility',inventory:'seed-baseline-inventory'};
const failures:string[]=[];
for(const vector of fixture.vectors){const validate=ajv.getSchema(schemas.get(mapping[vector.name]).$id)!;if(!validate(JSON.parse(vector.rawUtf8)))failures.push(vector.name+': '+JSON.stringify(validate.errors));}
const receipt={scope:'Four published composition payloads versus closed wire schemas only; no canonicalizer, completeness, authority, custody or native qualification',artifacts:fixture.vectors.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/seed-composition-wire.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
