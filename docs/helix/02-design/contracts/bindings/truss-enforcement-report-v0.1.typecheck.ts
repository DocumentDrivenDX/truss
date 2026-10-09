import type {AssertionOwner} from './truss-enforcement-report-v0.1';
const documentOwner:AssertionOwner={scope:'document',documentId:'source'};
const moduleOwner:AssertionOwner={documentId:'source',moduleId:'module'};
// @ts-expect-error Document assertions cannot invent a module.
const fabricatedOwner:AssertionOwner={scope:'document',documentId:'source',moduleId:'module'};
// @ts-expect-error A bare document identity does not establish scope.
const ambiguousOwner:AssertionOwner={documentId:'source'};
void [documentOwner,moduleOwner,fabricatedOwner,ambiguousOwner];
