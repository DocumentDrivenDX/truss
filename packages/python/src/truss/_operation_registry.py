"""Private structural registry decoding; no producer/cut/authority admission."""
COLUMNS = ('original_writer_xid','operation_ordinal','operation_kind','phase',
           'effect_generation','readiness_generation','sealed_generation','application_generation',
           'original_context_bytes_hex','original_definition_bytes_hex','original_input_bytes_hex',
           'original_prestate_bytes_hex','admitted_candidate_bytes_hex','effect_obligation_bytes_hex',
           'original_group_custody_bytes_hex','application_result_bytes_hex')
KINDS = ('mutation','import','catalog-transform','catalog-acceptance','home-migration','administrative-repair')
PHASES = {'admitted':(False,False,False,False),'effects_ready':(True,False,False,False),
          'row_sealed':(True,True,False,False),'application_finalized':(True,True,True,True)}


def _integer(value, maximum):
    if (type(value) is not str or not value or len(value)>20
            or any(c not in '0123456789' for c in value)
            or (len(value)>1 and value[0]=='0') or int(value)>maximum):
        raise ValueError('operation-registry:unavailable')


def decode_operation_registry(actual_xid, columns, rows, command, affected_rows,
                              maximum_rows, maximum_bytes):
    """Consume already admitted text/null cells; retain the complete multiset.

    Original descriptor/cycle/completion/account and same-cut proof are external.
    This does not choose a current operation or validate nested carrier meaning.
    """
    def refuse(): raise ValueError('operation-registry:unavailable')
    _integer(actual_xid, 18446744073709551615)
    for bound in (maximum_rows,maximum_bytes):
        if type(bound) is not int or not 0<=bound<=9007199254740991: refuse()
    if (type(columns) not in (tuple,list) or tuple(columns)!=COLUMNS
            or type(rows) not in (tuple,list) or len(rows)>maximum_rows
            or command!='SELECT' or type(affected_rows) is not str
            or affected_rows!=str(len(rows))): refuse()
    total=0; identities=set(); output=[]
    for row in rows:
        if type(row) not in (tuple,list) or len(row)!=16: refuse()
        values=tuple(row)
        for i,value in enumerate(values):
            if value is None:
                if i not in (5,6,7,15): refuse()
            else:
                if type(value) is not str or len(value)>maximum_bytes-total: refuse()
                # Every supported integer/kind/phase/hex carrier is ASCII.
                # Check the bound before scanning; never allocate encoded copies.
                if not value.isascii(): refuse()
                total+=len(value)
        if values[0]!=actual_xid: refuse()
        _integer(values[1],9223372036854775807)
        if values[1] in identities: refuse()
        identities.add(values[1])
        if values[2] not in KINDS: refuse()
        _integer(values[4],9223372036854775807)
        for i in (5,6,7):
            if values[i] is not None:
                _integer(values[i],9223372036854775807)
                if values[i]!=values[4]: refuse()
        for value in values[8:]:
            if value is not None and (not value or len(value)%2 or any(c not in '0123456789abcdef' for c in value)): refuse()
        expected=PHASES.get(values[3])
        if expected is None or tuple(values[i] is not None for i in (5,6,7,15))!=expected: refuse()
        output.append(values)
    return tuple(output)
