"""One configured native call and original Python report-source validation."""
import copy
import json
from test_catalog_source_candidate import ConfiguredCatalogSourceStageTests
from test_catalog_staging import ROOT
from truss._native_catalog_request import ConfiguredCatalogSelection,NativeCatalogStageInput,encode_catalog_stage
from truss._native_catalog_report_sources import compose_captured_catalog_sources
from truss._native_catalog_metadata import validate_configured_metadata


class ConfiguredCatalogStageTests(ConfiguredCatalogSourceStageTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'packages/postgresql/native/catalog-report/configured-stage.sql').read_text())
            c.run((ROOT/'packages/postgresql/native/catalog-stage-configured.sql').read_text())
        finally:c.close()

    def encoded(self, **changes):
        from dataclasses import replace
        selection=ConfiguredCatalogSelection('guard-fixture','guard-fixture-epoch',
            'guard-fixture-incarnation',b'original capture fixture',self.configuration_profile)
        return encode_catalog_stage(replace(NativeCatalogStageInput(self.prepared,b'{}',b'\x01',
            b'\x05',b'\x06',selection),**changes),'0')

    def configured(self):
        encoded=self.encoded()
        row=self.connection.run(encoded.sql)[0]
        context=bytes.fromhex(row[2]);result=json.loads(bytes.fromhex(row[3]))
        scope=json.loads(result['reportSources']['start']['empty_scope'])
        metadata=bytes.fromhex(scope['metadataUtf8Hex'])
        return encoded,row,context,result,metadata

    def test_one_original_call_and_python_composition(self):
        encoded,row,context,result,metadata=self.configured()
        snapshot=compose_captured_catalog_sources(encoded,result,context)
        self.assertEqual(json.loads(snapshot.assembly_bytes)['missingReportFields'],
                         ['reportProfile','originalExecution','assertions'])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[1]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.operation_configuration'),[[1]])
        self.assertEqual(json.loads(context)['ordinal'],'0')
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertFalse(result['accepted'])
        self.assertEqual(validate_configured_metadata(encoded,context,row[0],row[1],metadata),metadata)

    def test_hostile_rendering_settings_are_local_and_exact(self):
        self.connection.run("SET bytea_output='escape'; SET TimeZone='Pacific/Honolulu'")
        encoded,row,context,result,metadata=self.configured()
        compose_captured_catalog_sources(encoded,result,context)
        value=json.loads(metadata)
        self.assertTrue(value['epoch']['profile_bytes'].startswith('\\x'))
        self.assertTrue(value['marker']['installed_at'].endswith('+00:00'))
        self.assertEqual(self.connection.run('SHOW bytea_output'),[['escape']])
        self.assertEqual(self.connection.run('SHOW TimeZone'),[['Pacific/Honolulu']])

    def test_substituted_native_metadata_and_context_refuse(self):
        encoded,row,context,result,metadata=self.configured()
        original=json.loads(metadata)
        mutations=[('marker','installation_id','other'),('marker','layout_version','nul\0value'),('pointer','source_epoch','other'),
            ('epoch','evidence_sha256','\\x'+'00'*32),('configuration','original_context_sha256','\\x'+'00'*32),
            ('configuration','operation_ordinal',True),('admission','configuration_generation',False),
            ('admission','installed_inventory_bytes','\\x00'),
            ('epoch','profile_bytes','\\x00'),('configuration','admission_profile_bytes','\\x00')]
        for section,key,bad in mutations:
            value=copy.deepcopy(original);value[section][key]=bad
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):
                validate_configured_metadata(encoded,context,row[0],row[1],json.dumps(value).encode())
        value=copy.deepcopy(original);value['releaseArchive'].append(value['releaseArchive'][0])
        with self.assertRaises(ValueError):
            validate_configured_metadata(encoded,context,row[0],row[1],json.dumps(value).encode())
        for key in ('installationId','assertedOriginUtf8Hex','targetIncarnation','ordinal'):
            value=json.loads(context);value[key]='other'
            with self.subTest(key=key),self.assertRaises(ValueError):
                compose_captured_catalog_sources(encoded,result,json.dumps(value).encode())
        with self.assertRaises(ValueError):
            validate_configured_metadata(encoded,context,row[0],row[1],metadata.replace(b'{',b'{"interfaceVersion":"other",',1))
        for key,bad in (('artifact_bytes','\\x00'),('artifact_identity','other'),
                        ('artifact_identity_sha256','\\x'+'00'*32),('archive_row_id',True)):
            value=copy.deepcopy(original);value['releaseArchive'][0][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_configured_metadata(encoded,context,row[0],row[1],json.dumps(value).encode())
        with self.assertRaises(ValueError):
            validate_configured_metadata(encoded,context,row[0],row[1],metadata.decode().encode('utf16'))
        value=json.loads(context);value['backendPid']='2147483648'
        with self.assertRaises(ValueError):
            compose_captured_catalog_sources(encoded,result,json.dumps(value).encode())
        value=copy.deepcopy(original);value['marker']['bad\0key']='text'
        with self.assertRaises(ValueError):
            validate_configured_metadata(encoded,context,row[0],row[1],json.dumps(value).encode())

    def test_context_overflow_rolls_back_admission_before_catalog_write(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run("UPDATE truss.source_epoch_registry SET evidence_bytes=convert_to(repeat('x',2100),'UTF8')")
        self.connection.run('CREATE TEMP TABLE earlier_work(value int); INSERT INTO earlier_work VALUES(7)')
        self.connection.run('CREATE TEMP SEQUENCE first_catalog_write')
        self.connection.run("""CREATE FUNCTION truss.test_configured_write() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN PERFORM nextval('pg_temp.first_catalog_write'); RETURN NEW; END $$;
            CREATE TRIGGER test_configured_write BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.test_configured_write()""")
        self.connection.run('SAVEPOINT configured')
        with self.assertRaises(DatabaseError) as caught:self.connection.run(self.encoded().sql)
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.connection.run('ROLLBACK TO SAVEPOINT configured')
        self.assertEqual(self.connection.run('SELECT is_called FROM first_catalog_write'),[[False]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.operation_configuration'),[[0]])
        self.assertEqual(self.connection.run('SELECT value FROM earlier_work'),[[7]])

    def test_exact_context_limit_and_one_byte_evidence_overflow(self):
        from dataclasses import replace
        from pg8000.exceptions import DatabaseError
        encoded=self.encoded()
        self.connection.run('SAVEPOINT measure_context')
        row=self.connection.run(encoded.sql)[0]
        baseline=bytes.fromhex(row[2])
        self.connection.run('ROLLBACK TO SAVEPOINT measure_context')
        if len(baseline)%2:
            selection=replace(encoded.original_input.configuration,incarnation='guard-fixture-incarnationx')
            self.connection.run("UPDATE truss.source_epoch_registry SET target_incarnation='guard-fixture-incarnationx'")
            encoded=self.encoded(configuration=selection)
            row=self.connection.run(encoded.sql)[0];baseline=bytes.fromhex(row[2])
            self.connection.run('ROLLBACK TO SAVEPOINT measure_context')
            # The rollback also restores the original epoch incarnation.
            self.connection.run("UPDATE truss.source_epoch_registry SET target_incarnation='guard-fixture-incarnationx'")
        self.assertEqual(len(baseline)%2,0)
        evidence=bytes.fromhex(json.loads(baseline)['sourceEpochEvidenceHex'])
        exact=evidence+b'x'*((4096-len(baseline))//2)
        self.connection.run('UPDATE truss.source_epoch_registry SET evidence_bytes=:raw',raw=exact)
        self.connection.run('SAVEPOINT exact_context')
        row=self.connection.run(encoded.sql)[0]
        self.assertEqual(len(bytes.fromhex(row[2])),4096)
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[1]])
        self.connection.run('ROLLBACK TO SAVEPOINT exact_context')
        self.connection.run('UPDATE truss.source_epoch_registry SET evidence_bytes=:raw',raw=exact+b'x')
        self.connection.run('SAVEPOINT context_overflow')
        with self.assertRaises(DatabaseError) as caught:self.connection.run(encoded.sql)
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.connection.run('ROLLBACK TO SAVEPOINT context_overflow')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
