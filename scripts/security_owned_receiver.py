"""Owned fixed semantic receiver candidate; no authenticated public endpoint."""
import json,hashlib
from truss.psycopg_host import PsycopgHost
from truss.execution import TransactionHandle
from truss._psycopg_epoch_cut import _EpochComparison
from truss._psycopg_dependency_fact_cut import _OriginalFactSources,_inspect_original_fact_sources,_epoch_dependency_recipe
from security_owned_read import run_delegated_owned_identity_read


class _OwnedDecisionReceiver:
    __slots__=('__scope',)
    def __init__(self,caller_host,caller_transaction,executor_host,executor_transaction,epoch,requirements,sources):
        if (type(caller_host) is not PsycopgHost or type(executor_host) is not PsycopgHost
                or type(caller_transaction) is not TransactionHandle or type(executor_transaction) is not TransactionHandle
                or type(epoch) is not _EpochComparison or type(requirements) is not bytes or type(sources) is not _OriginalFactSources):
            raise ValueError('Original owned receiver context required')
        selected=_EpochComparison(epoch.installation,epoch.epoch,epoch.incarnation,epoch.profile,epoch.evidence)
        captured=_OriginalFactSources(sources.policy,sources.resolution)
        digest=hashlib.sha256(requirements).hexdigest()
        _inspect_original_fact_sources(requirements,digest,captured)
        selected,_=_epoch_dependency_recipe(selected,digest,captured)
        if json.loads(selected.profile)['kind']!='truss-flat-fact-provider-fixture/0.4':
            raise ValueError('Original delegated receiver profile required')
        self.__scope=(caller_host,caller_transaction,executor_host,executor_transaction,selected,requirements,captured)

    def dispatch(self,request):
        def refuse(*args):raise ValueError('Owned semantic request refused')
        if type(request) is not bytes or not 1<=len(request)<=1024:refuse()
        def pairs(entries):
            result={}
            for key,value in entries:
                if key in result:refuse()
                result[key]=value
            return result
        try:
            value=json.loads(request.decode('utf8'),object_pairs_hook=pairs,parse_constant=refuse)
        except (ValueError,UnicodeError,RecursionError):refuse()
        if (type(value) is not dict or set(value)!={'interfaceVersion','operation'}
                or type(value['interfaceVersion']) is not str or value['interfaceVersion']!='truss-owned-decision-request/0.1'
                or type(value['operation']) is not str or value['operation']!='read'):refuse()
        return run_delegated_owned_identity_read(*self.__scope)
