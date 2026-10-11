"""Private complete fixture dependency cuts; comparisons do not confer authority.

UMF owns semantic traversal. This composes original dependency coverage with
native recipes, not authenticated mapping/decoder qualification or policy execution.
"""
from dataclasses import dataclass
from ._security_fact_coverage import _FactBindingDeclaration, _inspect_fact_coverage
from ._psycopg_fact_cut import _FactColumnComparison, _FactRelationComparison, _run_fenced_fact_operation


@dataclass(frozen=True)
class _DependencyFactProvider:
    kind: str
    reference: tuple
    relation: _FactRelationComparison
    column: _FactColumnComparison | None = None


def _run_dependency_fact_operation(host, transaction, epoch, original_bytes,
                                   expected_sha256, providers, callback):
    if type(providers) is not tuple or not 1<=len(providers)<=8192:
        raise ValueError('Bounded original dependency provider tuple required')
    declarations=[]; relations={}
    for index,provider in enumerate(providers):
        if type(provider) is not _DependencyFactProvider:
            raise ValueError('Exact dependency provider comparison required')
        kind,reference,relation,column=provider.kind,provider.reference,provider.relation,provider.column
        if type(relation) is not _FactRelationComparison or type(relation.columns) is not tuple:
            raise ValueError('Exact original fact relation required')
        if kind=='field':
            if type(column) is not _FactColumnComparison:raise ValueError('Field column comparison required')
        elif kind=='association':
            if column is not None:raise ValueError('Association table presence comparison required')
        else:raise ValueError('Original dependency kind required')
        declarations.append(_FactBindingDeclaration(kind,reference,str(index)))
        # Copy comparison primitives before any host/native invocation. No issuer
        # or semantic relationship is inferred from relation/column names.
        base=(relation.schema,relation.name,relation.oid,relation.owner_oid,relation.guard_source)
        columns=relation.columns+((column,) if column is not None else ())
        copied=[]
        for c in columns:
            if type(c) is not _FactColumnComparison:raise ValueError('Exact original field descriptor required')
            copied.append(_FactColumnComparison(c.name,c.number,c.type_oid,c.type_modifier,c.not_null,c.collation_oid,c.generated,c.identity))
        if type(base[2]) is not int:raise ValueError('Exact native relation identity required')
        prior=relations.get(base[2])
        if prior is not None and prior[0]!=base:raise ValueError('Conflicting original relation comparisons')
        combined=(() if prior is None else prior[1])+tuple(copied)
        unique=[]
        for c in combined:
            if c not in unique:unique.append(c)
        relations[base[2]]=(base,tuple(unique))
    coverage=_inspect_fact_coverage(original_bytes,expected_sha256,tuple(declarations))
    if coverage.missing:raise ValueError('Incomplete original semantic dependency provider coverage')
    recipe=tuple(_FactRelationComparison(*base,columns) for base,columns in relations.values())
    return _run_fenced_fact_operation(host,transaction,epoch,recipe,callback)
