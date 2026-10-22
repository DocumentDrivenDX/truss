# Hosted Chromium apt bootstrap repair — 2026-10-22

## Original failure

Conformance run [39821070162](https://github.com/DocumentDrivenDX/weft/actions/runs/39821070162), job 119972301845, checked out Weft integration `aa37e57e3083fd22390796fd08dac1c9f7df6d2b` on hosted image `ubuntu24/20261021.345` (`20261021.345.10`). The `Install actual Chromium and system dependencies` step exited before `apt-get update` or Playwright ran, with `No official Ubuntu archive/security source URI was found`. The unchanged original job log is retained as `original-run-39821070162-job-119972301845.log`, SHA-256 `e381fcbc865c38210f66000c44d3ab65ee96fa6b1df23d757fcce53363f8589b`.

The failure was a bootstrap assumption mismatch: the previous workflow recognized direct Ubuntu URLs, while this runner image's official `configure-apt-sources.sh` configures `ubuntu.sources` with `mirror+file:/etc/apt/apt-mirrors.txt`. The exact runner-image source is [configure-apt-sources.sh at ubuntu24/20261021.345](https://github.com/actions/runner-images/blob/ubuntu24/20261021.345/images/ubuntu/scripts/build/configure-apt-sources.sh), blob SHA-1 `b3f5b2b180df8eb39fcbba034f616e03a69e775c`. The reviewed source uses that exact selector and provides HTTPS `archive.ubuntu.com` and `security.ubuntu.com` candidates; the workflow does not resolve or read the referenced file.

## Repair and local checks

The focused, reviewed Weft integration change is commit `cc694344da31af76ef6b97e572d20a8347989bdd`. A shared helper now recognizes only the exact runner selector, maps non-security and security suites to the corresponding official HTTPS hosts, preserves source options such as `Signed-By`, and leaves third-party and lookalike/unknown references untouched. Both `conformance.yml` and `fresh-hosts.yml` call it. The apt bounds use `zz-weft-network-bounds`, after the image's `zz-retries`, and the workflow asserts the effective retries and HTTP/HTTPS timeout values with `apt-config dump` before the bounded package update.

Local checks on macOS passed:

- `python3 .github/scripts/configure_ubuntu_apt_sources.py --self-test`
- `PYTHONPYCACHEPREFIX=/private/tmp/arras-apt-pycache python3 -m py_compile .github/scripts/configure_ubuntu_apt_sources.py`
- YAML parsing and `bash -n` on the extracted Chromium setup step in both workflows
- `git diff --check`

The fixture suite covers the runner-image source shape, suite mapping, `Signed-By` and third-party preservation, exact-token lookalikes, unknown paths, and idempotence. These checks do not establish execution on Ubuntu or successful Chromium installation.

## Retry status and limits

Hosted conformance run [39822650250](https://github.com/DocumentDrivenDX/weft/actions/runs/39822650250) is still in progress. Its compiler-and-evidence job reports the Chromium bootstrap step (step 6) completed successfully, as well as locked JavaScript dependency installation (step 7). This step runs the effective apt-config assertions, bounded apt update, pinned Playwright/Chromium installation, and Chromium launch smoke. The structured GitHub Actions status snapshot is `retry-status-20261022T172905Z.json`. At that observation the job was installing the pinned browser binding builder; later compiler, native, WASM parity and qualification steps were still pending. This qualifies the bootstrap repair on the hosted Ubuntu image, not the complete hosted conformance run. Do not claim the run or release gates passed until the overall workflow completes successfully. The original failure log above remains byte-identical. Compiler source, release build inputs, and published artifacts were not changed by the workflow repair.
