; benchmark generated from python API
(set-info :status unknown)
(declare-fun native_mapped_subject () String)
(declare-fun selected_subject () String)
(declare-fun mapped_effective () Int)
(declare-fun actual_effective () Int)
(declare-fun mapped_session () Int)
(declare-fun actual_session () Int)
(declare-fun role_setting_name_resolution_oid () Int)
(assert
 (let (($x15 (= selected_subject native_mapped_subject)))
 (let (($x14 (= actual_effective mapped_effective)))
 (let (($x13 (= actual_session mapped_session)))
 (and $x13 $x14 $x15)))))
(assert
 (= mapped_effective role_setting_name_resolution_oid))
(assert
 (and (distinct role_setting_name_resolution_oid actual_effective) true))
(check-sat)
