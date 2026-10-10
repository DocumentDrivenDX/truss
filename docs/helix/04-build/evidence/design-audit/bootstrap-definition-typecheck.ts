import type {BootstrapDefinitionAssembly, DefinitionFieldClassification} from '../../../02-design/contracts/bindings/truss-bootstrap-definition-v0.1.proposal';
import type {ExactArtifact} from '../../../02-design/contracts/bindings/truss-acceptance-input-v0.1';
type Complete = Extract<BootstrapDefinitionAssembly, {outcome:'complete'}>;
type Incomplete = Extract<BootstrapDefinitionAssembly, {outcome:'incomplete'}>;
declare const unsupported: Extract<DefinitionFieldClassification, {kind:'preserved_unsupported'}>;
declare const originalArtifact: ExactArtifact;
declare const stable: Extract<DefinitionFieldClassification, {kind:'stable'}>;
declare const operational: Extract<DefinitionFieldClassification, {kind:'operational_evidence'}>;
const admittedFieldKinds: Complete['fields'] = [stable, operational];
const retainedIncompleteFields: Incomplete['fields'] = [stable, operational, unsupported];
// @ts-expect-error Unsupported raw meaning cannot enter complete field classification.
const rejectedCompleteFields: Complete['fields'] = [unsupported];
// @ts-expect-error Incomplete result cannot carry a success definition artifact.
const rejectedIncompleteDefinition: Incomplete['interpretedDefinition'] = originalArtifact;
// @ts-expect-error Incomplete result cannot carry complete admission evidence.
const rejectedIncompleteAdmission: Incomplete['admissionEvidence'] = originalArtifact;
void [admittedFieldKinds, retainedIncompleteFields, rejectedCompleteFields,
 rejectedIncompleteDefinition, rejectedIncompleteAdmission];
