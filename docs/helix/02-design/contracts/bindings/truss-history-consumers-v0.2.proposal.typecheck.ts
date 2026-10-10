import type {JournalPageResult} from './truss-journal-page-v0.1';
import type {RetainedHistoryArchive} from './truss-retained-history-archive-v0.1';
import type {AcceptanceReport} from './truss-acceptance-report-v0.1';
import type {ProposedJournalPageResult} from './truss-journal-page-v0.2.proposal';
import type {ProposedRetainedHistoryArchive} from './truss-retained-history-archive-v0.2.proposal';
import type {ProposedAcceptanceReport} from './truss-acceptance-report-v0.2.proposal';
import type {ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
declare const oldPage:Extract<JournalPageResult,{outcome:'page'}>;
declare const oldArchive:RetainedHistoryArchive;
declare const oldReport:AcceptanceReport;
declare const retain:Extract<ProposedHistoricalEvent,{operation:'retain'}>;
declare const rebind:Extract<ProposedHistoricalEvent,{operation:'rebind'}>;
const page:ProposedJournalPageResult={...oldPage,events:[retain,rebind]};
const archive:ProposedRetainedHistoryArchive={...oldArchive,interfaceVersion:'truss-retained-history-archive/0.2.0-proposal',events:[retain,rebind]};
const report:ProposedAcceptanceReport={...oldReport,interfaceVersion:'truss-acceptance-report/0.2.0-proposal',rebinds:[rebind]};
// @ts-expect-error Old event page needs explicit version/profile conversion.
const oldPageIntoNew:ProposedJournalPageResult=oldPage;
// @ts-expect-error New event page cannot enter old result consumers.
const newPageIntoOld:JournalPageResult=page;
// @ts-expect-error Archive versions remain distinct.
const oldArchiveIntoNew:ProposedRetainedHistoryArchive=oldArchive;
// @ts-expect-error Archive versions remain distinct.
const newArchiveIntoOld:RetainedHistoryArchive=archive;
// @ts-expect-error Report versions remain distinct.
const oldReportIntoNew:ProposedAcceptanceReport=oldReport;
// @ts-expect-error Report versions remain distinct.
const newReportIntoOld:AcceptanceReport=report;
// @ts-expect-error Report rebinds excludes retain siblings.
const retainInReport:ProposedAcceptanceReport={...report,rebinds:[retain]};
// @ts-expect-error Unavailable result never carries partial event rows.
const partialUnavailable:ProposedJournalPageResult={outcome:'unavailable',reason:'profile',events:[retain]};
const unavailable:ProposedJournalPageResult={outcome:'unavailable',reason:'profile'};
void [page,archive,report,oldPageIntoNew,newPageIntoOld,oldArchiveIntoNew,newArchiveIntoOld,oldReportIntoNew,newReportIntoOld,retainInReport,partialUnavailable,unavailable];
