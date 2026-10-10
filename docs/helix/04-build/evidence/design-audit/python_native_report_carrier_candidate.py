"""Private numeric-free carrier codec; no native admission or publication authority."""
from dataclasses import dataclass
import json
from python_raw_json_candidate import JsonObject, RetainedJson


@dataclass(frozen=True)
class NativeReportCarrier:
    original: RetainedJson
    native_tree_text: str
    native_task_count: str
    scope: str = 'complete_report_wire_native_carrier_only'


def prepare_carrier(original: RetainedJson) -> NativeReportCarrier:
    # Exact compact ASCII length and native task count before tagged construction.
    pending = [original.value]
    steps = size = 0
    while pending:
        value = pending.pop()
        steps += 1
        if value is None:
            size += len('{"kind":"null"}')
        elif type(value) is bool:
            size += len('{"kind":"boolean","value":true}') + (0 if value else 1)
        elif type(value) is str:
            size += len('{"kind":"string","utf8Hex":""}') + 2 * len(value.encode('utf8'))
        elif type(value) is tuple:
            count = len(value)
            steps += count + 1
            size += len('{"kind":"array","items":[]}') + max(0, count - 1)
            pending.extend(value)
        elif type(value) is JsonObject:
            count = len(value.entries)
            steps += 3 * count + 1
            size += len('{"kind":"object","members":[]}') + max(0, count - 1)
            for key, child in value.entries:
                size += len('{"keyUtf8Hex":"","node":}') + 2 * len(key.encode('utf8'))
                pending.append(child)
        else:
            raise ValueError('Numeric-free retained tree required')
        if steps > 32768:
            raise ValueError('Native canonical tree task capacity exceeded')
        if size > 4194304:
            raise ValueError('Native canonical tree carrier capacity exceeded')

    root = [None]
    tasks = [(original.value, root, 0)]
    while tasks:
        value, destination, slot = tasks.pop()
        if value is None:
            node = {'kind': 'null'}
        elif type(value) is bool:
            node = {'kind': 'boolean', 'value': value}
        elif type(value) is str:
            node = {'kind': 'string', 'utf8Hex': value.encode('utf8').hex()}
        elif type(value) is tuple:
            items = [None] * len(value)
            node = {'kind': 'array', 'items': items}
            tasks.extend((child, items, index) for index, child in enumerate(value))
        else:
            members = [{'keyUtf8Hex': key.encode('utf8').hex(), 'node': None}
                       for key, _ in value.entries]
            node = {'kind': 'object', 'members': members}
            tasks.extend((child, members[index], 'node')
                         for index, (_, child) in enumerate(value.entries))
        destination[slot] = node
    text = json.dumps(root[0], ensure_ascii=True, separators=(',', ':'))
    if len(text) != size:
        raise ValueError('Native carrier preflight correspondence failed')
    return NativeReportCarrier(original, text, str(steps))
