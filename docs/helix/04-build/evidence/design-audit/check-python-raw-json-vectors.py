"""Authored fixture consistency only; not a production decoder or native oracle."""
import json
from pathlib import Path


class NumericToken(str):
    pass


def closed_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Ambiguous duplicate fixture member")
        result[name] = value
    return result


def reject_constant(value):
    raise ValueError("Non-JSON fixture constant: " + value)


def decode_fixture(source):
    return json.loads(source, parse_int=NumericToken, parse_float=NumericToken,
                      object_pairs_hook=closed_object, parse_constant=reject_constant)


def pointer_part(text):
    return text.replace("~", "~0").replace("/", "~1")


def collect(value, pointer=""):
    numbers, strings = {}, {}
    if type(value) is NumericToken:
        numbers[pointer] = str(value)
    elif type(value) is str:
        strings[pointer] = value
    elif isinstance(value, dict):
        for name, child in value.items():
            n, s = collect(child, pointer + "/" + pointer_part(name))
            numbers.update(n)
            strings.update(s)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            n, s = collect(child, pointer + "/" + str(index))
            numbers.update(n)
            strings.update(s)
    return numbers, strings


def expected_inventory(entries, field):
    result = {}
    for entry in entries:
        if entry["pointer"] in result:
            raise ValueError("Duplicate expected pointer")
        result[entry["pointer"]] = entry[field]
    return result


root = Path(__file__).resolve().parents[3]
fixture = decode_fixture((root / "03-test/python-raw-json-vectors.proposal.json").read_bytes())
ids = set()
expectations = 0
for vector in fixture["vectors"]:
    if vector["id"] in ids:
        raise ValueError("Duplicate vector identity")
    ids.add(vector["id"])
    document = decode_fixture(vector["sourceUtf8Text"].encode("utf-8"))
    numbers, strings = collect(document)
    if numbers != expected_inventory(vector["expectedNumericTokens"], "token"):
        raise ValueError(vector["id"] + ": incomplete/wrong numeric token inventory")
    if strings != expected_inventory(vector["expectedStrings"], "text"):
        raise ValueError(vector["id"] + ": incomplete/wrong string inventory")
    expectations += len(numbers) + len(strings)
    for entry in vector.get("expectedPresence", []):
        value, present = document, True
        for part in entry["pointer"].split("/")[1:]:
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
                value = value[int(part)]
            else:
                present = False
                break
        state = "absent" if not present else "present-null" if value is None else (
            "present-empty-sequence" if type(value) is list and not value else "other")
        if state != entry["state"]:
            raise ValueError(vector["id"] + ": wrong presence expectation")
        expectations += 1
negative_controls = [b'{"n":NaN}', b'{"n":Infinity}', b'{"n":-Infinity}',
                     b'{"n":1,"n":2}', b'{"nested":{"n":1,"n":2}}']
for source in negative_controls:
    try:
        decode_fixture(source)
    except ValueError:
        continue
    raise ValueError("Unsafe fixture parser accepted negative control")
print(f"{len(ids)} fixtures, {expectations} complete token/string and presence expectations, "
      f"{len(negative_controls)} parser refusal controls; "
      "fixture consistency only, no adapter/native qualification")
