; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_visibility () (Array Int Bool))
(declare-fun complete_relevant_forbidden_facts () (Array Int Bool))
(declare-fun later_visibility () (Array Int Bool))
(assert
 (exists ((fact Int) )(let (($x15 (select original_visibility fact)))
 (let (($x11 (select complete_relevant_forbidden_facts fact)))
 (and $x11 $x15))))
 )
(assert
 (let (($x31 (exists ((fact Int) )(let (($x11 (select complete_relevant_forbidden_facts fact)))
(and $x11 (select later_visibility fact))))
))
(not $x31)))
(check-sat)
