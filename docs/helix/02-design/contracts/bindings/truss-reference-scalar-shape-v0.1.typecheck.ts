import type {ReferenceScalarShapeDefinition} from './truss-reference-scalar-shape-v0.1';
import type {ExactArtifact} from './truss-acceptance-input-v0.1';
declare const artifact:ExactArtifact;
declare const shape:ReferenceScalarShapeDefinition;
const string:ReferenceScalarShapeDefinition={...shape,scalarFamily:'string',nullRoot:'explicit-owned-null-root-no-children-no-payload'};
const decimal:ReferenceScalarShapeDefinition={...shape,scalarFamily:'decimal',nullRoot:'refuse'};
// @ts-expect-error Reference decimal shape cannot admit explicit null.
const decimalNull:ReferenceScalarShapeDefinition={...shape,scalarFamily:'decimal',nullRoot:'explicit-owned-null-root-no-children-no-payload'};
// @ts-expect-error Leaf cannot refer back to downstream presence.
const presenceCycle:ReferenceScalarShapeDefinition={...shape,presenceDefinition:artifact};
// @ts-expect-error Leaf cannot refer back to downstream codec.
const codecCycle:ReferenceScalarShapeDefinition={...shape,scalarCodecDefinition:artifact};
// @ts-expect-error Leaf cannot refer back to composite value.
const valueCycle:ReferenceScalarShapeDefinition={...shape,valueDefinition:artifact};
// @ts-expect-error Container is outside this scalar reference leaf.
const container:ReferenceScalarShapeDefinition={...shape,scalarRoot:'container'};
void string;void decimal;void decimalNull;void presenceCycle;void codecCycle;void valueCycle;void container;
