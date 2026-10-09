"""Private bounded-source JSON convenience parser, not UMF/native admission.

Source/depth/node checks precede json.loads. This lexical preflight is not syntax
or semantic admission, nor complete precharged allocation accounting.
"""
from dataclasses import dataclass
import json


@dataclass(frozen=True)
class JsonNumberToken:
    text: str


@dataclass(frozen=True)
class JsonObject:
    entries: tuple


@dataclass(frozen=True)
class RetainedJson:
    source_bytes: bytes
    value: object


def parse_retained_json(source: bytes | bytearray, *, maximum_bytes: int,
                        maximum_depth: int, maximum_nodes: int) -> RetainedJson:
    if type(source) not in (bytes, bytearray) or any(
        type(bound) is not int or bound <= 0
        for bound in (maximum_bytes, maximum_depth, maximum_nodes)
    ) or maximum_depth > 128 or len(source) > maximum_bytes:
        raise ValueError("Original bytes and explicit finite candidate bounds required")
    original = bytes(source)
    text = original.decode("utf-8", errors="strict")
    depth = preflight_nodes = index = 0

    def charge_node():
        nonlocal preflight_nodes
        preflight_nodes += 1
        if preflight_nodes > maximum_nodes:
            raise ValueError("Selected JSON node count exceeded before parsing")

    # Count value starts without constructing decoded containers or scalar tokens.
    # Syntax (including malformed escapes) is still checked by json.loads.
    while index < len(text):
        char = text[index]
        if char in "[{":
            charge_node()
            depth += 1
            if depth > maximum_depth:
                raise ValueError("Selected JSON depth exceeded before parsing")
        elif char in "]}":
            depth -= 1
        elif char == '"':
            index += 1
            escaped = False
            while index < len(text):
                char = text[index]
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    break
                index += 1
            following = index + 1
            while following < len(text) and text[following] in " \t\r\n":
                following += 1
            # Object member names are not value nodes. Their bytes remain charged
            # by the whole source bound; syntax validation checks actual context.
            if following == len(text) or text[following] != ":":
                charge_node()
        elif char not in " \t\r\n,:":
            charge_node()
            while index + 1 < len(text) and text[index + 1] not in " \t\r\n,]}:":
                index += 1
        index += 1

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate exact JSON member")
            result[key] = value
        return result

    def reject_constant(_):
        raise ValueError("Non-JSON numeric constant")

    parsed = json.loads(text, parse_int=JsonNumberToken, parse_float=JsonNumberToken,
                        parse_constant=reject_constant, object_pairs_hook=object_pairs)
    nodes = 0

    def valid_string(value):
        if "\x00" in value:
            raise ValueError("PostgreSQL-bound NUL string unavailable")
        value.encode("utf-8", errors="strict")
        return value

    def freeze(value):
        nonlocal nodes
        nodes += 1
        if nodes > maximum_nodes:
            raise ValueError("Selected JSON node count exceeded")
        if type(value) is dict:
            return JsonObject(tuple((valid_string(key), freeze(child)) for key, child in value.items()))
        if type(value) is list:
            return tuple(freeze(child) for child in value)
        if type(value) is str:
            return valid_string(value)
        return value

    return RetainedJson(original, freeze(parsed))
