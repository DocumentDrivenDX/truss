"""Independent exhaustive finite-world oracle, no Z3 expression reuse."""
import itertools,json
from pathlib import Path
worlds=0;comparisons=0;positive=0
permutations=list(itertools.product([(0,1),(1,0)],repeat=4))
for mask in range(1<<14):
 bits=[bool(mask&(1<<i)) for i in range(14)];sa=[bits[0:2],bits[2:4]];ap=[bits[4:6],bits[6:8]];rp=[bits[8:10],bits[10:12]];active=bits[12:14]
 wanted={(s,r) for s in range(2) for r in range(2) if any(sa[s][a] and active[a] and ap[a][p] and rp[r][p] for a in range(2) for p in range(2))}
 positive+=bool(wanted)
 for sk,ak,pk,rk in permutations:
  native_sa=[[sa[sk[s]][ak[a]] for a in range(2)] for s in range(2)];native_ap=[[ap[ak[a]][pk[p]] for p in range(2)] for a in range(2)];native_rp=[[rp[rk[r]][pk[p]] for p in range(2)] for r in range(2)];native_active=[active[ak[a]] for a in range(2)]
  got={(sk[s],rk[r]) for s in range(2) for r in range(2) if any(native_sa[s][a] and native_active[a] and native_ap[a][p] and native_rp[r][p] for a in range(2) for p in range(2))}
  assert wanted==got;worlds+=1;comparisons+=4
Path(__file__).with_name('oracle.json').write_text(json.dumps({'booleanWorlds':1<<14,'keyPermutationCombinations':16,'mappedWorlds':worlds,'callerResourceComparisons':comparisons,'positiveBooleanWorlds':positive,'scope':'Same exact two-instance finite correspondence model; independent Python enumeration, not implementation refinement.'},indent=2)+'\n')
