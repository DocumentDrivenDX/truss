import type {ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
import type {JournalStartCaptureProposal,JournalOrderedTransitionProposal,JournalFinalPreparationProposal,JournalReservedPositionsProposal,JournalPendingPublicationProposal,OrderedDeltaPayloadProposal,PreparedSiblingPayloadProposal,PreparedEntityProposal,JournalExactBytesProposal} from './truss-journal-producer-v0.2.proposal';
declare const start:JournalStartCaptureProposal;
declare const delta:JournalOrderedTransitionProposal;
declare const final:JournalFinalPreparationProposal;
declare const reserved:JournalReservedPositionsProposal;
declare const pending:JournalPendingPublicationProposal;
declare const complete:ProposedHistoricalEvent;
declare const entity:PreparedEntityProposal;
declare const origin:JournalExactBytesProposal<'origin'>;
const payload:OrderedDeltaPayloadProposal={operation:'property',propertyId:'1',definitionPin:'definition',before:{present:false},after:{present:true,value:{kind:'null'}}};
const prepared:PreparedSiblingPayloadProposal=payload;
// @ts-expect-error Full event custody cannot enter pre-reservation payload.
const fullIntoPrepared:PreparedSiblingPayloadProposal=complete;
// @ts-expect-error Full event custody cannot enter ordered delta.
const fullIntoDelta:OrderedDeltaPayloadProposal=complete;
// @ts-expect-error Future seq is prohibited inside pre-reservation payload.
const futureSeq:OrderedDeltaPayloadProposal={...payload,seq:'41'};
// @ts-expect-error Changed entity needs nonempty sibling membership.
const changedEmpty:PreparedEntityProposal={...entity,changed:true,siblingOrdinals:[]};
// @ts-expect-error Unchanged entity cannot carry sibling membership.
const unchangedNonempty:PreparedEntityProposal={...entity,changed:false,siblingOrdinals:['0']};
// @ts-expect-error Origin carrier cannot substitute for event bytes.
const confused:JournalExactBytesProposal<'event'>=origin;
// @ts-expect-error Pending append evidence cannot become committed by a label.
const committed:JournalPendingPublicationProposal={...pending,durability:'committed'};
// @ts-expect-error Start capture cannot substitute for independent final preparation.
const startIntoFinal:JournalFinalPreparationProposal=start;
// @ts-expect-error Reservation is not pending publication evidence.
const reserveIntoPublish:JournalPendingPublicationProposal=reserved;
void [start,delta,final,reserved,pending,prepared,fullIntoPrepared,fullIntoDelta,futureSeq,changedEmpty,unchangedNonempty,confused,committed,startIntoFinal,reserveIntoPublish];
