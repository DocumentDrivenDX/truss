"""Private numeric-free wire decoder; not operation or native admission.

Matches the TypeScript acceptance decoder's logical resource accounting.
Only individual already-scanned string tokens use the standard JSON decoder.
"""
import json


class AcceptanceJsonError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def decode_acceptance_json(original: bytes):
    if type(original) is not bytes:
        raise AcceptanceJsonError("grammar")
    if len(original) > 1_048_576:
        raise AcceptanceJsonError("resource")
    index, nodes, work = 0, 0, len(original)
    stack = []
    missing = object()
    root = missing

    def refuse(reason):
        raise AcceptanceJsonError(reason)

    def charge(amount):
        nonlocal work
        if work > 2_000_000 - amount:
            refuse("resource")
        work += amount

    def peek():
        return original[index] if index < len(original) else None

    def take():
        nonlocal index
        charge(1)
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
        charge(2 * (index - start))
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
                              value=item, state="first", key="", keys=[]))
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

    def utf16_length(text):
        return len(text.encode("utf-16-le")) // 2

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
            for previous in frame["keys"]:
                charge(2 * (utf16_length(previous) + utf16_length(key)))
                if previous == key:
                    refuse("duplicate_member")
            frame["keys"].append(key)
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
