"""Private admitted-carrier projection; not a byte parser or model validator."""
from dataclasses import dataclass
from hashlib import sha256

from python_exact_numeric_candidate import (
    _bounded_text, integer_from_admitted_text, decimal_from_admitted_text,
)
from python_exact_timestamp_candidate import timestamp_from_admitted_text


@dataclass(frozen=True)
class TreeBounds:
    depth: int
    nodes: int
    entries: int
    text_bytes: int


@dataclass(frozen=True)
class ExactValue:
    kind: str
    payload: object


@dataclass(frozen=True)
class ExactPresence:
    present: bool
    value: ExactValue | None


def project_admitted_presence(carrier: dict, bounds: TreeBounds) -> ExactPresence:
    if type(bounds) is not TreeBounds or any(
        type(v) is not int or v <= 0 for v in
        (bounds.depth, bounds.nodes, bounds.entries, bounds.text_bytes)
    ) or bounds.depth > 128:
        raise ValueError("Explicit finite candidate bounds required")
    count = 0

    def closed(value, keys):
        if type(value) is not dict or set(value) != set(keys):
            raise ValueError("Closed admitted carrier required")

    def text(value, nonempty=False):
        value = _bounded_text(value, bounds.text_bytes)
        if "\x00" in value or (nonempty and not value):
            raise ValueError("PostgreSQL-bound exact text required")
        return value

    def items(value):
        if type(value) is not list or len(value) > bounds.entries:
            raise ValueError("Selected collection bound exceeded")
        return value

    def visit(value, depth):
        nonlocal count
        count += 1
        if count > bounds.nodes or depth > bounds.depth:
            raise ValueError("Selected tree bound exceeded")
        if type(value) is not dict or type(value.get("kind")) is not str:
            raise ValueError("Tagged admitted value required")
        kind = value["kind"]
        if kind in ("string", "binary", "integer", "decimal", "timestamp"):
            closed(value, ("kind", "text"))
            original = text(value["text"])
            convert = {"integer": integer_from_admitted_text,
                       "decimal": decimal_from_admitted_text,
                       "timestamp": timestamp_from_admitted_text}.get(kind)
            payload = convert(original, bounds.text_bytes) if convert else original
        elif kind == "null":
            closed(value, ("kind",))
            payload = None
        elif kind == "boolean":
            closed(value, ("kind", "value"))
            if type(value["value"]) is not bool:
                raise ValueError("Exact boolean required")
            payload = value["value"]
        elif kind == "sequence":
            closed(value, ("kind", "items"))
            payload = tuple(visit(entry, depth + 1) for entry in items(value["items"]))
        elif kind in ("map", "record"):
            record = kind == "record"
            closed(value, ("kind", "definitionPin", "fields") if record else ("kind", "entries"))
            identity_key = "fieldId" if record else "key"
            entries = items(value["fields" if record else "entries"])
            seen, projected = set(), []
            for entry in entries:
                closed(entry, (identity_key, "value"))
                identity = text(entry[identity_key], nonempty=record)
                if identity in seen:
                    raise ValueError("Duplicate exact entry identity")
                seen.add(identity)
                projected.append((identity, visit(entry["value"], depth + 1)))
            payload = (text(value["definitionPin"], True), tuple(projected)) if record else tuple(projected)
        elif kind == "opaque":
            closed(value, ("kind", "format", "sourceText", "sha256"))
            source = text(value["sourceText"])
            digest = text(value["sha256"])
            if sha256(source.encode("utf-8")).hexdigest() != digest:
                raise ValueError("Original opaque source digest mismatch")
            payload = (text(value["format"], True), source, digest)
        else:
            raise ValueError("Unsupported tagged carrier")
        return ExactValue(kind, payload)

    if type(carrier) is not dict or type(carrier.get("present")) is not bool:
        raise ValueError("Explicit presence required")
    if not carrier["present"]:
        closed(carrier, ("present",))
        return ExactPresence(False, None)
    closed(carrier, ("present", "value"))
    return ExactPresence(True, visit(carrier["value"], 1))
