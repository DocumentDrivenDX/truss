import unittest
from truss.contracts import ProfilePin, QualifiedOwner
from truss.catalog_view import (CatalogViewLimits, CatalogViewRequest,
    CurrentCatalogSelection, HistoricalCatalogSelection, CompleteCatalogScope,
    ProjectedCatalogScope, CatalogDefinitionReference)


class CatalogViewContractTests(unittest.TestCase):
    def test_exact_request_shape_preserves_large_budget_and_revision_text(self):
        pin=ProfilePin(identity='example',version='1',sha256='a'*64)
        request=CatalogViewRequest(layout_profile=pin,view_profile=pin,
            selection=HistoricalCatalogSelection(catalog_revision='9007199254740993'),
            scope=CompleteCatalogScope(),limits=CatalogViewLimits(
                definition_count='9007199254740993',encoded_bytes='1048576'))
        self.assertEqual(request.selection.catalog_revision,'9007199254740993')
        self.assertEqual(request.interface_version,'truss-catalog-view-request/0.1.0')

    def test_budget_refuses_host_numbers_and_noncanonical_tokens(self):
        for value in (1,True,'','0','01','-1','1.0','1e2','١'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                CatalogViewLimits(definition_count=value,encoded_bytes='1')

    def test_projection_refuses_empty_and_duplicate_owners(self):
        a=QualifiedOwner(document_id='a',module_id='m')
        b=QualifiedOwner(document_id='b',module_id='m')
        for owners in ((),(a,a)):
            with self.assertRaises(ValueError):ProjectedCatalogScope(owners=owners)
        self.assertEqual(ProjectedCatalogScope(owners=(a,b)).owners,(a,b))

    def test_selection_rejects_untyped_substitutes(self):
        pin=ProfilePin(identity='example',version='1',sha256='a'*64)
        with self.assertRaises(ValueError):
            CatalogViewRequest(layout_profile=pin,view_profile=pin,
                selection={'kind':'current'},scope=CompleteCatalogScope(),
                limits=CatalogViewLimits(definition_count='1',encoded_bytes='1'))
        for value in ('','01','-1','1.0','١'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                HistoricalCatalogSelection(catalog_revision=value)
    def test_reference_variants_require_exact_identity_fields(self):
        base={'definition_pin':'a'*64,'owner':QualifiedOwner(document_id='d',module_id='m'),'authored_identity':'a'}
        for values in ({'kind':'key'}, {'kind':'type','type_id':'1','property_id':'2'},
                       {'kind':'relationship','relationship_id':'01'}, {'kind':'property','type_id':'1'}):
            with self.subTest(values=values),self.assertRaises(ValueError):CatalogDefinitionReference(**base,**values)
        self.assertEqual(CatalogDefinitionReference(**base,kind='key',type_id='1',key_number='2').key_number,'2')


if __name__=='__main__':unittest.main()
