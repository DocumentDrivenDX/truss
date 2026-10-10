import type {CommittedGroupResponse,GroupResponse,GroupSemanticResult} from './truss-group-result-v0.1';
declare const semantic:GroupSemanticResult;
declare const committed:CommittedGroupResponse;
const general:GroupResponse=committed;
const applied:CommittedGroupResponse={disposition:'applied',durability:'committed',semantic};
// @ts-expect-error Pending IDs/results cannot be network success.
const pending:CommittedGroupResponse={disposition:'applied',durability:'pending',semantic};
// @ts-expect-error Same-transaction replay does not establish committed network success.
const sameTransaction:CommittedGroupResponse={disposition:'replayed',durability:'pending',semantic,replay:{basis:'same_transaction',observationProfile:applied.semantic.layoutProfile,evidence:{identity:'x',sha256:'x',bytesBase64:'eA=='}}};
// @ts-expect-error Application semantic output cannot replace commit uncertainty.
const uncertain:CommittedGroupResponse={disposition:'commit_unknown',durability:'committed',semantic};
void general;void applied;void pending;void sameTransaction;void uncertain;
