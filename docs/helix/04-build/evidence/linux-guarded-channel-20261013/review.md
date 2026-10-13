# Independent Astra Ultra evidence review

The existing Astra candidate-review agent checked the retained logs, source
correspondence and qualification scope. All 906 retained Weft file hashes match
commit 6fc0a279; mounted UMF is clean at 7c0f0c98; the native tests, channel
implementation and runtime 0.51 manifest correspond to Truss bd8ad3da.
No scope or behavior mismatch was found.

The reviewer requested retained observations for the asserted release-wheel
checksum, tool versions and locked build command. Added
pgserver-release-checksum.txt (original release entry and observed SHA256 match),
tool-versions.log (actual Python/rustc/maturin output) and build-command.txt
(recorded original build invocation). No native rerun was requested.
