/** Independent exact-integer design vectors, not native snapshot truth/admission implementation. */
const token=(s:string)=>/^(0|[1-9][0-9]*)$/.test(s)&&s.length<=20;
function consistent(xmin:string,xmax:string,inProgress:readonly string[]):boolean {
 if(![xmin,xmax,...inProgress].every(token))return false;
 const low=BigInt(xmin),high=BigInt(xmax);
 if(low>high)return false;
 let prior:bigint|null=null;
 for(const text of inProgress){const value=BigInt(text);if(value<low||value>=high||(prior!==null&&value<=prior))return false;prior=value;}
 return true;
}
const cases:[string,string,string,readonly string[],boolean][]=[
 ['ordinary','10','20',['10','14'],true],
 ['zero width empty','20','20',[],true],
 ['zero width member','20','20',['20'],false],
 ['reverse','20','10',[],false],
 ['below xmin','10','20',['9'],false],
 ['at xmax excluded','10','20',['20'],false],
 ['duplicate','10','20',['10','10'],false],
 ['unsorted','10','20',['14','10'],false],
 ['beyond safe integer','9007199254740993','9007199254740996',['9007199254740993','9007199254740995'],true],
 ['large adjacent excluded','9007199254740993','9007199254740994',['9007199254740994'],false],
 ['leading zero','010','20',[],false],
 ['negative','-1','20',[],false]
];
const failures=cases.filter(([,a,b,c,expected])=>consistent(a,b,c)!==expected).map(([name])=>name);
const receipt={scope:'Independent mathematical interval/order vectors only; no native xid range, classifier truth, authority/protection or adapter qualification',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/seed-snapshot-order.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
