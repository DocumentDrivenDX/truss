"""Independent Fraction oracle for proposed number-to-decimal admission examples."""
from fractions import Fraction
from pathlib import Path
import json
cases=[('exact_half',12.5,3,1,True),('inexact_tenth',0.1,3,1,False),('exact_binary_tenth_wide_domain',0.1,55,55,True),('precision_overflow',12.5,2,1,False),('exact_negative',-12.5,3,1,True),('exact_eighth_insufficient_scale',0.125,3,2,False),('exact_eighth',0.125,3,3,True)]
results=[]
for name,value,precision,scale,expected in cases:
 original=Fraction.from_float(value)
 scaled=original*10**scale
 admitted=scaled.denominator==1 and len(str(abs(scaled.numerator)))<=precision
 if admitted!=expected:raise ValueError(name)
 results.append({'case':name,'precision':precision,'scale':scale,'binaryNumerator':str(original.numerator),'binaryDenominator':str(original.denominator),'expectedAdmitted':expected,'observedAdmitted':admitted})
receipt={'scope':'Independent Python Fraction oracle for seven finite binary64 domain examples; no TypeScript adapter, UMF validation, browser, storage or native qualification','cases':results,'nativeQualified':False}
Path(__file__).with_name('number-decimal-domain-examples.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'cases':len(results),'passed':True,'nativeQualified':False}))
