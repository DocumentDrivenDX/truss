"""Conforming candidate for original UMF required set-Field literal semantics.

Only owner-prepared Boolean/Integer/String Fields; no native admission. Retain
original literal spelling outside this evaluator. Equality below is mathematical.
"""
from decimal import Decimal
import re


class SetValueRefusal(ValueError):
    pass


def _decimal_digits(digits):
    """Exact balanced conversion without a process-global int-string override."""
    if len(digits)<=256:
        return int(digits or '0')
    middle=len(digits)//2
    return _decimal_digits(digits[:middle])*10**(len(digits)-middle)+_decimal_digits(digits[middle:])


def _integer(token):
    if type(token) is not str:
        raise SetValueRefusal('Exact original integer token required')
    m=re.fullmatch(r'(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?',token)
    if not m:
        raise SetValueRefusal('Exact JSON integer token refused')
    digits=(m[2]+(m[3] or '')).lstrip('0')
    if not digits:
        return 0
    exponent=m[4] or '0'
    if len(exponent)>32:
        raise SetValueRefusal('Original numeric exponent bound exceeded')
    shift=int(exponent)-len(m[3] or '')
    if shift<0:
        cut=-shift
        if cut>len(digits) or any(c!='0' for c in digits[len(digits)-cut:]):
            raise SetValueRefusal('Integer token would require rounding')
        digits=digits[:len(digits)-cut]
    else:
        if len(digits)+shift>4000000:
            raise SetValueRefusal('Original numeric expansion bound exceeded')
    # Preserve compact exponents; Decimal.as_integer_ratio on millions of
    # expanded digits can spend nearly the complete native operation deadline.
    value=_decimal_digits(digits)
    if shift>0:
        value*=10**shift
    return -value if m[1] else value


def _metadata_integer(value):
    if type(value) is int:return value
    if type(value) is Decimal and value.is_finite() and 1 <= value <= 9007199254740991:
        numerator,denominator=value.as_integer_ratio()
        if denominator==1:return numerator
    raise SetValueRefusal('Exact integral original metadata required')


def _closed(value, names):
    if type(value) is not dict or any(k not in names for k in value):
        raise SetValueRefusal('Unknown relevant Field meaning')


def _identity(family,literal):
    wrapper={'boolean':'boolean','integer':'integerToken','string':'string'}[family]
    if type(literal) is not dict or set(literal)!={wrapper}:
        raise SetValueRefusal('Exactly one original typed literal required')
    value=literal[wrapper]
    if family=='integer':return _integer(value)
    if family=='boolean':
        if type(value) is not bool:raise SetValueRefusal('Boolean literal required')
    else:
        if type(value) is not str:raise SetValueRefusal('String literal required')
        try:value.encode('utf-8',errors='strict')
        except UnicodeError:raise SetValueRefusal('Unicode scalar string required') from None
    return value


def check_set_literal(field,literal):
    """No schema/model resolver: caller must supply the exact owner-prepared Field."""
    if type(field) is not dict or field.get('kind')!='field' or field.get('cardinality')!='one' or field.get('nullability')!='required':
        raise SetValueRefusal('Original required one-valued Field needed')
    family=field.get('scalarType')
    if family not in ('boolean','integer','string') or field.get('extensions') or field.get('itemType') or any(r.get('role')=='record-type' for r in field.get('references',[])):
        raise SetValueRefusal('Outside original first set-value domain')
    facets=field.get('facets',{})
    _closed(facets,{'integerWidth','range'} if family=='integer' else {'length'} if family=='string' else set())
    value=_identity(family,literal)
    if 'integerWidth' in facets:
        width=facets['integerWidth'];_closed(width,{'bits','signed'})
        bits=_metadata_integer(width.get('bits'));signed=width.get('signed')
        if type(bits) is not int or not 1<=bits<=9007199254740991 or type(signed) is not bool:
            raise SetValueRefusal('Original integer width missing')
        magnitude=abs(value);size=magnitude.bit_length()
        fits=(size<bits if value>=0 else size<bits or (size==bits and magnitude&(magnitude-1)==0)) if signed else value>=0 and size<=bits
        if not fits:raise SetValueRefusal('Integer outside original width')
    if 'range' in facets:
        bounds=facets['range'];_closed(bounds,{'min','max','minInclusive','maxInclusive'})
        for end in ('min','max'):
            if end in bounds:
                bound=_identity(family,bounds[end])
                if (value<bound if end=='min' else value>bound) or value==bound and bounds.get(end+'Inclusive') is False:
                    raise SetValueRefusal('Integer outside original range')
    if 'length' in facets:
        length=facets['length'];_closed(length,{'min','max','unit'})
        if length.get('unit')!='unicode-scalar':raise SetValueRefusal('Original Unicode length unit required')
        if 'min' in length and len(value)<length['min'] or 'max' in length and len(value)>length['max']:
            raise SetValueRefusal('String outside original scalar length')
    if 'allowedValues' in field:
        if not any(_identity(family,candidate)==value for candidate in field['allowedValues']):
            raise SetValueRefusal('Literal outside original allowed values')
