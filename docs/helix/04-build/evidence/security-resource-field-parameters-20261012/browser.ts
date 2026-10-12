import {request} from '/private/tmp/truss-security-main-integration/tests/fixtures/security-resource-parameters';
import {lowerSecurityRowPredicate} from '/private/tmp/truss-security-main-integration/packages/postgresql/src/security-predicate';
const plain=request();const tagged:any=request();tagged.types[0].discriminator={column:'type_id',carrier:'int8',value:'42'};tagged.resourceDiscriminatorParameter=2;
(globalThis as any).results={plain:lowerSecurityRowPredicate(plain),tagged:lowerSecurityRowPredicate(tagged)};
