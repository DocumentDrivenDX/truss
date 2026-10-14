"""Fresh native Subject/action-role observations, never a permit.

Original source/DDL/role lifecycle, authenticated engine peer capture and complete
mapping cuts remain premises. Direct privileged collector is diagnostic/private;
there is no enrolled production SECURITY DEFINER admission surface here.
"""
from dataclasses import dataclass
from .bulk_action_gateway import ActionRegistration
from ._action_identity_codec import encode_action_role
from ._security_preparation_authority import _native_path, verify_preparation_peer_with_cursor
from ._security_catalog_subject_installation import _text_rows, verify_held_registered_role_catalog_cut_with_cursor


@dataclass(frozen=True, slots=True)
class ActionAuthorityObservation:
    principal_identity: bytes
    subject_kind: str
    role_match: bool
    human_enrolled: bool
    security_ready: bool = False


def observe_current_action_authority_with_cursor(cursor, *, original, registration, ticket, store_identity):
    """Requires both original mapping SHARE cuts before native role cuts."""
    if (type(registration) is not ActionRegistration or type(store_identity) is not bytes
            or not 1 <= len(store_identity) <= 4096):
        raise ValueError('Original action registry/store comparison required')
    policy = registration.family_policy(ticket)
    _native_path(cursor)
    verify_preparation_peer_with_cursor(cursor, original)
    verify_held_registered_role_catalog_cut_with_cursor(cursor)
    held = _text_rows(cursor, """SELECT c.relname::text FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='truss' AND c.relname IN ('action_subject_binding','action_role_binding')
        AND c.relkind='r' AND c.relpersistence='p' AND NOT c.relrowsecurity AND NOT c.relforcerowsecurity
        AND c.relowner=(SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton)
        AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid)
        AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.pid=pg_catalog.pg_backend_pid()
            AND l.relation=c.oid AND l.locktype='relation' AND l.mode='ShareLock' AND l.granted
            AND l.database=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()))
        ORDER BY c.relname""", limit=2)
    if held != [('action_role_binding',),('action_subject_binding',)]:
        raise ValueError('Original complete private mapping cuts required')
    subject = _text_rows(cursor, """SELECT pg_catalog.encode(b.principal_identity,'hex'),b.subject_kind::text
        FROM ONLY truss.action_subject_binding b
        JOIN pg_catalog.pg_roles r ON r.oid=b.role_oid
        JOIN truss.catalog_runtime_installation i ON i.installation_id=b.installation_id AND i.singleton
        WHERE b.role_oid=%s::oid AND b.authentication_profile='truss.local-scram/0.1'
        AND r.rolcanlogin AND NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb
        AND NOT r.rolreplication AND NOT r.rolbypassrls
        AND NOT pg_catalog.pg_has_role(r.oid,i.owner_oid,'MEMBER')""", (original.identity[1],), 1)
    if len(subject) != 1 or subject[0][1] not in ('human','service'):
        raise ValueError('Original current ordinary Subject association required')
    roles = _text_rows(cursor, """WITH RECURSIVE memberships(role_oid) AS (
        SELECT %s::oid UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m
        JOIN memberships p ON p.role_oid=m.member)
        SELECT pg_catalog.encode(b.role_identity,'hex'),pg_catalog.encode(b.original_action_pin,'hex'),
        EXISTS(SELECT 1 FROM memberships m WHERE m.role_oid=b.native_role_oid)::text
        FROM ONLY truss.action_role_binding b
        JOIN truss.catalog_runtime_installation i ON i.installation_id=b.installation_id AND i.singleton
        JOIN pg_catalog.pg_roles r ON r.oid=b.native_role_oid
        WHERE b.store_identity=%s AND b.family_identity=%s
        AND b.profile_id='umf.actions.roles' AND b.profile_version='1'
        AND NOT r.rolcanlogin AND NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb
        AND NOT r.rolreplication AND NOT r.rolbypassrls
        AND NOT pg_catalog.pg_has_role(r.oid,i.owner_oid,'MEMBER')
        ORDER BY b.role_identity""", (original.identity[1],store_identity,policy.family_identity), 64)
    expected = sorted(encode_action_role(role).hex() for role in policy.roles)
    if ([row[0] for row in roles] != expected
            or any(row[1] != policy.action_pin.hex() or row[2] not in ('true','false') for row in roles)):
        raise ValueError('Complete exact original current role mapping required')
    verify_preparation_peer_with_cursor(cursor, original)
    return ActionAuthorityObservation(bytes.fromhex(subject[0][0]),subject[0][1],
        any(row[2]=='true' for row in roles),subject[0][1]=='human')
