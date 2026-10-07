import type {PhysicalJobTooling,PendingIndexAdmission,CommittedIndexAdmission} from './truss-physical-job-tooling-v0.1';
declare const tooling:PhysicalJobTooling;declare const pending:PendingIndexAdmission;declare const committed:CommittedIndexAdmission;
// @ts-expect-error Pending queue admission cannot start native DDL.
void tooling.runIndexAttempt(pending);
// @ts-expect-error Index admission cannot invoke statistics execution.
void tooling.runStatisticsAttempt(committed);
// @ts-expect-error Serialized evidence cannot mint original committed custody.
const forged:CommittedIndexAdmission={durability:'committed',attempt:committed.attempt,observation:committed.observation};
void forged;
import type {PhysicalJobServiceConfiguration,PhysicalJobServiceRegistration} from './truss-physical-job-tooling-v0.1';
declare const config:PhysicalJobServiceConfiguration;
// @ts-expect-error Serialized configuration cannot mint original service custody.
const fakeService:PhysicalJobServiceRegistration={configuration:config};
// @ts-expect-error Group selection cannot register physical job service.
const wrongFamily:PhysicalJobServiceConfiguration={...config,selection:{...config.selection,family:'group'}};
void fakeService;void wrongFamily;
