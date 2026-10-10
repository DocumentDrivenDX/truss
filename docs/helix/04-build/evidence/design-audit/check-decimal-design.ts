/** Independent bounded rational oracle for authored design vectors; no production codec. */
type Tuple=readonly ['positive'|'negative'|'zero',string,string];
function rational(token:string):readonly [bigint,bigint] {
  // This oracle covers the declared JSON-number fixture subset only.
  const match=/^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(token);
  if(!match)throw Error('fixture grammar');
  const fraction=match[3]??'', exponent=BigInt(match[4]??'0')-BigInt(fraction.length);
  if(exponent < -1000n || exponent > 1000n)throw Error('bounded oracle domain');
  const digits=BigInt(match[2]+fraction)*(match[1]? -1n:1n);
  return exponent>=0n ? [digits*10n**exponent,1n] : [digits,10n**(-exponent)];
}
function tupleValue([sign,coefficient,exponent]:Tuple):readonly [bigint,bigint] {
  if(sign==='zero') {if(coefficient!=='0'||exponent!=='0')throw Error('noncanonical zero');return [0n,1n]}
  if(!/^[1-9](?:[0-9]*[1-9])?$/.test(coefficient)||! /^(?:0|-?[1-9][0-9]*)$/.test(exponent))throw Error('noncanonical tuple');
  return rational(`${sign==='negative'?'-':''}${coefficient}e${exponent}`);
}
const fixtures:readonly [string,Tuple][]=[
 ['1.00',['positive','1','0']],['100.00',['positive','1','2']],
 ['1e2',['positive','1','2']],['0.00120',['positive','12','-4']],
 ['1.20e-3',['positive','12','-4']],['-0.00',['zero','0','0']],
 ['0e100',['zero','0','0']],['-12.30',['negative','123','-1']],
 ['9007199254740993',['positive','9007199254740993','0']]
];
for(const [token,tuple] of fixtures) {
  const [a,b]=rational(token),[c,d]=tupleValue(tuple);
  if(a*d!==c*b)throw Error(`unequal design fixture: ${token}`);
}
const comparisons:readonly [string,string,-1|0|1][]=[
 ['2','10',-1],['-10','-2',-1],['-0.00','0e100',0],
 ['9007199254740992','9007199254740993',-1],['1e2','100.00',0],
 ['0.00120','1.20e-3',0],['-0.001','0',-1],['0','0.001',-1]
];
for(const [left,right,expected] of comparisons) {
 const [a,b]=rational(left),[c,d]=rational(right),delta=a*d-c*b;
 const actual=delta<0n?-1:delta>0n?1:0;
 if(actual!==expected)throw Error(`comparison fixture: ${left}, ${right}`);
}
console.log(JSON.stringify({scope:'Authored decimal design vectors checked with bounded exact rational oracle; no normalizer/comparator implementation, native domain, encoding or browser qualification',tupleCases:fixtures.length,comparisonCases:comparisons.length,fixtures,comparisons},null,2));
