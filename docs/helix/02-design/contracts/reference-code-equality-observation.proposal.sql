-- Private reference candidate; not executed or installed.
-- Two already-admitted non-null exact Unicode scalar strings, excluding U+0000.
-- Full original Field/home/source custody and resource/transport preflight precede this call.
-- Native resolution of text, equality, C collation and bool-to-text cast must be observed.
SELECT (($1::pg_catalog.text COLLATE pg_catalog."C")
        OPERATOR(pg_catalog.=)
        ($2::pg_catalog.text COLLATE pg_catalog."C"))::pg_catalog.text
       AS equal_text;
