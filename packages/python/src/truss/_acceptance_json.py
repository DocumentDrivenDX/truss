# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private numeric-free wire decoder; not operation or native admission.

Uses byte, tree-depth, member-count and node-count limits.
Only individual already-scanned string tokens use the standard JSON decoder.
"""
import json


class AcceptanceJsonError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def decode_acceptance_json(original: bytes):
    """Strict numeric-free acceptance JSON with a 16-MiB byte limit."""
    return _decode_numeric_free(original, 16_777_216)


def decode_row_operation_json(original: bytes):
    """Numeric-free row operation JSON with an 8-MiB byte limit."""
    return _decode_numeric_free(original, 8_388_608)


def _decode_numeric_free(original: bytes, maximum_bytes: int):
    if type(original) is not bytes:
        raise AcceptanceJsonError("grammar")
    if len(original) > maximum_bytes:
        raise AcceptanceJsonError("resource")
    index, nodes = 0, 0
    stack = []
    missing = object()
    root = missing

    def refuse(reason):
        raise AcceptanceJsonError(reason)

    def peek():
        return original[index] if index < len(original) else None

    def take():
        nonlocal index
        result = peek()
        index += 1
        return result

    def whitespace():
        while peek() in (32, 9, 10, 13):
            take()

    def hex_code(reason):
        value = 0
        for _ in range(4):
            digit = take()
            if digit is None or chr(digit) not in "0123456789abcdefABCDEF":
                refuse(reason)
            value = value * 16 + int(chr(digit), 16)
        return value

    def string():
        start = index
        if take() != 34:
            refuse("grammar")
        closed = False
        while index < len(original):
            char = take()
            if char == 34:
                closed = True
                break
            if char < 32:
                refuse("grammar")
            if char == 92:
                escape = take()
                if escape == 117:
                    code = hex_code("grammar")
                    if 0xD800 <= code <= 0xDBFF:
                        if take() != 92 or take() != 117:
                            refuse("unicode")
                        if not 0xDC00 <= hex_code("unicode") <= 0xDFFF:
                            refuse("unicode")
                    elif 0xDC00 <= code <= 0xDFFF:
                        refuse("unicode")
                elif escape not in (34, 92, 47, 98, 102, 110, 114, 116):
                    refuse("grammar")
        if not closed:
            refuse("grammar")
        try:
            text = original[start:index].decode("utf-8", errors="strict")
        except UnicodeError:
            refuse("unicode")
        try:
            return json.loads(text)
        except ValueError:
            refuse("grammar")

    def attach(item):
        nonlocal root
        if not stack:
            if root is not missing:
                refuse("grammar")
            root = item
            return
        parent = stack[-1]
        if parent["kind"] == "array":
            if len(parent["value"]) >= 4096:
                refuse("resource")
            parent["value"].append(item)
        else:
            parent["value"][parent["key"]] = item
        parent["state"] = "comma"

    def value():
        nonlocal nodes
        whitespace()
        nodes += 1
        if nodes > 100_000 or len(stack) > 128:
            refuse("resource")
        char = peek()
        if char == 34:
            attach(string())
            return
        if char in (123, 91):
            take()
            item = {} if char == 123 else []
            attach(item)
            stack.append(dict(kind="object" if char == 123 else "array",
                              value=item, state="first", key="", keys=set()))
            return
        for token, result in ((b"null", None), (b"true", True), (b"false", False)):
            if char == token[0]:
                for expected in token:
                    if take() != expected:
                        refuse("grammar")
                attach(result)
                return
        if char == 45 or char is not None and 48 <= char <= 57:
            refuse("numeric_node")
        refuse("grammar")

    value()
    while stack:
        whitespace()
        frame, char = stack[-1], peek()
        state = frame["state"]
        if frame["kind"] == "array":
            if state == "first" and char == 93:
                take()
                stack.pop()
            elif state in ("first", "value"):
                value()
            elif char == 93:
                take()
                stack.pop()
            elif char == 44:
                take()
                frame["state"] = "value"
            else:
                refuse("grammar")
        elif state == "first" and char == 125:
            take()
            stack.pop()
        elif state in ("first", "key"):
            if char != 34:
                refuse("grammar")
            if len(frame["keys"]) >= 4096:
                refuse("resource")
            key = string()
            if key in frame["keys"]:
                refuse("duplicate_member")
            frame["keys"].add(key)
            frame["key"], frame["state"] = key, "colon"
        elif state == "colon":
            if take() != 58:
                refuse("grammar")
            frame["state"] = "value"
        elif state == "value":
            value()
        elif char == 125:
            take()
            stack.pop()
        elif char == 44:
            take()
            frame["state"] = "key"
        else:
            refuse("grammar")
    whitespace()
    if index != len(original) or root is missing:
        refuse("grammar")
    return root
