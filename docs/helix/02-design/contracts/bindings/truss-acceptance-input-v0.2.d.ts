/** Native source-reference input. Exact source bytes travel once in their source carrier. */
import type {AcceptanceInput as LegacyInput, AcceptanceDocument as LegacyDocument} from './truss-acceptance-input-v0.1';
export interface AcceptanceDocument extends Omit<LegacyDocument,'artifact'|'ingress'> {
  readonly artifact: {readonly identity:string; readonly sha256:string};
  readonly ingress: {readonly kind:'native'};
}
export interface AcceptanceInput extends Omit<LegacyInput,'interfaceVersion'|'documents'> {
  readonly interfaceVersion:'truss-acceptance-input/0.2.0';
  readonly documents: readonly [AcceptanceDocument,...AcceptanceDocument[]];
}
