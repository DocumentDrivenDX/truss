"""Declared migration metadata planning only; no installation or execution authority."""
from dataclasses import dataclass
import re
from typing import Literal
from ._acceptance_json import AcceptanceJsonError, decode_acceptance_json


@dataclass(frozen=True)
class LayoutPin:
    version: str
    bundleSha256: str
    inventorySha256: str


@dataclass(frozen=True)
class Artifact:
    identity: str
    sha256: str


@dataclass(frozen=True)
class Procedure:
    identity: str
    version: str
    sha256: str


@dataclass(frozen=True)
class MigrationStep:
    id: str
    from_version: str
    to_version: str
    recipe: Artifact
    procedure: Procedure
    transactional: bool


@dataclass(frozen=True)
class Refused:
    reason: str
    outcome: Literal['refused'] = 'refused'
    scope: Literal['declared_metadata_only'] = 'declared_metadata_only'


@dataclass(frozen=True)
class NoSteps:
    family: str
    source: LayoutPin
    target: LayoutPin
    outcome: Literal['no_steps'] = 'no_steps'
    scope: Literal['declared_metadata_only'] = 'declared_metadata_only'


@dataclass(frozen=True)
class Plan:
    family: str
    source: LayoutPin
    target: LayoutPin
    route: str
    direction: str
    steps: tuple[MigrationStep, ...]
    outcome: Literal['plan'] = 'plan'
    scope: Literal['declared_metadata_only'] = 'declared_metadata_only'


def _object(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('closed object required')
    return value


def _text(value):
    if type(value) is not str or not value or len(value) > 256 or '\0' in value:
        raise ValueError('bounded text required')
    if len(value.encode('utf-8', errors='strict')) > 256:
        raise ValueError('text byte bound')
    return value


def _sha(value):
    if type(value) is not str or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('exact hash required')
    return value


def _version(value):
    value = _text(value)
    if not re.fullmatch(r'(0|[1-9][0-9]{0,19})\.(0|[1-9][0-9]{0,19})\.(0|[1-9][0-9]{0,19})', value):
        raise ValueError('version required')
    return value


def _list(value, nonempty=True):
    if type(value) is not list or len(value) > 1024 or nonempty and not value:
        raise ValueError('bounded list required')
    return value


def _pin(value):
    value = _object(value, ('version', 'bundleSha256', 'inventorySha256'))
    return LayoutPin(_version(value['version']), _sha(value['bundleSha256']), _sha(value['inventorySha256']))


def _unique(values, key):
    result = {}
    for value in values:
        identity = key(value)
        if identity in result:
            raise ValueError('duplicate identity')
        result[identity] = value
    return result


def _step(value, layouts):
    value = _object(value, ('id', 'from', 'to', 'recipe', 'procedure', 'transactional'))
    source, target = _version(value['from']), _version(value['to'])
    if source == target or source not in layouts or target not in layouts or type(value['transactional']) is not bool:
        raise ValueError('invalid step')
    recipe = _object(value['recipe'], ('identity', 'sha256'))
    procedure = _object(value['procedure'], ('identity', 'version', 'sha256'))
    return MigrationStep(_text(value['id']), source, target,
                         Artifact(_text(recipe['identity']), _sha(recipe['sha256'])),
                         Procedure(_text(procedure['identity']), _text(procedure['version']), _sha(procedure['sha256'])),
                         value['transactional'])


def plan_layout_migration(manifest_bytes: bytes, observation_bytes: bytes, target_version: str) -> Plan | NoSteps | Refused:
    """Select an explicit route from closed original metadata; never submit SQL.

    Input bytes must be immutable. Callers retain original artifacts independently;
    these frozen decoded views cannot serve as administrative permits or receipts.
    """
    try:
        manifest = _object(decode_acceptance_json(manifest_bytes), ('interfaceVersion', 'family', 'layouts', 'steps', 'routes'))
        if manifest['interfaceVersion'] != 'truss-layout-migrations/0.1.0':
            return Refused('invalid_input')
        family = _text(manifest['family'])
        layouts = _unique(map(_pin, _list(manifest['layouts'])), lambda pin: pin.version)
        steps = _unique((_step(value, layouts) for value in _list(manifest['steps'], False)), lambda step: step.id)
        recipe_pins, procedure_pins = {}, {}
        for step in steps.values():
            for pins, key, digest in ((recipe_pins, step.recipe.identity, step.recipe.sha256),
                                     (procedure_pins, (step.procedure.identity, step.procedure.version), step.procedure.sha256)):
                if key in pins and pins[key] != digest:
                    raise ValueError('Contradictory original artifact pin')
                pins[key] = digest
        routes, route_ids = {}, set()
        for value in _list(manifest['routes'], False):
            value = _object(value, ('id', 'from', 'to', 'direction', 'steps'))
            source, target = _version(value['from']), _version(value['to'])
            direction = value['direction']
            if source not in layouts or target not in layouts or type(direction) is not str or direction not in ('upgrade', 'downgrade'):
                raise ValueError('invalid route')
            ids = [_text(item) for item in _list(value['steps'])]
            if len(set(ids)) != len(ids):
                raise ValueError('repeated step')
            ordered, at = [], source
            for identity in ids:
                step = steps.get(identity)
                if step is None or step.from_version != at:
                    raise ValueError('broken chain')
                left = tuple(map(int, step.from_version.split('.')))
                right = tuple(map(int, step.to_version.split('.')))
                if (left < right) != (direction == 'upgrade'):
                    raise ValueError('wrong direction')
                at = step.to_version
                ordered.append(step)
            route_id = _text(value['id'])
            pair = (source, target)
            if at != target or pair in routes or route_id in route_ids:
                raise ValueError('invalid or duplicate route')
            route_ids.add(route_id)
            routes[pair] = (route_id, direction, tuple(ordered))
        observation = _object(decode_acceptance_json(observation_bytes), ('interfaceVersion', 'family', 'layout'))
        if observation['interfaceVersion'] != 'truss-layout-observation/0.1.0':
            return Refused('invalid_input')
        if _text(observation['family']) != family:
            return Refused('family')
        source = _pin(observation['layout'])
        if layouts.get(source.version) != source:
            return Refused('source_pin')
        target = layouts.get(_version(target_version))
        if target is None:
            return Refused('target')
        if source.version == target.version:
            return NoSteps(family, source, target)
        route = routes.get((source.version, target.version))
        if route is None:
            return Refused('route')
        if any(not step.transactional for step in route[2]):
            return Refused('nontransactional_profile')
        return Plan(family, source, target, *route)
    except (AcceptanceJsonError, ValueError, UnicodeError):
        return Refused('invalid_input')
