#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fresh public Linux TN-14. Stdlib preflight precedes every owner import.

Pure tests of this module are synthetic sensitivity checks, never qualification.
No source bootstrap, fixture TestCase, decoder patch or direct data writes.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib
import importlib.util
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from typing import ClassVar
from urllib.parse import unquote, urlparse
from zipfile import ZipFile

PACKAGES = {'truss': 'truss', 'core': 'umf', 'access': 'umf_access', 'weft': 'weft'}
OPERATIONS = ('install', 'accept-local-property', 'write', 'import', 'typed-read',
              'hidden-composite-pages', 'replay-2.1', 'ordinary-1.2')
KINDS = ('instant', 'date', 'local')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()



def retain_result(output, operation, value):
    def encode(item):
        if is_dataclass(item):
            return {key: encode(value) for key, value in asdict(item).items()}
        if type(item) is bytes:
            return {'encoding': 'base64', 'bytes': base64.b64encode(item).decode(), 'sha256': digest(item)}
        if type(item) in (datetime, date):
            return {'type': type(item).__name__, 'iso': item.isoformat(),
                    'aware': isinstance(item, datetime) and item.tzinfo is not None}
        if isinstance(item, dict):
            return {key: encode(value) for key, value in item.items()}
        if isinstance(item, (list, tuple)):
            return [encode(value) for value in item]
        return item
    (output / (operation + '-result.json')).write_bytes(canonical(encode(value)))


def read_json(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def load_control(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight(assets, publication, source, controller):
    """Authenticate A's original closure; no Truss/native import is allowed here."""
    publication = read_json(publication)
    need(publication.get('schema') == 'pypi-publication-receipt.v1'
         and publication.get('status') == 'passed'
         and publication.get('registry_bytes_verified') is True,
         'Actual successful public byte verification required')
    receipt = read_json(assets / 'source-receipt.json')
    need(receipt.get('schema') == 'pypi-release-source.v1' and receipt.get('status') == 'verified'
         and receipt.get('github_release_immutable') is True, 'Authenticated immutable release source receipt required')
    need(digest((assets / 'SHA256SUMS').read_bytes()) == receipt.get('sums_sha256')
         and digest((assets / 'release-pins.json').read_bytes()) == receipt.get('release_pins_sha256'),
         'Public qualification assets do not join authenticated release checksums/pins')
    sums = {}
    for line in (assets / 'SHA256SUMS').read_text().splitlines():
        parts = line.split()
        need(len(parts) == 2 and parts[1] not in sums and Path(parts[1]).name == parts[1],
             'Closed unique release checksum entries required')
        sums[parts[1]] = parts[0]
    for name in ('temporal-qualification-binding.json', 'temporal-qualified-evidence.zip',
                 'temporal-qualification-intake.json', 'temporal-qualified-member-manifest.json'):
        need(name in sums and digest((assets / name).read_bytes()) == sums[name],
             'Public original qualification asset hash differs: ' + name)
    commit = receipt.get('source_sha')
    need(commit and publication.get('source_sha') == commit
         and publication.get('files') == receipt.get('files')
         and publication.get('version') == receipt.get('version')
         and publication.get('distribution') == receipt.get('distribution'),
         'Publication/source/archive identity mismatch')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()
    need(git('rev-parse', 'HEAD') == commit, 'Exact released source checkout required')
    tree = git('rev-parse', 'HEAD^{tree}')
    # The controller is deliberately equal to the released source for this route.
    # A future Q!=S route needs explicit review, never an equivalence waiver.
    controls = ('verify_published_temporal_consumer.py', 'temporal_qualified_artifact.py',
                'temporal_qualification_support.py', 'component_prerequisite_validators.py',
                'install-local-runtime.py')
    hashes = {}
    for name in controls:
        original = source / 'scripts' / name
        actual = controller / name
        need(original.is_file() and actual.is_file() and original.read_bytes() == actual.read_bytes(),
             'Admitted controller/source differs: ' + name)
        hashes[name] = digest(actual.read_bytes())
    sys.modules['component_prerequisite_validators'] = load_control(
        controller / 'component_prerequisite_validators.py', 'component_prerequisite_validators')
    helper = load_control(controller / 'temporal_qualified_artifact.py', 'tn14_qualified_artifact')
    qualified = helper.verify_release_staging(assets, source_commit=commit, source_tree=tree)
    binding = read_json(assets / 'temporal-qualification-binding.json')
    need(binding.get('componentPrerequisiteReceipts'), 'Missing component stage prerequisites')
    candidate = binding['candidateWheel']
    wheel = assets / candidate['filename']
    raw = wheel.read_bytes()
    need(digest(raw) == qualified['candidateWheelSha256'] == candidate['sha256'],
         'Public candidate is not the qualified original wheel')
    with ZipFile(io.BytesIO(raw)) as archive:
        profile_raw = archive.read('truss/_profiles/local-postgres-runtime.json')
    need(profile_raw == (source / 'packages/python/src/truss/_profiles/local-postgres-runtime.json').read_bytes(),
         'Released runtime profile differs from admitted source')
    profile = json.loads(profile_raw)
    need(profile['repository'] == 'https://github.com/DocumentDrivenDX/pgserver'
         and profile['serverVersion'] == '18.6', 'Selected public PostgreSQL profile required')
    with ZipFile(assets / 'temporal-qualified-evidence.zip') as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    cohort = json.loads(members[binding['receipts']['cohort']['path']])
    return dict(publication=publication, source=receipt, binding=binding, qualified=qualified,
                controls=hashes, cohort=cohort, members=members, profile=profile,
                profileSha256=digest(profile_raw))


def validate_origins(report, cohort, wheel_hashes, runtime):
    """Only one exact checksum-authenticated public runtime file is exceptional."""
    selected = {}
    for item in report.get('install', ()):
        info = item.get('download_info', {})
        url = info.get('url', '')
        parsed = urlparse(url)
        name = item['metadata']['name'].lower().replace('_', '-')
        sha = info.get('archive_info', {}).get('hashes', {}).get('sha256')
        if parsed.scheme == 'file':
            need(not parsed.netloc and name == runtime['distribution'].lower().replace('_', '-')
                 and Path(unquote(parsed.path)).resolve() == Path(runtime['path']).resolve()
                 and sha == runtime['sha256'] and item['metadata']['version'] == runtime['version'],
                 'Only the exact verified public runtime file may use local origin')
        else:
            need(parsed.scheme == 'https' and parsed.hostname == 'files.pythonhosted.org'
                 and not parsed.username and not parsed.password and parsed.port in (None, 443),
                 'Private/source/non-public installation origin')
            need(parsed.path.endswith('.whl'), 'Public source build is forbidden')
        need(name not in selected, 'Duplicate installed distribution')
        selected[name] = item
    for owner, expected in cohort.items():
        if owner not in PACKAGES:
            continue
        name = expected['distribution'].lower().replace('_', '-')
        item = selected.get(name)
        need(item is not None and item['metadata']['version'] == expected['version']
             and item['download_info']['archive_info']['hashes']['sha256'] == wheel_hashes[owner],
             'Public owner wheel/version differs: ' + owner)
    need(runtime['distribution'].lower().replace('_', '-') in selected, 'Public runtime install missing')
    return selected


def verify_record(distribution, wheel_bytes):
    """Compare full original wheel payload and installed RECORD before imports."""
    files = list(distribution.files or ())
    need(files, 'Installed wheel RECORD missing')
    listed = {str(path): path for path in files}
    with ZipFile(io.BytesIO(wheel_bytes)) as archive:
        for name in archive.namelist():
            if name.endswith('/') or name.endswith('.dist-info/RECORD'):
                continue
            need('.data/' not in name, 'Unmapped relocated owner wheel payload')
            need(name in listed, 'Original member absent from installed RECORD: ' + name)
            path = Path(distribution.locate_file(listed[name]))
            need(path.is_file() and not path.is_symlink() and path.read_bytes() == archive.read(name),
                 'Installed source/native/payload substitution: ' + name)
    observations = {}
    for entry in files:
        path = Path(distribution.locate_file(entry))
        need(path.is_file() and not path.is_symlink(), 'Installed RECORD member missing/unsafe')
        if entry.hash is not None:
            need(entry.hash.mode == 'sha256', 'Unsupported installed RECORD hash')
            raw = path.read_bytes()
            need(base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode() == entry.hash.value
                 and len(raw) == entry.size, 'Installed RECORD hash/size mismatch')
            observations[str(entry)] = digest(raw)
        else:
            need(str(entry).endswith(('.pyc', '.dist-info/RECORD')), 'Unexpected unhashed installed member')
    return observations


def installed_identity(context, report, runtime):
    binding, members, cohort = context['binding'], context['members'], context['cohort']
    wheels = {}
    for owner in PACKAGES:
        path = 'inputs/' + binding['originalWheelPaths'][owner]['archivePath']
        need(path in members and path.startswith('inputs/') and path.endswith('.whl'),
             'Original admitted wheel member missing: ' + owner)
        wheels[owner] = members[path]
    validate_origins(report, cohort, {owner: digest(raw) for owner, raw in wheels.items()}, runtime)
    for forbidden in ('weft-sql', 'pgserver', 'pgserver-pg16', 'pgserver-pg17'):
        try:
            metadata.distribution(forbidden)
        except metadata.PackageNotFoundError:
            continue
        raise ValueError('Conflicting owner/runtime distribution: ' + forbidden)
    records = {}
    for owner, package in PACKAGES.items():
        expected = cohort[owner]
        dist = metadata.distribution(expected['distribution'])
        need(dist.version == expected['version'], 'Installed owner version mismatch')
        records[owner] = verify_record(dist, wheels[owner])
        # find_spec may import parent packages, so actual module imports follow RECORD checks.
    for owner, package in PACKAGES.items():
        module = importlib.import_module(package)
        dist = metadata.distribution(cohort[owner]['distribution'])
        expected = Path(dist.locate_file(package)).resolve()
        need(Path(module.__file__).resolve().is_relative_to(expected)
             and expected.is_relative_to(Path(sys.prefix).resolve()), 'Loaded owner origin differs')
    for owner, package, native_name in (('core', 'umf', 'umf._rust'), ('weft', 'weft', 'weft.weft')):
        native = importlib.import_module(native_name)
        if owner == 'core':
            native = native._rust_core
        base = Path(importlib.import_module(package).__file__).resolve().parent
        path = Path(native.__file__).resolve()
        selected = binding['ownerIdentities'][owner]
        need(path.is_relative_to(base) and str(path.relative_to(base)) == selected['modulePath']
             and digest(path.read_bytes()) == selected['moduleSha256'], 'Actual loaded owner native module differs')
    need(metadata.distribution(runtime['distribution']).version == runtime['version'], 'Runtime version differs')
    records['runtime'] = verify_record(metadata.distribution(runtime['distribution']), Path(runtime['path']).read_bytes())
    return records


def expected_rows():
    return [(datetime(2024, 1, 1, tzinfo=timezone.utc), date(2024, 1, i + 1),
             datetime(2024, 2, 29, 12, 0, i, 1)) for i in range(6)]


def assert_rows(actual, expected):
    need(len(actual) == len(expected), 'Typed row count/completeness mismatch')
    for row, wanted in zip(actual, expected, strict=True):
        need(len(row) == 3 and type(row[0]) is datetime and row[0].tzinfo is not None
             and type(row[1]) is date and type(row[2]) is datetime and row[2].tzinfo is None,
             'Strict instant/date/local type distinction lost')
        need(row == wanted, 'Authored temporal values differ')


def assert_pages(metadata, pages, expected):
    keys = metadata['keyOutputPositions']
    need(len(keys) == 2 and len(set(keys)) == 2
         and set(keys) - set(metadata['visibleOutputPositions']), 'Hidden full compositeKey required')
    need([len(items) for items, token in pages] == [2, 2, 2], 'Page boundaries differ')
    need([row for items, token in pages for row in items] == expected, 'Page ordering/completeness differs')
    tokens = [token for items, token in pages[:-1]]
    need(all(type(token) is bytes and token for token in tokens) and len(set(tokens)) == len(tokens)
         and pages[-1][1] is None, 'Actual owner continuation bytes missing/repeated')


def assert_replay(prepared, document, stored, first_report, replay):
    need(replay.replayed is True and replay.report_bytes == first_report, 'Original acceptance replay/report differs')
    need(tuple(bytes(value) for value in stored[:3]) ==
         (prepared.input_bytes, prepared.archive_documents_bytes, prepared.declarations_bytes),
         'Original retained preparation bytes differ')
    summary = json.loads(bytes(stored[3])); archived = json.loads(bytes(stored[1]))
    declarations = json.loads(bytes(stored[2]))
    need(summary['sourceFormat'] == 'truss-registration-summary/2.1', 'Original summary2.1 required')
    need(archived[0]['originalText'].encode() == document.content
         and archived[0]['validation']['inspection'] == summary['documentValidations'][0]['inspection'],
         'Original retained document/inspection differs')
    local = [field for record in declarations[0]['records'] for field in record['fields']
             if 'nativeDescriptor' in field]
    need(local and all(field['declaration']['scalarType'] == 'timestamp'
                      and field['nativeDescriptor']['nativeScalarType'] == 'localTimestamp' for field in local),
         'Accepted local property descriptor missing')


def _assert_operation_results(operations):
    need(set(operations) == set(OPERATIONS), 'Missing actual TN-14 operation')
    for name in OPERATIONS:
        need(operations[name].get('status') == 'passed', 'Unasserted operation: ' + name)
    for name in ('write', 'import', 'typed-read'):
        need(operations[name].get('kinds') == list(KINDS), 'Missing temporal kind: ' + name)


def assert_operations(operations, cleanup):
    _assert_operation_results(operations)
    need(cleanup.confirmed, 'Native cleanup empty/mixed/uncertain')


def authored_document():
    """Minimal authored A/B data from the existing temporal public API corpus."""
    fields = [('A-label', 'string'), ('A-value', 'string'), ('A-date', 'date'),
              ('A-instant', 'timestamp'), ('A-local', 'timestamp'), ('A-payload', 'string'),
              ('B-label', 'string'), ('B-value', 'string')]
    elements, views = [], []
    for record in ('A', 'B'):
        names = [name for name, kind in fields if name.startswith(record + '-')]
        elements.append(dict(id=record, name=record, kind='record',
            members=[dict(module='m', element=name) for name in names],
            keys=[dict(id='a-primary', name='primary', primary=True,
                       fields=[dict(module='m', element=record + '-value'),
                               dict(module='m', element=record + '-label')])], extensions={}))
        view_fields = []
        for name in names:
            optional = name == 'A-local'
            field = dict(field=dict(module='m', element=name), row=dict(missing=optional, null=optional),
                         create=dict(missing=optional, null=optional), mutable=name not in ('A-label', 'A-value', 'B-label', 'B-value'),
                         generated=False)
            if name in ('A-instant', 'A-local'):
                field['temporal'] = 'instant' if name == 'A-instant' else 'local'
            view_fields.append(field)
        views.append(dict(record=dict(module='m', element=record), fields=view_fields,
                          selectedKey=dict(module='m', element=record, key='a-primary')))
    for name, kind in fields:
        elements.append(dict(id=name, name=name, kind='field', scalarType=kind,
            nullability='absent-allowed' if name == 'A-local' else 'required', cardinality='one', extensions={}))
    return dict(umf='0.10.0', id='adoc', vocabularies={'umf.access': {'version': '0.1.0'}}, extensions={},
                modules=[dict(id='m', namespace='m', extensions={'umf.access': dict(views=views, columns=[], search=[], searchBindings=[])},
                              elements=elements, relationships=[])])


class PublicSession:
    def __init__(self, api, runtime):
        self.api, self.runtime = api, runtime
        self.params = api.pg.conninfo.conninfo_to_dict(runtime.info.connection_uri)

    @contextmanager
    def transaction(self, user='consumer', readonly=False):
        api = self.api
        with api.pg.connect(**{**self.params, 'user': user}, autocommit=True,
                            options='-c statement_timeout=15000') as connection:
            connection.execute('BEGIN READ ONLY' if readonly else 'BEGIN')
            host = api.truss.adopt_psycopg_host(connection, statement_timeout_ms=15000, operation_timeout_ms=30000)
            try:
                tx = self.ok(host.adopt_transaction(access_mode='read_only' if readonly else 'read_write'))
                assembly = self.ok(api.truss.create_reference_assembly(api.truss.CatalogRuntimeConfiguration(), host))
                yield connection, assembly, tx
                need(host.detach(), 'Host detach failed')
                connection.commit()
            except BaseException:
                host.detach(); connection.rollback()
                raise

    def ok(self, result):
        need(isinstance(result, self.api.truss.Ok), 'Public API refused: ' + repr(result))
        return result.value

    def admin(self):
        return self.api.pg.connect(**self.params, autocommit=True, options='-c statement_timeout=15000')

    def query(self, row, sql, *, page=False, ordinary=False):
        from umf_access.engine_catalog import EngineRead
        from umf_access.types import StrictModel
        class Parameters(StrictModel):
            pass
        with self.transaction(readonly=True) as (connection, assembly, tx):
            method = assembly.query_catalog_sources_in_transaction if ordinary else assembly.query_temporal_catalog_sources_in_transaction
            captured = self.ok(method(tx, sql=sql, document_ids=('adoc',)))
        original = json.loads(captured.request_json)
        options = {'method': 'truss-runtime'} if ordinary else {
            'method': 'truss-runtime-temporal', 'temporal_profile': 'umf.weft-binding-temporal/0.2'}
        if page:
            options.update(page_size=2, selected_key={'module': 'm', 'record': 'A', 'key': 'a-primary'})
        entry = EngineRead.build(self.api.weft, original, parameters=Parameters, result=row, **options)
        need(entry.artifact()['request'] == original, 'Original compiler request changed')
        return entry, Parameters()

    def target(self, entry):
        from truss.access import TrussTarget
        @contextmanager
        def operation(budget):
            with self.transaction(readonly=True) as (connection, assembly, tx):
                yield assembly, tx
        return TrussTarget(operation, binding_sha256=entry.artifact()['request']['target']['bindingSha256'],
            platform=(('postgresql', '18.6'),), default_timeout=timedelta(seconds=15), catalog_entries=(entry,))


def values(api, index, *, ordinary=False):
    contracts = api.contracts
    authored = api.temporal.AuthoredValue
    prefix = 'B' if ordinary else 'A'
    result = [authored(name=prefix + '-label', value=contracts.TextValue(kind='string', text=f'row-{index}')),
              authored(name=prefix + '-value', value=contracts.TextValue(kind='string', text='shared-key'))]
    if not ordinary:
        result += [authored(name='A-date', value=contracts.TextValue(kind='date', text=f'2024-01-{index+1:02}')),
                   authored(name='A-instant', value=contracts.TextValue(kind='timestamp', text='2024-01-01T00:00:00Z')),
                   authored(name='A-local', value=contracts.LocalTimestampValue(text=f'2024-02-29T12:00:{index:02}.000001')),
                   authored(name='A-payload', value=contracts.TextValue(kind='string', text='public-tn14'))]
    return tuple(result)


def write_and_import(session, documents, output=None):
    api = session.api
    with session.transaction() as (connection, assembly, tx):
        selected = assembly.temporal_values()
        refs = {record: session.ok(assembly.get_type_reference_in_transaction(tx, document_id='adoc', module_id='m', record_id=record))
                for record in ('A', 'B')}
        operations = tuple(api.temporal.CreateObject(type_definition_pin=refs['A'].definition_pin,
            values=values(api, i), ownership=api.groups.RootlessOwnership(), alias=f'row{i}') for i in range(3))
        context = session.ok(selected.group_context_in_transaction(tx))
        original = context.input(operations, api.contracts.MapValue(entries=()))
        request = context.request('tn14-public-three-writes')
        applied = session.ok(selected.apply_in_transaction(tx, original, request, documents=documents))
        need(isinstance(applied, api.groups.GroupSuccess)
             and len(applied.response.semantic.results) == 3
             and all(item.outcome == 'created' for item in applied.response.semantic.results), 'Actual temporal group create failed')
        if output is not None:
            retain_result(output, 'write', {'input': original, 'request': request, 'result': applied})
        # Independent ordinary sibling uses the ordinary facade and carriers.
        ordinary_context = session.ok(assembly.group_context_in_transaction(tx))
        ordinary_values = tuple(api.groups.AuthoredValue(name=value.name, value=value.value) for value in values(api, 0, ordinary=True))
        ordinary = api.groups.CreateObject(type_definition_pin=refs['B'].definition_pin,
            values=ordinary_values, ownership=api.groups.RootlessOwnership(), alias='ordinary')
        sibling = session.ok(assembly.apply_in_transaction(tx,
            ordinary_context.input((ordinary,), api.contracts.MapValue(entries=())),
            ordinary_context.request('tn14-ordinary-sibling'), documents=documents))
        need(isinstance(sibling, api.groups.GroupSuccess), 'Ordinary sibling create failed')
    with session.transaction() as (connection, assembly, tx):
        selected = assembly.temporal_values()
        context = session.ok(selected.import_context_in_transaction(tx))
        records = tuple(session.ok(selected.object_import_record_in_transaction(tx,
            document_id='adoc', module_id='m', record_id='A', values=values(api, i))) for i in range(3, 6))
        original = context.input(records, load_id='tn14-public-import', asserted_origin=api.contracts.MapValue(entries=()))
        imported = selected.import_in_transaction(tx, original, documents=documents)
        need(isinstance(imported, api.imports.ImportReported)
             and len(imported.report.outcomes) == 3 and not imported.report.unprocessed_indices
             and all(isinstance(item, api.imports.ImportCreated) for item in imported.report.outcomes),
             'Actual temporal import did not create all records')
        if output is not None:
            retain_result(output, 'import', {'input': original, 'result': imported})
    return {'write': dict(status='passed', kinds=list(KINDS), count=3, request='tn14-public-three-writes'),
            'import': dict(status='passed', kinds=list(KINDS), count=3, load='tn14-public-import')}


def generated_models(api, document, destination):
    from umf import rust_codegen
    package = 'tn14_public_models'
    owner = rust_codegen.CodegenEngine.from_installed(max_work=1_000_000)
    generated = owner.generate_python_client({'text': document.content.decode(), 'package': package})
    need(generated.get('files'), 'Real installed owner generation missing')
    for entry in generated['files']:
        relative = Path(entry['path'])
        need(not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] == package,
             'Generated source path escaped')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True); target.write_text(entry['text'])
    (destination / 'owner-generation.json').write_bytes(canonical(generated))
    sys.path.insert(0, str(destination))
    try:
        models = importlib.import_module(package + '.models')
    finally:
        sys.path.remove(str(destination))
    source = json.loads(document.content)
    result = {}
    for record in ('A', 'B'):
        required = {member['element'] for element in source['modules'][0]['elements']
                    if element['id'] == record for member in element['members']}
        rows = [value for value in vars(models).values() if isinstance(value, type) and hasattr(value, 'objects')
                and {element for module, element, name in getattr(value, 'UMF_FIELDS', ()) if module == 'm'} == required]
        need(len(rows) == 1, 'One genuine owner-generated model required: ' + record)
        need(rows[0].UMF_SOURCE.document_sha256 == digest(document.content), 'Generated source custody differs')
        result[record] = rows[0]
    return result


def typed_reads(session, models, output=None):
    from umf_access.types import StrictModel
    row = models['A']; names = {element: name for module, element, name in row.UMF_FIELDS}
    quote = lambda name: '"' + name.replace('"', '""') + '"'
    sql = 'SELECT ' + ','.join(quote(element) + ' AS ' + quote(name) for module, element, name in row.UMF_FIELDS)
    sql += ' FROM "A" ORDER BY "A-instant" ASC,"A-label" ASC'
    entry, parameters = session.query(row, sql)
    target = session.target(entry); target.verify()
    actual = target.read(entry, parameters)
    observed = [(getattr(item, names['A-instant']), getattr(item, names['A-date']), getattr(item, names['A-local'])) for item in actual]
    assert_rows(observed, expected_rows())
    if output is not None:
        retain_result(output, 'typed-read', {'original': entry.originals(), 'observed': observed})
    need([getattr(item, names['A-label']) for item in actual] == [f'row-{i}' for i in range(6)], 'Stable authored ordering differs')
    # Hidden full key: only instant is visible, and every row shares its value
    # and first business-key component. Losing the second key skips rows.
    fields = tuple(field for field in row.UMF_FIELDS if field[1] in ('A-instant', 'A-date', 'A-local'))
    namespace = {'__module__': __name__, 'UMF_SOURCE': row.UMF_SOURCE, 'UMF_FIELDS': fields,
        '__annotations__': {'UMF_SOURCE': ClassVar[type(row.UMF_SOURCE)], 'UMF_FIELDS': ClassVar[tuple],
            **{name: row.model_fields[name].rebuild_annotation() for module, element, name in fields}}}
    projection = type('PublicHiddenInstant', (StrictModel,), namespace)
    page_sql = 'SELECT ' + ','.join(quote(element) + ' AS ' + quote(name) for module, element, name in fields) + ' FROM "A" ORDER BY "A-instant" ASC'
    entry, parameters = session.query(projection, page_sql, page=True)
    target = session.target(entry); pages = []; after = None
    for index in range(4):
        batch = target.page(entry, parameters, after=after)
        after = batch.next_after
        pages.append(([(getattr(item, names['A-instant']), getattr(item, names['A-date']), getattr(item, names['A-local'])) for item in batch.items], None if after is None else after.owner_cursor))
        if after is None:
            break
    assert_pages(entry.artifact()['page'], pages, expected_rows())
    assert_rows([item for items, token in pages for item in items], expected_rows())
    if output is not None:
        retain_result(output, 'hidden-composite-pages', {'original': entry.originals(), 'pages': pages})
    ordinary_row = models['B']
    ordinary_sql = 'SELECT ' + ','.join(quote(element) + ' AS ' + quote(name) for module, element, name in ordinary_row.UMF_FIELDS) + ' FROM "B"'
    ordinary, parameters = session.query(ordinary_row, ordinary_sql, ordinary=True)
    request = ordinary.artifact()['request']
    # Inspect the original public capture, not a fabricated binding carrier.
    ordinary_binding = json.loads(request['target']['bindingJson'])
    need(ordinary_binding['queryAbi']['version'] == '1.2', 'Ordinary request must retain ABI1.2')
    sibling = session.target(ordinary).read(ordinary, parameters)
    need(len(sibling) == 1 and all(type(getattr(sibling[0], name)) is str and getattr(sibling[0], name) ==
         ('row-0' if element == 'B-label' else 'shared-key') for module, element, name in ordinary_row.UMF_FIELDS),
         'Independent ordinary sibling result differs')
    if output is not None:
        retain_result(output, 'ordinary-1.2', {'original': ordinary.originals(),
            'rows': [[getattr(item, name) for module, element, name in ordinary_row.UMF_FIELDS] for item in sibling]})
    return {'typed-read': dict(status='passed', kinds=list(KINDS), rows=6),
            'hidden-composite-pages': dict(status='passed', pageSizes=[len(items) for items, token in pages], keyOutputPositions=entry.artifact()['page']['keyOutputPositions']),
            'ordinary-1.2': dict(status='passed', rows=1, requestSha256=digest(canonical(request)))}


def accept_and_replay(session, document, output=None):
    api = session.api
    with session.admin() as admin:
        admin.execute('CREATE ROLE consumer LOGIN')
    with session.transaction(user='postgres') as (connection, assembly, tx):
        installation = session.ok(assembly.install_in_transaction(tx))
        need(installation.status == 'pending_commit', 'Fresh native install missing')
    with session.admin() as admin:
        admin.execute(api.pg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(api.pg.sql.Identifier(installation.registrar_role)))
    with session.transaction() as (connection, assembly, tx):
        selected = assembly.temporal_values()
        prepared = selected.prepare_catalog((document,))
        accepted = session.ok(selected.accept_in_transaction(tx, prepared, request_key='tn14-public-model'))
        need(accepted.revision == 1 and not accepted.replayed, 'Fresh temporal acceptance required')
    with session.transaction() as (connection, assembly, tx):
        replay = session.ok(assembly.temporal_values().accept_in_transaction(tx, prepared, request_key='tn14-public-model'))
        with session.admin() as admin:
            stored = admin.execute('SELECT input_bytes,document_bytes,declaration_bytes,source_bytes FROM truss.catalog_registration_request WHERE request_key=%s', ('tn14-public-model',)).fetchone()
        assert_replay(prepared, document, stored, accepted.report_bytes, replay)
    with session.transaction() as (connection, assembly, tx):
        again = session.ok(assembly.temporal_values().accept_in_transaction(tx, prepared, request_key='tn14-public-model'))
        with session.admin() as admin:
            retained = admin.execute('SELECT input_bytes,document_bytes,declaration_bytes,source_bytes FROM truss.catalog_registration_request WHERE request_key=%s', ('tn14-public-model',)).fetchone()
        assert_replay(prepared, document, retained, replay.report_bytes, again)
        need(retained == stored, 'Repeated replay changed retained bytes')
    if output is not None:
        retain_result(output, 'install', installation)
        retain_result(output, 'accept-local-property', {'document': document, 'prepared': prepared, 'accepted': accepted})
        retain_result(output, 'replay-2.1', {'retained': stored, 'firstReport': accepted.report_bytes, 'replay': again})
    with session.admin() as admin:
        # Only role/ACL setup uses administrative SQL; model and rows come from
        # the public acceptance, group and import APIs above/below.
        for role in ('tn14_reader', 'tn14_writer'):
            admin.execute(api.pg.sql.SQL('CREATE ROLE {} NOLOGIN').format(api.pg.sql.Identifier(role)))
    with session.transaction(user='postgres') as (connection, assembly, tx):
        configured = session.ok(assembly.configure_module_access_in_transaction(tx,
            (api.truss.ModuleAccessGrant('adoc', 'm', 'tn14_reader', 'tn14_writer'),)))
        need(isinstance(configured, api.truss.PendingModuleAccessConfiguration), 'Actual module grant configuration missing')
    with session.admin() as admin:
        admin.execute('GRANT tn14_writer TO consumer WITH SET FALSE')
        admin.execute(api.pg.sql.SQL('REVOKE {} FROM consumer').format(api.pg.sql.Identifier(installation.registrar_role)))
    return {'install': dict(status='passed', installationStatus=installation.status),
            'accept-local-property': dict(status='passed', revision=accepted.revision, documentSha256=digest(document.content)),
            'replay-2.1': dict(status='passed', requestKey='tn14-public-model', reportSha256=digest(replay.report_bytes),
                               retainedSha256=[digest(bytes(value)) for value in stored])}


def finish_cleanup(runtime, monitor, root, *, remove=True):
    """Close and remove through the same owned-tree gate as the isolated campaign."""
    monitor.finish_runtime(runtime, root, remove=remove)


def run_native(context, output, controller, *, seconds=300):
    # All prerequisite/public/RECORD admission happens in main before here.
    from types import SimpleNamespace
    import psycopg
    import truss
    from truss import contracts, groups, imports, temporal
    import weft
    api = SimpleNamespace(pg=psycopg, truss=truss, contracts=contracts, groups=groups, imports=imports,
                          temporal=temporal, weft=weft)
    support = load_control(controller / 'temporal_qualification_support.py', 'tn14_cleanup_support')
    root = Path(tempfile.mkdtemp(prefix='truss-public-tn14-'))
    runtime = truss.LocalPostgres(root / 'data')
    monitor = support.OwnedNativeCleanup([], output / 'cleanup.json', only_runtime=runtime)
    operations = {}
    def timed_out(signum, frame):
        raise TimeoutError('Public TN-14 operation deadline')
    old_term = signal.signal(signal.SIGTERM, timed_out)
    old_alarm = signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(seconds)
    try:
        with monitor:
            try:
                runtime.__enter__()
                need(runtime.info.server_version == context['profile']['serverVersion'], 'Actual server version differs')
                session = PublicSession(api, runtime)
                document = truss.CatalogDocument('adoc', 'r1', canonical(authored_document()))
                operations.update(accept_and_replay(session, document, output))
                (output / 'operations.json').write_bytes(canonical(operations))
                operations.update(write_and_import(session, (document,), output))
                (output / 'operations.json').write_bytes(canonical(operations))
                models = generated_models(api, document, output / 'generated')
                operations.update(typed_reads(session, models, output))
                (output / 'operations.json').write_bytes(canonical(operations))
                for name in OPERATIONS:
                    path = output / (name + '-result.json')
                    need(path.is_file(), 'Original operation result evidence missing: ' + name)
                    operations[name]['result'] = {'path': path.name, 'sha256': digest(path.read_bytes())}
                _assert_operation_results(operations)
            finally:
                signal.alarm(0)
                finish_cleanup(runtime, monitor, root, remove=sys.exc_info()[0] is None)
    finally:
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGALRM, old_alarm)
    need(monitor.confirmed, 'Owned cleanup uncertain; retained: ' + str(root))
    assert_operations(operations, monitor)
    return operations, read_json(output / 'cleanup.json')


def install_public(context, source, output, *, deadline=None):
    """Download-only public runtime exception, normal resolver for all owners."""
    def timeout(maximum):
        remaining = maximum if deadline is None else min(maximum, int(deadline - time.monotonic()))
        need(remaining > 0, 'TN-14 job work deadline exhausted; cleanup reserve preserved')
        return remaining
    subprocess.run([sys.executable, '-I', '-B', str(source / 'scripts/install-local-runtime.py'),
                    '--download-only', '--wheelhouse', str(output / 'runtime')], check=True, timeout=timeout(90))
    profile = context['profile']
    wheels = list((output / 'runtime').glob('*.whl'))
    need(len(wheels) == 1, 'One verified public runtime wheel required')
    wheel = wheels[0]
    sums = (output / 'runtime/SHA256SUMS').read_text().splitlines()
    expected = [line.split()[0] for line in sums if len(line.split()) == 2 and line.split()[1] == wheel.name]
    need(expected == [digest(wheel.read_bytes())], 'Public runtime checksum mismatch')
    candidate = context['binding']['candidateWheel']
    subprocess.run([sys.executable, '-m', 'pip', '--isolated', 'install', '--disable-pip-version-check',
        '--no-cache-dir', '--only-binary=:all:', '--index-url', 'https://pypi.org/simple',
        '--report', str(output / 'install-report.json'),
        candidate['distribution'] + '[local,native,query,typed-sdk]==' + candidate['version'], str(wheel.resolve())],
        check=True, timeout=timeout(120))
    subprocess.run([sys.executable, '-m', 'pip', '--isolated', 'check'], check=True, timeout=timeout(30))
    return dict(distribution=profile['distribution'], version=profile['distributionVersion'],
                path=str(wheel.resolve()), sha256=expected[0], profileSha256=context['profileSha256'],
                canonicalRelease=profile['repository'] + '/releases/tag/' + profile['releaseTag'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', required=True, type=Path)
    parser.add_argument('--publication', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    controller = Path(__file__).resolve().parent
    args.output.mkdir(parents=True, exist_ok=False)
    status = {'schema': 'truss.public-temporal-consumer/1', 'status': 'failed',
              'scope': 'Fresh Linux public TN-14 only; separate HF/platform obligations not claimed'}
    try:
        need(sys.platform == 'linux', 'Selected consumer is Linux only')
        need(not Path.cwd().resolve().is_relative_to(args.source.resolve()), 'Consumer must run outside repository')
        context = preflight(args.assets, args.publication, args.source, controller)
        # Leave at least 75 seconds for original native stop proof/upload.
        # This bounded B work envelope is inside the unchanged ten-minute job;
        # the eventual complete-job timing remains an admission measurement.
        deadline = time.monotonic() + 405
        runtime = install_public(context, args.source, args.output, deadline=deadline)
        before = installed_identity(context, read_json(args.output / 'install-report.json'), runtime)
        remaining = min(300, int(deadline - time.monotonic()))
        need(remaining > 0, 'No native work budget remains')
        operations, cleanup = run_native(context, args.output, controller, seconds=remaining)
        after = installed_identity(context, read_json(args.output / 'install-report.json'), runtime)
        need(before == after, 'Installed RECORD/native/source changed during consumer execution')
        status.update(status='passed', sourceCommit=context['binding']['sourceCommit'],
            sourceTree=context['binding']['sourceTree'], controllerFiles=context['controls'],
            qualified=context['qualified'], candidateWheel=context['binding']['candidateWheel'],
            installed=context['binding']['installed'], ownerIdentities=context['binding']['ownerIdentities'],
            cohort=context['cohort'], publication=context['publication'], runtime=runtime,
            installReportSha256=digest((args.output / 'install-report.json').read_bytes()),
            installedRecordBefore=before, installedRecordAfter=after, operations=operations, cleanup=cleanup)
    except BaseException as error:
        status['error'] = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        (args.output / 'public-tn14-receipt.json').write_bytes(canonical(status) + b'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
