#!/usr/bin/env bash
# Run on Ubuntu/WSL inside the already patched Nethermind latticefold-main repo.
# Expected status: baseline ACCEPT, mu=2 control REJECT, restored baseline ACCEPT.
# This script does not install software or change your installed toolchain.
set -euo pipefail

FILE='crates/latticefold/src/nifs/folding/utils.rs'
TEST='nifs_verifier_accepts_illegal_last_digit_by_range_cancellation'
if [[ ! -f "$FILE" || ! -f 'crates/latticefold/src/nifs/attack_range_cancel_regression.rs' ]]; then
  echo 'ERROR: enter latticefold-main and apply the archived .patch first.' >&2
  exit 2
fi
if ! grep -qF 'mu_s.push(NTT::ONE);' "$FILE"; then
  echo 'ERROR: baseline mu=1 statement absent. Do not run against already modified code.' >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOGDIR="${PWD}/evidence_${STAMP}"
mkdir -p "$LOGDIR"
printf 'Rust toolchain:\n' | tee "$LOGDIR/00_env.txt"
rustc +nightly-2025-08-19 --version | tee -a "$LOGDIR/00_env.txt"
cargo +nightly-2025-08-19 --version | tee -a "$LOGDIR/00_env.txt"
sha256sum Cargo.lock "$FILE" crates/latticefold/src/nifs/attack_range_cancel_regression.rs \
  | tee -a "$LOGDIR/00_env.txt"

run_attack() {
  local dest="$1"
  cargo +nightly-2025-08-19 test --locked -p latticefold --lib "$TEST" -- --nocapture \
    2>&1 | tee "$dest"
}

echo '== 1: Ajtai deterministic short collision =='
cargo +nightly-2025-08-19 test --locked -p latticefold --lib \
  ajtai_rand_has_trivial_short_collision -- --nocapture \
  2>&1 | tee "$LOGDIR/01_ajtai_pass.log"

echo '== 2: baseline, expected ACCEPT (test passes) =='
run_attack "$LOGDIR/02_mu1_accept.log"

BACKUP="$(mktemp)"
cp "$FILE" "$BACKUP"
restore_source() {
  cp "$BACKUP" "$FILE"
  rm -f "$BACKUP"
}
trap restore_source EXIT
python3 - <<'PY2'
from pathlib import Path
p=Path('crates/latticefold/src/nifs/folding/utils.rs')
s=p.read_text()
needle='mu_s.push(NTT::ONE);'
assert s.count(needle)==1
p.write_text(s.replace(needle, 'mu_s.push(NTT::ONE + NTT::ONE);',1))
print('CONTROL: mu=2, no extra transcript challenges')
PY2

echo '== 3: mu=2 control, expected REJECT (test must panic) =='
if run_attack "$LOGDIR/03_mu2_rejected_expected_failure.log"; then
  echo 'ERROR: malicious proof ACCEPTED with mu=2; control unexpectedly passed.' >&2
  exit 1
fi
if ! grep -q 'SumCheckFailed' "$LOGDIR/03_mu2_rejected_expected_failure.log"; then
  echo 'ERROR: test failed for an unexpected reason; inspect control log.' >&2
  exit 1
fi
printf '\nEXPECTED CONTROL RESULT: rejected by SumCheckFailed\n'

restore_source
trap - EXIT

echo '== 4: original mu=1 restored, expected ACCEPT =='
run_attack "$LOGDIR/04_restored_mu1_accept.log"
echo "DONE: evidence logs are in $LOGDIR"
