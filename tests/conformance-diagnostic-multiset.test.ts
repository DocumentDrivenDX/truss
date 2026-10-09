import {test,expect} from 'bun:test';
import {equalAdmittedDiagnosticMultisets as equal,type AdmittedDiagnosticComparison as Entry} from '../packages/tooling/src/conformance-diagnostic-multiset';
const error:Entry={sourceIdentity:'original-document-A',diagnosticProfile:'original-umf-0.7-profile',classification:'upstream_validation',severity:'error',code:'STRUCTURE',path:''};
const warning:Entry={...error,severity:'warning',code:'UNKNOWN_EXTENSION',path:'/vocabularies/vendor~1future'};
test('order is informative while duplicate multiplicity remains normative',()=>{
 expect(equal([error,error,warning],[warning,error,error])).toBe(true);
 expect(equal([error,error,warning],[warning,warning,error])).toBe(false);
 expect(equal([error,error],[error])).toBe(false);
});
test('root and empty member paths remain different',()=>{
 expect(equal([error],[{...error,path:'/'}])).toBe(false);
});
test('equal paths cannot merge different sources, profiles or stages',()=>{
 for(const entry of [{...error,sourceIdentity:'original-document-B'},{...error,diagnosticProfile:'another-profile'},{...error,classification:'truss_admission'}])expect(equal([error],[entry])).toBe(false);
});
test('severity, code and escaped pointer content cannot be rewritten',()=>{
 for(const entry of [{...warning,severity:'error' as const},{...warning,code:'STRUCTURE'},{...warning,path:'/vocabularies/vendor/future'}])expect(equal([warning],[entry])).toBe(false);
});
