; benchmark generated from python API
(set-info :status unknown)
(declare-fun login_name_at_publication () String)
(declare-fun original_native_authentication () String)
(declare-fun final_role_oid_matches () Bool)
(declare-fun native_authentication_present () Bool)
(declare-fun original_guards_retained () Bool)
(declare-fun original_semantic_permit () Bool)
(declare-fun executor_invoked () Bool)
(declare-fun decision_published () Bool)
(declare-fun login_name_at_admission () String)
(declare-fun entry_role_oid_matches () Bool)
(declare-fun original_source_cut () Bool)
(assert
 (let (($x23 (= original_native_authentication (str.++ "scram-sha-256:" login_name_at_publication))))
 (let (($x24 (and native_authentication_present final_role_oid_matches $x23)))
 (let (($x27 (and executor_invoked original_semantic_permit original_guards_retained $x24)))
 (let (($x20 (= original_native_authentication (str.++ "scram-sha-256:" login_name_at_admission))))
 (let (($x21 (and native_authentication_present entry_role_oid_matches $x20)))
 (and (= executor_invoked (and original_source_cut $x21)) (= decision_published $x27))))))))
(assert
 entry_role_oid_matches)
(assert
 final_role_oid_matches)
(assert
 (= original_native_authentication (str.++ "scram-sha-256:" login_name_at_admission)))
(assert
 (and (distinct login_name_at_admission login_name_at_publication) true))
(assert
 decision_published)
(check-sat)
