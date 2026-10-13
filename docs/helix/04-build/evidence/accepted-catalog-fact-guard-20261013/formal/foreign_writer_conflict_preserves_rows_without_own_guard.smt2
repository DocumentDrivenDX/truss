; benchmark generated from python API
(set-info :status unknown)
(declare-sort SelectedFactRow 0)
(declare-fun operation () Int)
(declare-fun continuously_held_cut () Bool)
(declare-fun same_backend () Bool)
(declare-fun before () (Array Int SelectedFactRow))
(declare-fun value () SelectedFactRow)
(declare-fun absent () SelectedFactRow)
(declare-fun key () Int)
(declare-fun installed_before_effect_guard () Bool)
(assert
 (>= operation 0))
(assert
 (<= operation 3))
(assert
 continuously_held_cut)
(assert
 (not same_backend))
(assert
 (let ((?x24 (ite (= operation 3) ((as const (Array Int SelectedFactRow)) absent) (store before key (ite (= operation 2) absent value)))))
(let (($x13 (not continuously_held_cut)))
(let (($x16 (or $x13 (and same_backend (not installed_before_effect_guard)))))
(let ((?x25 (ite $x16 ?x24 before)))
(and (distinct ?x25 before) true))))))
(check-sat)
