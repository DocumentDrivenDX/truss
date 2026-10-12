; benchmark generated from python API
(set-info :status unknown)
(declare-fun mapped_session () Int)
(declare-fun actual_session () Int)
(declare-fun role_setting_name_resolution_oid () Int)
(declare-fun mapped_effective () Int)
(declare-fun actual_effective () Int)
(assert
 (= actual_session mapped_session))
(assert
 (= mapped_effective role_setting_name_resolution_oid))
(assert
 (and (distinct role_setting_name_resolution_oid actual_effective) true))
(check-sat)
