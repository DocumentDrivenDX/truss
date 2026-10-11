; benchmark generated from python API
(set-info :status unknown)
(declare-fun writer_end () Real)
(declare-fun writer_start () Real)
(declare-fun reader_end () Real)
(declare-fun reader_start () Real)
(assert
 (and (< reader_start reader_end) (< writer_start writer_end)))
(assert
 (let (($x20 (<= writer_end reader_start)))
 (or (<= reader_end writer_start) $x20)))
(assert
 (<= writer_start reader_start))
(assert
 (< reader_start writer_end))
(check-sat)
