"""Authority receipt inclusion in the caller's original read transaction."""
from dataclasses import dataclass,field
from typing import Literal
from .contracts import ProfilePin

@dataclass(frozen=True,slots=True,kw_only=True)
class ReceiptIncluded:
    included: bool
    comparison_profile: ProfilePin
    interface_version: Literal['truss-receipt-visibility-result/0.1.0']=field(default='truss-receipt-visibility-result/0.1.0',init=False)
    outcome: Literal['available']=field(default='available',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class ReceiptVisibilityUnavailable:
    reason: Literal['authorization','epoch_profile','retention','observation_integrity','resource','invalid_token']
    interface_version: Literal['truss-receipt-visibility-result/0.1.0']=field(default='truss-receipt-visibility-result/0.1.0',init=False)
    outcome: Literal['unavailable']=field(default='unavailable',init=False)
