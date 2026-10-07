import type {PhysicalOptimizationRequest,PhysicalOptimizationResult,PhysicalOptimizationTooling} from './truss-physical-optimization-v0.1';
declare const tooling:PhysicalOptimizationTooling;
declare const request:PhysicalOptimizationRequest;
declare const pending:Extract<PhysicalOptimizationResult,{readonly outcome:'pending'}>;
// @ts-expect-error Optional physical tooling never accepts arbitrary runnable SQL directly.
const sql:PhysicalOptimizationRequest={...request,sql:'create index arbitrary'};
// @ts-expect-error Supplied-scope DDL cannot claim committed durability.
const committed:PhysicalOptimizationResult={...pending,durability:'committed'};
// @ts-expect-error Catalog acceptance is not an optional physical operation kind.
const catalog:PhysicalOptimizationRequest={...request,kind:'accept_revision'};
void [tooling,sql,committed,catalog];

// @ts-expect-error A byte estimate cannot replace measured post-DDL native bytes.
const estimate:typeof pending.budgetObservation={...pending.budgetObservation,after:{indexCount:'1',estimatedBytes:'10',observation:pending.resultingInventory}};
// @ts-expect-error The scoped budget observation is not confirmed postcommit evidence.
const durable:typeof pending.budgetObservation={...pending.budgetObservation,scope:'committed'};
void [estimate,durable];
