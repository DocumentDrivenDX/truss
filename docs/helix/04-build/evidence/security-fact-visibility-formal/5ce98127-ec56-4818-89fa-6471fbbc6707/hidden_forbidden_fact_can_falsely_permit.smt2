; benchmark generated from python API
(set-info :status unknown)
(declare-fun complete_relevant_forbidden_facts () (Array Int Bool))
(declare-fun original_visibility () (Array Int Bool))
(assert
 (exists ((fact Int) )(select complete_relevant_forbidden_facts fact))
 )
(assert
 (let (($x27 (exists ((fact Int) )(let (($x15 (select original_visibility fact)))
(let (($x11 (select complete_relevant_forbidden_facts fact)))
(and $x11 $x15))))
))
(not $x27)))
(check-sat)
