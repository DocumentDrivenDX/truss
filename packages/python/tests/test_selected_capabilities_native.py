# SPDX-License-Identifier: MIT OR Apache-2.0
"""One adopter workflow through real selected public capability objects."""
from dataclasses import replace
import psycopg
from truss import (Ok,Error,CapabilityAvailable,CatalogUnchanged,ObjectFound,ObjectPage)
from truss.groups import GroupSuccess,UpdateObject,StoredObjectReference
from truss.contracts import MapValue
from truss.imports import ImportReported
import test_object_mutations_native as mutation_tests


class SelectedCapabilityTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_select_register_create_lookup_update_import_and_dispose(self):
        connection,host,assembly,tx=self.ready()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        self.assertIs(assembly.catalog(),assembly)
        catalog_result=assembly.catalog(assembly.catalog_selection)
        self.assertIsInstance(catalog_result,CapabilityAvailable);catalog=catalog_result.capability
        self.assertEqual(catalog.selection,assembly.catalog_selection)
        prepared=catalog.prepare_catalog(self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(catalog.accept_in_transaction(tx,prepared,request_key='selected-unchanged').value,CatalogUnchanged)
        self.assertEqual(catalog.report_in_transaction(tx).value.revision,1)
        self.assertEqual(catalog.accepted_document_in_transaction(tx,document_id='adoc').value.document_revision,'r1')
        reader_result=assembly.direct_reads(assembly.direct_read_selection)
        self.assertIsInstance(reader_result,CapabilityAvailable);reader=reader_result.capability
        groups=assembly.groups(assembly.group_selection,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').capability
        context=assembly.group_context_in_transaction(tx).value
        created=groups.apply_in_transaction(tx,context.input((self.create(),),MapValue(entries=())),context.request('selected-create'))
        self.assertIsInstance(created.value,GroupSuccess)
        found=reader.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','one'),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(found.value,ObjectFound)
        updated=groups.apply_in_transaction(tx,context.input((UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(),unset=()),),MapValue(entries=())),context.request('selected-noop'))
        self.assertIsInstance(updated.value,GroupSuccess)
        self.assertIsInstance(reader.page_objects_in_transaction(tx,document_id='adoc',module_id='m',record_id='A').value,ObjectPage)
        importer_result=assembly.imports(assembly.import_selection,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(importer_result,CapabilityAvailable);importer=importer_result.capability
        import_context=importer.import_context_in_transaction(tx).value
        record=importer.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='B',values=self.create(label='imported',value='imported',record='B').values).value
        imported=importer.import_in_transaction(tx,import_context.input((record,),load_id='selected-import',asserted_origin=MapValue(entries=())))
        self.assertIsInstance(imported,ImportReported)
        bad=replace(assembly.direct_read_selection,value_profile=replace(assembly.direct_read_selection.value_profile,sha256='0'*64))
        self.assertEqual(assembly.direct_reads(bad).reason,'selection')
        assembly.dispose()
        self.assertEqual(assembly.direct_reads(assembly.direct_read_selection).reason,'disposed')
        self.assertIsInstance(reader.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=found.value.object.id),Error)
        self.assertIsInstance(catalog.report_in_transaction(tx),Error)
        self.assertIsInstance(importer.import_context_in_transaction(tx),Error)
        host.detach();connection.commit()
