/** Synthetic exact-byte capacity witnesses; not production canonical measurement or native import. */
type Row={kind:'object'|'edge';bytes:string};
function partition(rows:Row[],count:string,bytes:string):number[][]|null{
 const maxCount=BigInt(count),maxBytes=BigInt(bytes);if(maxCount<=0n||maxBytes<=0n)return null;
 const order=[...rows.flatMap((r,i)=>r.kind==='object'?[i]:[]),...rows.flatMap((r,i)=>r.kind==='edge'?[i]:[])];
 const result:number[][]=[];let current:number[]=[];let used=0n;
 for(const i of order){const size=BigInt(rows[i].bytes);if(size<0n||size>maxBytes)return null;
  if(BigInt(current.length)>=maxCount||used+size>maxBytes){result.push(current);current=[];used=0n;}
  current.push(i);used+=size;
 }
 if(current.length)result.push(current);return result;
}
const o=(bytes:string):Row=>({kind:'object',bytes}),e=(bytes:string):Row=>({kind:'edge',bytes});
const cases:[string,Row[],string,string,number[][]|null][]=[
 ['empty',[],'2','10',[]],
 ['global phase order',[e('2'),o('2'),e('2'),o('2')],'2','10',[[1,3],[0,2]]],
 ['inclusive bytes',[o('4'),o('6'),o('1')],'10','10',[[0,1],[2]]],
 ['inclusive count',[o('1'),o('1'),o('1')],'2','100',[[0,1],[2]]],
 ['no later small-record packing',[o('6'),o('6'),o('4')],'10','10',[[0],[1,2]]],
 ['single overflow refuses entire partition',[o('1'),o('11')],'10','10',null],
 ['chunk may cross phase boundary',[e('2'),o('2'),e('2')],'2','10',[[1,0],[2]]]
];
const failures=cases.filter(([,r,c,b,want])=>!Bun.deepEquals(partition(r,c,b),want)).map(([n])=>n);
console.log(JSON.stringify({scope:'synthetic original-index phase/count/byte partition only',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
