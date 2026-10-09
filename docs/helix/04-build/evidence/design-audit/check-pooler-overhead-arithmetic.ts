/** Independent synthetic witnesses for the proposed mean rule; no native timings. */
type Pair={object:string;preparedNs:string;unpreparedNs:string;preparedValue:string;unpreparedValue:string};
type Repetition={unit:string;preparedProfile:string;unpreparedProfile:string;pairs:Pair[]};
const expected=Array.from({length:1000},(_,i)=>({object:'object-'+i,value:'value-'+i}));
const unsigned=/^(0|[1-9][0-9]*)$/;
function assess(repetitions:Repetition[]):'pass'|'over_bound'|'invalid'{
 if(repetitions.length!==3)return 'invalid';
 let over=false;
 for(const repetition of repetitions){
  if(repetition.unit!=='ns'||repetition.preparedProfile!=='prepared-fixture'||repetition.unpreparedProfile!=='unprepared-fixture'||repetition.pairs.length!==1000)return 'invalid';
  const seen=new Set<string>();let delta=0n;
  for(let i=0;i<1000;i++){
   const pair=repetition.pairs[i],wanted=expected[i];
   if(seen.has(pair.object)||pair.object!==wanted.object||pair.preparedValue!==wanted.value||pair.unpreparedValue!==wanted.value)return 'invalid';
   seen.add(pair.object);
   if(!unsigned.test(pair.preparedNs)||!unsigned.test(pair.unpreparedNs))return 'invalid';
   delta+=BigInt(pair.unpreparedNs)-BigInt(pair.preparedNs);
  }
  if(delta>50000000n)over=true;
 }
 return over?'over_bound':'pass';
}
function fixture():Repetition[]{return Array.from({length:3},()=>({unit:'ns',preparedProfile:'prepared-fixture',unpreparedProfile:'unprepared-fixture',pairs:expected.map(x=>({object:x.object,preparedNs:'100',unpreparedNs:'50100',preparedValue:x.value,unpreparedValue:x.value}))}));}
let count=0;
function witness(name:string,wanted:ReturnType<typeof assess>,change:(x:Repetition[])=>void){const x=fixture();change(x);if(assess(x)!==wanted)throw Error(name);count++;}
witness('exact 50000000 ns sum passes','pass',()=>{});
witness('one ns over sum refuses','over_bound',x=>x[0].pairs[999].unpreparedNs='50101');
witness('negative deltas remain negative','pass',x=>{for(const r of x)for(const p of r.pairs)p.unpreparedNs='99';});
witness('missing sample refuses','invalid',x=>{x[0].pairs.pop();});
witness('wrong independently expected value refuses','invalid',x=>{x[0].pairs[0].preparedValue='wrong';x[0].pairs[0].unpreparedValue='wrong';});
witness('duplicate pair identity refuses','invalid',x=>x[0].pairs[1].object='object-0');
witness('changed mode profile refuses','invalid',x=>x[0].unpreparedProfile='prepared-fixture');
witness('wrong units refuse','invalid',x=>x[0].unit='ms');
witness('favorable combined mean cannot hide failed repetition','over_bound',x=>{for(const p of x[0].pairs)p.unpreparedNs='50101';for(const p of x[1].pairs)p.unpreparedNs='0';});
witness('unsafe-number durations stay exact','over_bound',x=>{x[0].pairs[0].preparedNs='9007199254740992';x[0].pairs[0].unpreparedNs='9007199254740993';x[0].pairs[1].unpreparedNs='100100';});
witness('fractional duration refuses','invalid',x=>x[0].pairs[0].preparedNs='0.1');
witness('missing repetition refuses','invalid',x=>{x.pop();});
console.log(count+' synthetic proposed-mean controls passed. No statistic adoption, native timing, mode execution or resource qualification.');
