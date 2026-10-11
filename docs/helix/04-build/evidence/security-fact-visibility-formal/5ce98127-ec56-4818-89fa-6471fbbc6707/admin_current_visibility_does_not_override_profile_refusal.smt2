; benchmark generated from python API
(set-info :status unknown)
(declare-fun force_row_security () Bool)
(declare-fun row_security_enabled () Bool)
(declare-fun admitted_plain_profile () Bool)
(declare-fun admin_observes_all_rows () Bool)
(assert
 (= admitted_plain_profile (and (not row_security_enabled) (not force_row_security))))
(assert
 admin_observes_all_rows)
(assert
 row_security_enabled)
(assert
 admitted_plain_profile)
(check-sat)
