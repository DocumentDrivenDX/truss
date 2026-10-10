/** Wire shape only; source/namespace/identity invariants remain semantic admission. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts')) ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const validate=ajv.getSchema('urn:truss:draft:conformance-aliases:0.1.0')!;
const pin={identity:'original-profile',version:'0.1.0',sha256:'a'.repeat(64)};
const basis={identity:'original-case-basis',bytesBase64:'e30=',sha256:'b'.repeat(64)};
const namespace={identity:'objects',entityKind:'object',identityProfile:pin,originalBasis:basis};
const binding={symbol:'$a',namespaceIdentity:'objects',bind:{kind:'operation_result',operationIndex:'0',pointer:'/result/id'}};
const base={interfaceVersion:'truss-conformance-aliases/0.1.0',caseId:'independent-case',comparisonProfile:pin,identityPathGrammar:pin,namespaces:[namespace],aliases:[binding]};
const cases:[string,unknown,boolean][]=[
 ['operation binding',base,true],
 ['setup binding',{...base,aliases:[{...binding,bind:{kind:'setup',pointer:'/records/0/id'}}]},true],
 ['escaped pointer',{...base,aliases:[{...binding,bind:{...binding.bind,pointer:'/a~1b/~0id'}}]},true],
 ['empty inventory requires semantic proof',{...base,namespaces:[],aliases:[]},true],
 ['no runtime allocation literals',{...base,aliases:[{...binding,resolvedId:'123'}]},false],
 ['no numeric index',{...base,aliases:[{...binding,bind:{...binding.bind,operationIndex:0}}]},false],
 ['no noncanonical index',{...base,aliases:[{...binding,bind:{...binding.bind,operationIndex:'00'}}]},false],
 ['no invalid pointer escape',{...base,aliases:[{...binding,bind:{...binding.bind,pointer:'/a~2b'}}]},false],
 ['no executable loader',{...base,command:'load-host-code'},false],
 ['duplicate symbol requires semantic refusal',{...base,aliases:[binding,binding]},true],
 ['unknown namespace requires semantic refusal',{...base,aliases:[{...binding,namespaceIdentity:'foreign'}]},true],
 ['literal-value pointer requires grammar refusal',{...base,aliases:[{...binding,bind:{...binding.bind,pointer:'/result/props/text'}}]},true]
];
const failures=cases.filter(([,input,expected])=>Boolean(validate(input))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'typed corpus alias wire shape only; no grammar, injectivity, original source, native or interchange qualification',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);
export {};
