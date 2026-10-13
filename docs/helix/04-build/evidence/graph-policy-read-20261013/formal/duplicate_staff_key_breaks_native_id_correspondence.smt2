; benchmark generated from python API
(set-info :status unknown)
(declare-fun ownership_project () Int)
(declare-fun assignment_project () Int)
(declare-fun project_key (Int) String)
(declare-fun ownership_resource () Int)
(declare-fun resource_node () Int)
(declare-fun resource_key (Int) String)
(declare-fun assignment_staff () Int)
(declare-fun caller_node () Int)
(declare-fun staff_key (Int) String)
(assert
 (let (($x19 (= assignment_project ownership_project)))
 (let (($x18 (= (project_key assignment_project) (project_key ownership_project))))
 (=> $x18 $x19))))
(assert
 (let (($x24 (= resource_node ownership_resource)))
 (let (($x23 (= (resource_key resource_node) (resource_key ownership_resource))))
 (=> $x23 $x24))))
(assert
 (and (distinct caller_node assignment_staff) true))
(assert
 (let ((?x12 (staff_key assignment_staff)))
 (let ((?x11 (staff_key caller_node)))
 (= ?x11 ?x12))))
(assert
 (= assignment_project ownership_project))
(assert
 (= resource_node ownership_resource))
(assert
 (let (($x23 (= (resource_key resource_node) (resource_key ownership_resource))))
(let (($x18 (= (project_key assignment_project) (project_key ownership_project))))
(let ((?x12 (staff_key assignment_staff)))
(let ((?x11 (staff_key caller_node)))
(let (($x13 (= ?x11 ?x12)))
(let (($x27 (and $x13 $x18 $x23)))
(let (($x24 (= resource_node ownership_resource)))
(let (($x19 (= assignment_project ownership_project)))
(let (($x14 (= caller_node assignment_staff)))
(let (($x26 (and $x14 $x19 $x24)))
(and (distinct $x26 $x27) true))))))))))))
(check-sat)
