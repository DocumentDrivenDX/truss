/** CONTRACT-004/011 draft observation; not a native enforcement certificate. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
export type PolicyPrincipal = {readonly kind: 'public'} | {readonly kind: 'role'; readonly name: string};
export interface QualifiedRelation {readonly schema: string; readonly name: string;}
export interface QualifiedRoutine {
  readonly schema: string;
  readonly name: string;
  /** Native identity arguments, never name-only overload matching. */
  readonly identityArguments: string;
}
export interface EffectiveRole {
  readonly name: string;
  readonly superuser: boolean;
  readonly bypassRls: boolean;
  readonly inherit: boolean;
  readonly canLogin: boolean;
  readonly memberships: readonly {
    readonly role: string;
    /** Exact resolved grantor identity; distinct grants must remain distinct. */
    readonly grantor: string;
    readonly inheritOption: boolean;
    readonly setOption: boolean;
    readonly adminOption: boolean;
  }[];
}
export type RelationPrivilegeScope = {
  readonly column: {readonly kind: 'relation'};
  readonly privilege: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'TRUNCATE' | 'REFERENCES' | 'TRIGGER' | 'MAINTAIN';
} | {
  readonly column: {readonly kind: 'column'; readonly name: string};
  readonly privilege: 'SELECT' | 'INSERT' | 'UPDATE' | 'REFERENCES';
};
export type RelationGrant = RelationPrivilegeScope & {
  readonly grantor: string;
  readonly grantee: PolicyPrincipal;
  readonly grantOption: boolean;
};
export type RelationEffectivePrivilege = RelationPrivilegeScope & {
  readonly role: string;
  readonly grantOption: boolean;
};
export interface SequencePolicyInventory {
  readonly relation: QualifiedRelation;
  readonly owner: string;
  readonly grants: readonly {
    readonly grantor: string;
    readonly grantee: PolicyPrincipal;
    readonly privilege: 'USAGE' | 'SELECT' | 'UPDATE';
    readonly grantOption: boolean;
  }[];
  readonly effectivePrivileges: readonly {
    readonly role: string;
    readonly privilege: 'USAGE' | 'SELECT' | 'UPDATE';
    readonly grantOption: boolean;
  }[];
}
export type RowSecurityPolicyInventory = {
  readonly name: string;
  /** Complete admitted resolved definition; deparsed strings are separate observations. */
  readonly definition: ExactArtifact;
  readonly permissive: boolean;
  readonly roles: readonly PolicyPrincipal[];
} & ({
  readonly command: 'SELECT' | 'DELETE';
  readonly usingExpression: string | null;
  readonly checkExpression: null;
} | {
  readonly command: 'INSERT';
  readonly usingExpression: null;
  readonly checkExpression: string | null;
} | {
  readonly command: 'ALL' | 'UPDATE';
  readonly usingExpression: string | null;
  readonly checkExpression: string | null;
});
export interface RelationPolicyInventory {
  readonly relation: QualifiedRelation;
  readonly owner: string;
  readonly relationKind: string;
  readonly parentRelations: readonly QualifiedRelation[];
  readonly rowSecurity: boolean;
  readonly forceRowSecurity: boolean;
  readonly grants: readonly RelationGrant[];
  /** Resolved effective rights include PUBLIC, inherited and SET ROLE paths. */
  readonly effectivePrivileges: readonly RelationEffectivePrivilege[];
  readonly policies: readonly RowSecurityPolicyInventory[];
  readonly triggers: readonly {
    readonly name: string;
    readonly enabledMode: string;
    readonly internal: boolean;
    readonly routine: QualifiedRoutine;
    readonly definitionSql: string;
    readonly definition: ExactArtifact;
  }[];
  readonly constraints: readonly {readonly name: string; readonly definitionSql: string; readonly definition: ExactArtifact; readonly validated: boolean}[];
}
export interface RoutinePolicyInventory {
  readonly routine: QualifiedRoutine;
  readonly owner: string;
  readonly securityDefiner: boolean;
  readonly language: string;
  readonly definition: ExactArtifact;
  /** Include all proconfig settings; missing search_path is meaningful. */
  readonly settings: readonly {readonly name: string; readonly value: string}[];
  /** Explicit/default-expanded ACL facts; independent of effective execution. */
  readonly grants: readonly {
    readonly grantor: string;
    readonly grantee: PolicyPrincipal;
    readonly privilege: 'EXECUTE';
    readonly grantOption: boolean;
  }[];
  readonly executableBy: readonly string[];
}
/** Resolved namespace meaning; raw native OIDs/ACL representation stay in extraction. */
export interface NamespacePolicyInventory {
  readonly schema: string;
  readonly owner: string;
  readonly grants: readonly {
    readonly grantor: string;
    readonly grantee: PolicyPrincipal;
    readonly privilege: 'CREATE' | 'USAGE';
    readonly grantOption: boolean;
  }[];
  /** Evaluated for every admitted actual role/path, independently of ACL rows. */
  readonly effectivePrivileges: readonly {
    readonly role: string;
    readonly privilege: 'CREATE' | 'USAGE';
    readonly grantOption: boolean;
  }[];
}
/** Reached type/domain or language grant provenance, distinct from routine EXECUTE. */
export interface UsagePolicyFacts {
 readonly owner:string;
 readonly grants:readonly {readonly grantor:string;readonly grantee:PolicyPrincipal;readonly privilege:'USAGE';readonly grantOption:boolean}[];
 readonly effectivePrivileges:readonly {readonly role:string;readonly privilege:'USAGE';readonly grantOption:boolean}[];
}
export interface TypePolicyInventory extends UsagePolicyFacts {
 readonly type:{readonly schema:string;readonly name:string};
}
export interface LanguagePolicyInventory extends UsagePolicyFacts {
 readonly language:string;
 readonly trusted:boolean;
}
export interface InstalledPolicyInventory {
  readonly interfaceVersion: 'truss-installed-policy/0.1.0';
  readonly inventoryProfile: ProfilePin;
  readonly layoutProfile: ProfilePin;
  readonly target: {readonly databaseIdentity: string; readonly schema: string; readonly serverVersion: string};
  readonly writer: {readonly sessionRole: string; readonly currentRole: string};
  readonly observer: {readonly sessionRole: string; readonly currentRole: string};
  readonly roles: readonly EffectiveRole[];
  /** Deployment schema plus complete reached definition/lookup namespace closure. */
  readonly namespaces: readonly [NamespacePolicyInventory, ...NamespacePolicyInventory[]];
  readonly relations: readonly RelationPolicyInventory[];
  readonly routines: readonly RoutinePolicyInventory[];
  readonly sequences: readonly SequencePolicyInventory[];
 readonly types:readonly TypePolicyInventory[];
 readonly languages:readonly LanguagePolicyInventory[];
  /** Schema CREATE/ownership, guard alteration, SET ROLE/replication paths. */
  readonly administrativeCapabilities: readonly {
    readonly role: string;
    readonly capability: string;
    readonly permitted: boolean;
    readonly evidence: ExactArtifact;
  }[];
  readonly extraction: {readonly procedure: ExactArtifact; readonly rawObservations: readonly [ExactArtifact, ...ExactArtifact[]]};
}
export type InstalledPolicyObservation = {
  readonly state: 'match'; readonly observedAt: string;
  readonly inventorySha256: string; readonly qualifiedInventorySha256: string;
  readonly contextEvidenceSha256: string;
} | {
  readonly state: 'drift'; readonly observedAt: string;
  readonly inventorySha256: string; readonly qualifiedInventorySha256: string;
  readonly differences: readonly [string, ...string[]];
} | {
  readonly state: 'unavailable'; readonly observedAt: string;
  readonly reason: 'permission' | 'incomplete_scope' | 'unsupported_profile' | 'unstable_observation';
};
