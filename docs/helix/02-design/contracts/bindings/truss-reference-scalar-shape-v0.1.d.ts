/** Draft reference PostgreSQL definition data; no callable or runtime registration. */
import type {ExactArtifact} from './truss-acceptance-input-v0.1';
export interface ReferenceFieldIdentity {
 readonly documentId:string;
 readonly revision:string;
 readonly module:string;
 readonly element:string;
}
type ReferenceScalarShapeBase = {
 readonly interfaceVersion:'truss-reference-scalar-shape/0.1.0';
 readonly fieldIdentity:ReferenceFieldIdentity;
 readonly scalarRoot:'one-original-owned-root-no-children-one-qualified-scalar-payload';
 readonly absence:'outside-value-shape-presence-admission';
 readonly scope:'original-account-item-four-scalar-fields-only';
 readonly acceptedDefinition:ExactArtifact;
 readonly authoredDefinition:ExactArtifact;
 readonly physicalDefinition:ExactArtifact;
 /** Downstream references are excluded from this leaf. */
 readonly presenceDefinition?:never;
 readonly scalarCodecDefinition?:never;
 readonly valueDefinition?:never;
};
/** Full original identity/artifact/root/physical correspondence is runtime admitted. */
export type ReferenceScalarShapeDefinition = ReferenceScalarShapeBase & (
 {readonly scalarFamily:'string';readonly nullRoot:'refuse'|'explicit-owned-null-root-no-children-no-payload'} |
 {readonly scalarFamily:'decimal';readonly nullRoot:'refuse'}
);
