# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private bounded action registration; no native authority or execution issuer.

The trusted host supplies the original owner preparation port. Byte comparison
is custody, not semantic qualification of that port or native Truss dependencies.
"""
from dataclasses import dataclass
import hashlib
import inspect
from threading import Lock
from truss.weft import _decode, CompileRefusal
from truss._bulk_set_values import check_set_literal, SetValueRefusal
from truss._action_identity_codec import encode_action_family, encode_action_role


class GatewayRefusal(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RegisteredAction:
    model: bytes
    action_pin: bytes
    preparation: bytes


@dataclass(frozen=True, slots=True)
class RegisteredActionPolicy:
    family_identity: bytes
    action_pin: bytes
    roles: tuple[str, ...]
    person_required: bool


@dataclass(frozen=True, slots=True, eq=False)
class _ActionTicket:
    pass


def _artifact(original):
    try:
        _, value = _decode(original, 4194304, 'owner_artifact')
        if type(value) is not dict or set(value) != {'mediaType', 'utf8', 'sha256'}:
            raise GatewayRefusal('Exact original Artifact required')
        if value['mediaType'] != 'application/json' or type(value['utf8']) is not str:
            raise GatewayRefusal('Original JSON artifact required')
        body = value['utf8'].encode('utf-8', errors='strict')
        if len(body) > 1048576 or hashlib.sha256(body).hexdigest() != value['sha256']:
            raise GatewayRefusal('Original artifact digest differs')
        _decode(body, 1048576, 'owner_body')
        return value
    except (CompileRefusal, UnicodeError) as error:
        raise GatewayRefusal('Original bounded artifact refused') from error


class ActionRegistration:
    """Original model/action/preparation custody for a configured gateway.

    The port takes immutable original model Artifact/action-pin bytes and returns
    original owner preparation Artifact bytes. Missing/deferred ports refuse.
    This class grants no execution rights and exposes no invoke/connection API.
    """
    def __init__(self, prepare_owner, maximum=64):
        call = getattr(prepare_owner, '__call__', None)
        if (not callable(prepare_owner) or any(inspect.iscoroutinefunction(f) or
                inspect.isgeneratorfunction(f) or inspect.isasyncgenfunction(f)
                for f in (prepare_owner, call)) or type(maximum) is not int or not 1 <= maximum <= 64):
            raise GatewayRefusal('Synchronous original owner port and finite capacity required')
        self._prepare = prepare_owner
        self._maximum = maximum
        self._entries = {}
        self._busy = False
        self._lock = Lock()

    def register(self, model, action_pin, preparation):
        model_value = _artifact(model)
        _artifact(preparation)
        try:
            _, pin = _decode(action_pin, 1048576, 'action_pin')
        except CompileRefusal as error:
            raise GatewayRefusal('Original action pin refused') from error
        if type(pin) is not dict or pin.get('documentSha256') != model_value['sha256']:
            raise GatewayRefusal('Original action/model correspondence differs')
        with self._lock:
            if self._busy:
                raise GatewayRefusal('Owner registration already active')
            if len(self._entries) >= self._maximum:
                raise GatewayRefusal('Registration capacity exhausted')
            self._busy = True
        try:
            returned = self._prepare(model, action_pin)
            if inspect.isgenerator(returned) or inspect.iscoroutine(returned):
                returned.close()
                raise GatewayRefusal('Deferred owner preparation refused')
            if inspect.isawaitable(returned) or inspect.isasyncgen(returned):
                raise GatewayRefusal('Deferred owner preparation refused')
            if type(returned) is not bytes:
                raise GatewayRefusal('Original immutable owner preparation required')
            expected = _artifact(returned)
            supplied = _artifact(preparation)
            # Outer Artifact JSON formatting is transport; original payload bytes
            # and their media/digest remain exact owner correspondence.
            if supplied != expected:
                raise GatewayRefusal('Preparation differs from original owner output')
            registered = RegisteredAction(model, action_pin, preparation)
            with self._lock:
                handle = _ActionTicket()
                self._entries[handle] = registered
                return handle
        except GatewayRefusal:
            raise
        except Exception as error:
            raise GatewayRefusal('Original owner preparation refused') from None
        finally:
            with self._lock:
                self._busy = False

    def original(self, handle):
        with self._lock:
            if type(handle) is not _ActionTicket or handle not in self._entries:
                raise GatewayRefusal('Local registered action handle required')
            return self._entries[handle]

    def validate_values(self, ticket, original_values):
        """Validate all recipe value inputs against exact registered original Fields.

        Entity Key resolution, authority, frames and native transaction admission
        are not supplied by this result. Original value bytes are returned unchanged.
        """
        registered=self.original(ticket)
        try:
            _, values=_decode(original_values,1048576,'set_values')
            model=_artifact(registered.model)
            preparation=_artifact(registered.preparation)
            _, document=_decode(model['utf8'].encode(),1048576,'owner_model')
            _, prepared=_decode(preparation['utf8'].encode(),1048576,'owner_preparation')
            if prepared.get('protocol')!='umf.actions.plan-model/1' or prepared['model']['sha256']!=model['sha256']:
                raise GatewayRefusal('Original prepared set-action required')
            assignments=prepared['assignments']
            expected=[a['input'] for a in assignments]
            if type(values) is not dict or len(expected)!=len(set(expected)) or set(values)!=set(expected):
                raise GatewayRefusal('Complete exact set-value inputs required')
            for assignment in assignments:
                reference=assignment['field']
                selected=[e for module in document['modules'] if module['id']==reference['module'] for e in module['elements'] if e['id']==reference['element']]
                if len(selected)!=1:
                    raise GatewayRefusal('Exact original Field required')
                check_set_literal(selected[0],values[assignment['input']])
            return original_values
        except GatewayRefusal:
            raise
        except (CompileRefusal,SetValueRefusal,KeyError,TypeError,AttributeError,UnicodeError):
            raise GatewayRefusal('Original set-value admission refused') from None

    def family_policy(self, ticket):
        """Derive exact known role obligations from retained original source.

        This comparison is not current membership, authentication, replay
        discovery permission or native registry/operation admission.
        """
        original = self.original(ticket)
        try:
            model = _artifact(original.model)
            prepared = _artifact(original.preparation)
            _, pin = _decode(original.action_pin,1048576,'action_pin')
            _, document = _decode(model['utf8'].encode(),1048576,'owner_model')
            _, preparation = _decode(prepared['utf8'].encode(),1048576,'owner_preparation')
            if (preparation.get('protocol') != 'umf.actions.plan-model/1'
                    or preparation['action'] != pin
                    or preparation['model']['sha256'] != model['sha256']
                    or pin['documentSha256'] != model['sha256']):
                raise GatewayRefusal('Original action preparation correspondence required')
            identity = pin['identity']
            if type(identity) is not dict or set(identity) != {'module','action'}:
                raise GatewayRefusal('Original exact action identity required')
            family = encode_action_family(identity['module'],identity['action'])
            modules = [m for m in document['modules'] if m['id'] == identity['module']]
            if len(modules) != 1:
                raise GatewayRefusal('Unique original action module required')
            actions = [a for a in modules[0]['extensions']['umf.actions']['actions'] if a['id'] == identity['action']]
            if len(actions) != 1:
                raise GatewayRefusal('Unique original action declaration required')
            authorization = actions[0]['authorization']
            if (type(authorization) is not dict or set(authorization) != {'kind','profile','roles'}
                    or authorization['kind'] != 'roles'
                    or authorization['profile'] != {'id':'umf.actions.roles','version':'1'}):
                raise GatewayRefusal('Original known action roles profile required')
            roles = authorization['roles']
            if type(roles) is not list or not 1 <= len(roles) <= 64:
                raise GatewayRefusal('Bounded original action role obligations required')
            encoded = [encode_action_role(role) for role in roles]
            if len(set(encoded)) != len(encoded):
                raise GatewayRefusal('Distinct original action roles required')
            attribution = actions[0]['attribution']
            if attribution != {'subject':'person-required'}:
                raise GatewayRefusal('Original person-required profile required')
            return RegisteredActionPolicy(family, original.action_pin, tuple(roles), True)
        except GatewayRefusal:
            raise
        except (CompileRefusal,ValueError,KeyError,TypeError,AttributeError,UnicodeError):
            raise GatewayRefusal('Original registered action policy refused') from None
