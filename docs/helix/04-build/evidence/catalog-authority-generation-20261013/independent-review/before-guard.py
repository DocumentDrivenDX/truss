def guard(cursor):
    cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1 FOR SHARE NOWAIT', prepare=False)
    if cursor.fetchmany(2) != [expected_guard]:
        raise ValueError('Original current native authority comparison required')
