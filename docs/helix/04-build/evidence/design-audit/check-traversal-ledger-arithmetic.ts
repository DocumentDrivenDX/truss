/** Independent mathematical witnesses for ledger rules, not host-store/native implementation. */
const zero={examinedEdges:'0',pathStates:'0',activeWorkMilliseconds:'0'};
const initial={...zero,pathStates:'1'};
const reserved={id:'permit',state:'reserved',maximum:{examinedEdges:'10',pathStates:'10',activeWorkMilliseconds:'100'}};
const settled={...reserved,state:'settled',actual:{examinedEdges:'8',pathStates:'6',activeWorkMilliseconds:'80'}};
const base={initial,actual:initial,outstanding:reserved.maximum,permits:[reserved]};
const done={...base,actual:{examinedEdges:'8',pathStates:'7',activeWorkMilliseconds:'80'},outstanding:zero,permits:[settled]};
const cases:[string,any,boolean][]=[
 ['original reserve',base,true],['actual settlement',done,true],
 ['initial state cannot disappear',{...done,actual:{...done.actual,pathStates:'6'}},false],
 ['outstanding cannot be refunded on reply loss',{...base,outstanding:zero},false],
 ['same permit cannot settle twice',{...done,permits:[settled,settled],actual:{examinedEdges:'16',pathStates:'13',activeWorkMilliseconds:'160'}},false],
 ['actual above maximum',{...done,permits:[{...settled,actual:{...settled.actual,examinedEdges:'11'}}],actual:{...done.actual,examinedEdges:'11'}},false],
 ['new work after failed checkpoint still counts',{...done,actual:{examinedEdges:'10',pathStates:'9',activeWorkMilliseconds:'100'},permits:[settled,{...settled,id:'retry',maximum:{examinedEdges:'2',pathStates:'2',activeWorkMilliseconds:'20'},actual:{examinedEdges:'2',pathStates:'2',activeWorkMilliseconds:'20'}}]},true]
];
function consistent(v:any):boolean{
 const keys=Object.keys(zero);const actual:any={};const outstanding:any={};const ids=new Set();
 for(const k of keys){actual[k]=BigInt(v.initial[k]);outstanding[k]=0n;}
 for(const p of v.permits){if(ids.has(p.id))return false;ids.add(p.id);
  for(const k of keys){const maximum=BigInt(p.maximum[k]);if(maximum<0n)return false;
   if(p.state==='reserved')outstanding[k]+=maximum;
   else{const used=BigInt(p.actual[k]);if(used<0n||used>maximum)return false;actual[k]+=used;}
  }
 }
 return keys.every(k=>actual[k]===BigInt(v.actual[k])&&outstanding[k]===BigInt(v.outstanding[k]));
}
const failures=cases.filter(([,v,e])=>consistent(v)!==e).map(([n])=>n);
console.log(JSON.stringify({scope:'independent exact-integer ledger arithmetic only; no issuer/physical/native evidence',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
