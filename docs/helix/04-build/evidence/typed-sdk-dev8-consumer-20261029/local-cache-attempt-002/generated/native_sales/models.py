# SPDX-License-Identifier: MIT OR Apache-2.0
# Generated from pinned UMF inputs. Regenerate; do not edit.
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, ClassVar, TYPE_CHECKING, TypeVar, final
from pydantic import BeforeValidator, TypeAdapter
from umf_access.dsl import FieldRef, GeneratedSource
from umf_access.types import MISSING, StrictModel, Vector
from umf_access.values import validate_integer, validate_decimal, validate_string, validate_date, validate_instant, validate_local, validate_boolean, validate_binary, validate_length, validate_range, validate_allowed, validate_vector, validate_float32, FieldValidator
_AliasTag = TypeVar("_AliasTag")
UMF_GENERATED_SOURCE = GeneratedSource(document_id="truss-typed-sdk-0052-consumer-fixture", core_version="0.10.0", document_sha256="8a243c3eb6980c3528d490487220bff26ca6f5481b6b7d19ee71439fc5e4b7f4", input_digest="2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474", runtime_abi="umf-access-runtime/0.1")
if TYPE_CHECKING:
    from .fields import OrderColumns, OrderQuery, OrderAlias
    from .fields import CustomerColumns, CustomerQuery, CustomerAlias

validate_field__modules_0_extensions_umf_access_views_0_fields_0 = FieldValidator(kind="string")

validate_field__modules_0_extensions_umf_access_views_0_fields_1 = FieldValidator(kind="string")

validate_field__modules_0_extensions_umf_access_views_1_fields_0 = FieldValidator(kind="string")

validate_field__modules_0_extensions_umf_access_views_1_fields_1 = FieldValidator(kind="string")

@final
class Order(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    c: ClassVar[OrderColumns]
    objects: ClassVar[OrderQuery]
    @classmethod
    def alias(cls, tag: type[_AliasTag]) -> OrderAlias[_AliasTag]:
        from .fields import OrderAlias
        return OrderAlias(tag)
    id: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_0_fields_0)]
    status: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_0_fields_1)]
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "id", "id"), ("sales", "status", "status"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

@final
class OrderCreate(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    id: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_0_fields_0)]
    status: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_0_fields_1)]
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "id", "id"), ("sales", "status", "status"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

@final
class OrderPatch(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    status: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_0_fields_1)] | MISSING = MISSING
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "status", "status"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

@final
class OrderIdentity(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    UMF_PROJECTION_OWNER: ClassVar[type[Order]] = Order
    @classmethod
    def _umf_projection_model(cls) -> type[OrderIdentity]:
        return cls
    UMF_PROJECTION_FIELDS: ClassVar[tuple[FieldRef, ...]] = (FieldRef(source=UMF_GENERATED_SOURCE, module="sales", element="order", field="id", field_module="sales", logical_name="id"),)
    id: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_0_fields_0)]
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "id", "id"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

@final
class Customer(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    c: ClassVar[CustomerColumns]
    objects: ClassVar[CustomerQuery]
    @classmethod
    def alias(cls, tag: type[_AliasTag]) -> CustomerAlias[_AliasTag]:
        from .fields import CustomerAlias
        return CustomerAlias(tag)
    customer_id: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_1_fields_0)]
    customer_name: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_1_fields_1)]
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "customerId", "customer_id"), ("sales", "customerName", "customer_name"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

@final
class CustomerCreate(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    customer_id: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_1_fields_0)]
    customer_name: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_1_fields_1)]
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "customerId", "customer_id"), ("sales", "customerName", "customer_name"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

@final
class CustomerPatch(StrictModel):
    UMF_SOURCE: ClassVar[GeneratedSource] = UMF_GENERATED_SOURCE
    customer_name: Annotated[str, BeforeValidator(validate_field__modules_0_extensions_umf_access_views_1_fields_1)] | MISSING = MISSING
    UMF_FIELDS: ClassVar[tuple[tuple[str, str, str], ...]] = (("sales", "customerName", "customer_name"),)
    UMF_BUNDLE_INPUT_DIGEST: ClassVar[str] = "2afe420d9ceb17774b788653c3634fa00633e7f365194fd6d9b13aeaa5669474"
    UMF_RUNTIME_ABI: ClassVar[tuple[str, str, str]] = ("umf_access", "0.1.0.dev8", "umf-access-runtime/0.1")
    UMF_FINAL: ClassVar[bool] = True

OrderIdentity.model_rebuild()
__all__ = ["Order", "OrderCreate", "OrderPatch", "Customer", "CustomerCreate", "CustomerPatch", "OrderIdentity"]
