"""Public import construction from accepted native catalog identities."""
from dataclasses import dataclass
from .contracts import ProfilePin,MapValue,ExactArtifact,ObjectKeySelection
from .imports import ImportInput,ImportCatalogPin,ImportRecordInput,OwnedImportInput,OwnedImportRecordInput
from .groups import AuthoredValue,OrderKey
from ._group_runtime import _wire,_bytes,_artifact

@dataclass(frozen=True,slots=True,kw_only=True)
class ImportRuntimeContext:
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    payload_profile: ProfilePin
    catalog: ImportCatalogPin

    def input(self,records: tuple[ImportRecordInput,...],*,load_id: str,asserted_origin: MapValue) -> ImportInput:
        return ImportInput(layout_profile=self.layout_profile,import_profile=self.import_profile,value_profile=self.value_profile,
            catalog=self.catalog,load_id=load_id,asserted_origin=asserted_origin,records=records)

    def object_payload(self,values: tuple[AuthoredValue,...],*,source: MapValue | None=None) -> ExactArtifact:
        value={'interfaceVersion':'truss-import-payload/0.1.0','kind':'object','values':_wire(values),'ownership':{'state':'rootless'}}
        if source is not None:value['source']=_wire(source)
        return _artifact(_bytes(value))

    def edge_payload(self,values: tuple[AuthoredValue,...],order_key: OrderKey,*,source: MapValue | None=None) -> ExactArtifact:
        value={'interfaceVersion':'truss-import-payload/0.1.0','kind':'edge','values':_wire(values),'orderKey':_wire(order_key)}
        if source is not None:value['source']=_wire(source)
        return _artifact(_bytes(value))


@dataclass(frozen=True,slots=True,kw_only=True)
class OwnedImportRuntimeContext:
    """Explicit atomic import selection, separate from per-record imports."""
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    payload_profile: ProfilePin
    catalog: ImportCatalogPin

    def input(self,records: tuple[OwnedImportRecordInput,...],*,load_id: str,asserted_origin: MapValue) -> OwnedImportInput:
        return OwnedImportInput(layout_profile=self.layout_profile,import_profile=self.import_profile,
            value_profile=self.value_profile,catalog=self.catalog,load_id=load_id,
            asserted_origin=asserted_origin,records=records)

    def object_payload(self,values: tuple[AuthoredValue,...],*,root: ObjectKeySelection | None=None,
                       source: MapValue | None=None) -> ExactArtifact:
        ownership={'state':'rootless'} if root is None else {'state':'owned','root':_wire(root)}
        value={'interfaceVersion':'truss-owned-import-payload/0.1.0','kind':'object',
               'values':_wire(values),'ownership':ownership}
        if source is not None:value['source']=_wire(source)
        return _artifact(_bytes(value))

    def edge_payload(self,values: tuple[AuthoredValue,...],order_key: OrderKey,*,source: MapValue | None=None) -> ExactArtifact:
        value={'interfaceVersion':'truss-owned-import-payload/0.1.0','kind':'edge','values':_wire(values),'orderKey':_wire(order_key)}
        if source is not None:value['source']=_wire(source)
        return _artifact(_bytes(value))
