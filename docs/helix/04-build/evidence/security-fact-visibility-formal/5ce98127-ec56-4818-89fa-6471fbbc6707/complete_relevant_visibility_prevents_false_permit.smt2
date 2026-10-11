; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_visibility () (Array Int Bool))
(declare-fun complete_relevant_forbidden_facts () (Array Int Bool))
(assert
 (forall ((fact Int) )(let (($x15 (select original_visibility fact)))
 (let (($x11 (select complete_relevant_forbidden_facts fact)))
 (=> $x11 $x15))))
 )
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
