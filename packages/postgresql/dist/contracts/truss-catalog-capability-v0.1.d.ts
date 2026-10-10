/** CONTRACT-003/007 draft bound catalog facade; no runtime implementation. */
import type {AcceptanceInput, AcceptanceAttemptContext} from './truss-acceptance-input-v0.1';
import type {AcceptanceReport, AcceptanceSemanticResult} from './truss-acceptance-report-v0.1';
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
export interface AcceptanceReportRequest {
  readonly interfaceVersion:'truss-acceptance-report-request/0.1.0';
  readonly revision:string;
}
export type AcceptanceReportResult = {
  readonly outcome:'available'; readonly report:AcceptanceReport;
} | {
  readonly outcome:'not_found'; readonly report?:never;
} | {
  readonly outcome:'unavailable';
  readonly reason:'profile' | 'context' | 'retention' | 'observation';
  readonly report?:never;
};
export interface CatalogCapability {
  readonly selection:CapabilitySelection & {readonly family:'catalog'};
  /** Produces no committed claim; caller/outer executor owns transaction outcome. */
  acceptInTransaction(transaction:TransactionHandle,input:AcceptanceInput,
    assertedOrigin:AcceptanceAttemptContext['assertedOrigin']):Promise<Outcome<AcceptanceSemanticResult>>;
  report(transaction:TransactionHandle,request:AcceptanceReportRequest):Promise<Outcome<AcceptanceReportResult>>;
}
export type CatalogCapabilityResult = {
  readonly status:'ok'; readonly capability:CatalogCapability;
} | {
  readonly status:'unavailable'; readonly reason:'selection' | 'disposed';
};
