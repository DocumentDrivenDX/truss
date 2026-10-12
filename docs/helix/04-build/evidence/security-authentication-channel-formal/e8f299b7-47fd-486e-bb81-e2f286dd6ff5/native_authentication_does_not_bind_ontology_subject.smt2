; benchmark generated from python API
(set-info :status unknown)
(declare-fun authenticated_original () Bool)
(declare-fun original_session_authentication_end () Bool)
(declare-fun credential_at_new_login () Bool)
(declare-fun required_at_new_login () Bool)
(declare-fun authenticated_new () Bool)
(declare-fun credential_at_login () Bool)
(declare-fun required_at_login () Bool)
(declare-fun accepted_new () Bool)
(declare-fun accepted_original () Bool)
(declare-fun independent_ontology_subject_binding () Bool)
(assert
 (let (($x26 (= original_session_authentication_end authenticated_original)))
 (let (($x25 (= authenticated_new (and required_at_new_login credential_at_new_login))))
 (let (($x23 (= authenticated_original (and required_at_login credential_at_login))))
 (let (($x21 (= accepted_new (or (not required_at_new_login) credential_at_new_login))))
 (let (($x18 (= accepted_original (or (not required_at_login) credential_at_login))))
 (and $x18 $x21 $x23 $x25 $x26)))))))
(assert
 authenticated_original)
(assert
 (not independent_ontology_subject_binding))
(check-sat)
