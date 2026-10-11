; benchmark generated from python API
(set-info :status unknown)
(declare-fun writer_end () Real)
(declare-fun writer_start () Real)
(declare-fun reader_end () Real)
(declare-fun reader_start () Real)
(declare-fun role_effect () Real)
(assert
 (and (< reader_start reader_end) (< writer_start writer_end)))
(assert
 (and (<= writer_start role_effect) (< role_effect writer_end)))
(assert
 (or (<= reader_end writer_start) (<= writer_end reader_start)))
(assert
 (and (<= reader_start role_effect) (< role_effect reader_end)))
(check-sat)
