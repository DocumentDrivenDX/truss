// Minimal exact JSON reader/writer: numbers stay as their source tokens (same tree shape as UMF's NativeJson,
// src/model/native-json.ts). Used for bulk loading, where UMF's YAML-backed parser is slower; the fidelity suite
// reads results back with UMF's parseNativeJson itself.
export type NJ={kind:'null'}|{kind:'boolean';value:boolean}|{kind:'string';value:string}|{kind:'number';value:string}|{kind:'array';items:NJ[]}|{kind:'object';members:Record<string,NJ>};
export function parseExact(text:string):NJ{
  let i=0;
  const ws=()=>{while(i<text.length&&(text[i]===' '||text[i]==='\n'||text[i]==='\r'||text[i]==='\t'))i++;};
  const val=():NJ=>{
    ws();const c=text[i];
    if(c==='{'){i++;const members:Record<string,NJ>=Object.create(null);ws();if(text[i]==='}'){i++;return {kind:'object',members};}
      for(;;){ws();const k=str();ws();if(text[i++]!==':')throw new Error('expected : at '+i);if(Object.hasOwn(members,k))throw new Error('duplicate key '+k);members[k]=val();ws();const d=text[i++];if(d==='}')break;if(d!==',')throw new Error('expected , at '+i);}
      return {kind:'object',members};}
    if(c==='['){i++;const items:NJ[]=[];ws();if(text[i]===']'){i++;return {kind:'array',items};}
      for(;;){items.push(val());ws();const d=text[i++];if(d===']')break;if(d!==',')throw new Error('expected , at '+i);}
      return {kind:'array',items};}
    if(c==='"')return {kind:'string',value:str()};
    if(text.startsWith('true',i)){i+=4;return {kind:'boolean',value:true};}
    if(text.startsWith('false',i)){i+=5;return {kind:'boolean',value:false};}
    if(text.startsWith('null',i)){i+=4;return {kind:'null'};}
    const m=/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(i,i+400));
    if(!m)throw new Error('bad token at '+i);i+=m[0].length;return {kind:'number',value:m[0]};
  };
  const str=():string=>{
    if(text[i]!=='"')throw new Error('expected string at '+i);
    let j=i+1;let esc=false;for(;j<text.length;j++){if(esc){esc=false;continue;}if(text[j]==='\\')esc=true;else if(text[j]==='"')break;}
    const s=JSON.parse(text.slice(i,j+1));i=j+1;return s;
  };
  const v=val();ws();if(i!==text.length)throw new Error('trailing data at '+i);return v;
}
export function render(n:NJ):string{
  switch(n.kind){case 'null':return 'null';case 'number':return n.value;case 'boolean':return String(n.value);case 'string':return JSON.stringify(n.value);
    case 'array':return '['+n.items.map(render).join(',')+']';case 'object':return '{'+Object.entries(n.members).map(([k,v])=>JSON.stringify(k)+':'+render(v)).join(',')+'}';}
}
export const S=(value:string):NJ=>({kind:'string',value});
export const N=(value:string|number|bigint):NJ=>({kind:'number',value:String(value)});
