---
ddx:
  id: TD-031
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-031
      kind: informed_by
    - id: SD-008
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-031: Transaction-local role grants

**Story:** [[US-031]]. **Parent:** [[SD-008]]. **Feature:** FEAT-008.

## Technical Approach

Host establishes an authorized transaction-local database role; Truss executes through that context and captures trusted acting-role identity in the journal. The connecting principal has no direct/inherited write authority in the qualified profile. Role selection is database-authorized, not a caller-origin string. End-of-transaction reset must be proven on the actual adapter/pooler profile.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/adapter-bun/src/context.ts`, `packages/adapter-pg/src/context.ts` | Host-supplied role/context integration without session leakage | US-031-AC2, US-031-AC3 |
| `packages/postgresql/src/journal/origin.ts` | Trusted role observation, including qualified definer path | US-031-AC2 |
| `tests/host/roles.test.ts` | Native grant/refusal/reset matrix | US-031-AC1, US-031-AC2, US-031-AC3 |

New runtime adapter components reuse CONTRACT-007 rather than own caller transaction lifetime.

## API/Interface Design

CONTRACT-007 owns executor/transaction context; CONTRACT-002 owns trusted db_role; CONTRACT-005 owns optional module-role semantics. Host administrative grant setup and exact role-capture mechanism must be specified in shared contracts. No user-supplied executable SQL or role identifier interpolation is allowed.

## Data Model and Integration

No canonical DDL. Grants/role membership are explicit deployment profile. Verify connecting identity cannot inherit/directly write, allowed role can write and journal role is database-derived. Caller-owned transaction may already have an authorized role: adopting it must not silently broaden or reset host policy. Context lifetime differs from per-call origin restoration and must be explicit.

## Security and Performance

Host authenticates principal and chooses permitted role; database rejects unheld roles. Definer functions require trusted acting-role propagation and fixed search path, never owner masquerading as actor. Pool reuse tests prove no role leakage. Qualify native version-specific grant behavior instead of assuming identical membership syntax/semantics across targets. Context setup cost is measured separately; never use session-global role for performance.

## Testing

STP-031 owns criteria. Use powerless connector, allowed writer, unauthorized role and two sequential transactions on the same physical connection. Include rollback/cancellation, definer call and actual transaction-mode pooler only when advertised. Driver mocks cannot qualify server role reset.

## Migration and Rollback

Role/grant changes are host-admin migrations, not automatic library startup. Revoking a profile withdraws support/evidence and may block new calls. Failed calls preserve host transaction semantics; transaction-local role resets when the transaction ends. Reverting to broader inherited privileges is not a safe security rollback.

## Implementation Sequence

1. Define exact trusted role/deployment profile and caller adoption obligations.
2. Create red native powerless/assume/reset tests.
3. Implement adapter context integration and trusted journal capture.
4. Qualify each adapter/server and advertised pooler separately.

## Risks and Gates

Trusted acting-role capture and caller transaction context authority remain shared gates. Ordinary writer cannot forge role by setting origin data. A direct connection pass does not qualify transaction-mode pooling. Native membership behavior and definer execution need actual evidence.
