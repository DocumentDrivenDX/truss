import type {HistoricalSourceResult, HistoricalSourceRequest} from './truss-historical-source-v0.1';
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const request: HistoricalSourceRequest={interfaceVersion:'truss-historical-source/0.1.0',sourceEpoch:'fixture',sourceProfile:pin,identity:{id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'d',moduleId:'m'}}};
const hidden: HistoricalSourceResult={outcome:'not_found'};
// @ts-expect-error Hidden identity cannot return its request context.
const disclosed: HistoricalSourceResult={outcome:'not_found',request};
// @ts-expect-error Proved absence requires creation/ownership/current-authority evidence.
const unproved: HistoricalSourceResult={outcome:'absent',request};
// @ts-expect-error Found cannot return a fabricated null source fact.
const empty: HistoricalSourceResult={outcome:'found',request,fact:null};
void [hidden,disclosed,unproved,empty];
