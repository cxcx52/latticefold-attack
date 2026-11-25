#!/usr/bin/env bash
# Nethermind LatticeFold: fixed mu=2, adaptive payload (+5,-4), end-to-end PoC.
# Works on a FRESH, isolated copy of the supplied source ZIP. Does not modify
# the user's existing ~/latticefold-audit/latticefold-main working directory.
set -Eeuo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$PACKAGE_DIR/../.." && pwd)"
SOURCE_ZIP="$REPO_ROOT/vendor/nethermind-latticefold-snapshot.zip"
BASE_PATCH="$REPO_ROOT/latticefold/nethermind/range_cancellation.patch"
OUT_PARENT="${LATTICEFOLD_AUDIT_ROOT:-$HOME/latticefold-audit}"
TOOLCHAIN="nightly-2025-08-19"
TEST_NAME="nifs_verifier_accepts_illegal_last_digit_by_range_cancellation"

for bin in cargo git unzip python3 tee grep sha256sum; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        printf 'ERROR: missing command: %s\n' "$bin" >&2
        exit 2
    fi
done
for fn in \
    "$SOURCE_ZIP" \
    "$BASE_PATCH" \
    "$PACKAGE_DIR/adaptive_payload.patch" \
    "$PACKAGE_DIR/strong_assertions.patch" \
    "$PACKAGE_DIR/fixed_mu2_sumcheck_model.py"; do
    if [[ ! -f "$fn" ]]; then
        printf 'ERROR: required file not found: %s\n' "$fn" >&2
        exit 2
    fi
done

mkdir -p "$OUT_PARENT"
LAB_DIR="$(mktemp -d "$OUT_PARENT/mu2-e2e.XXXXXXXX")"
printf '=== ISOLATED TEST DIR ===\n%s\n' "$LAB_DIR"
printf '%s\n' "$LAB_DIR" > "$OUT_PARENT/LAST_MU2_E2E_DIR.txt"

sha256sum "$SOURCE_ZIP" "$BASE_PATCH" \
  "$PACKAGE_DIR/adaptive_payload.patch" \
  "$PACKAGE_DIR/strong_assertions.patch" \
  > "$LAB_DIR/SHA256_INPUTS.txt"

{
  date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
  printf 'Package: %s\n' "$PACKAGE_DIR"
  cargo +"$TOOLCHAIN" --version
  rustc +"$TOOLCHAIN" --version
} > "$LAB_DIR/ENVIRONMENT.txt"

printf '\n[0/4] Verify exact algebraic claim (does NOT substitute for Rust test)\n'
python3 "$PACKAGE_DIR/fixed_mu2_sumcheck_model.py" \
    2>&1 | tee "$LAB_DIR/00_algebra.log"

printf '\n[1/4] Apply all three patches in a new source directory\n'
unzip -q "$SOURCE_ZIP" -d "$LAB_DIR"
cd "$LAB_DIR/latticefold-main"
for patch in \
    "$BASE_PATCH" \
    "$PACKAGE_DIR/adaptive_payload.patch" \
    "$PACKAGE_DIR/strong_assertions.patch"; do
    git apply --check "$patch"
    git apply "$patch"
    echo "APPLIED: $(basename "$patch")"
done

grep -nF 'mu_s.push(NTT::ONE + NTT::ONE);' \
    crates/latticefold/src/nifs/folding/utils.rs \
    | tee "$LAB_DIR/01_mu2_code.log"
grep -nF 'fn nifs_verifier_accepts_illegal_last_digit_by_range_cancellation()' \
    crates/latticefold/src/nifs/attack_range_cancel_regression.rs \
    >> "$LAB_DIR/01_mu2_code.log"

# The NIFS proof is constructed from a malformed decomposition, then submitted
# to the REAL NIFSVerifier::verify. Additional assertions check the output
# opening, output MLE values and the linearization claims independently.
run_attack_test() {
    cargo +"$TOOLCHAIN" test --locked -p latticefold --lib \
        "$TEST_NAME" -- --nocapture
}

printf '\n[2/4] Positive test: fixed mu=2, adaptive (+5,-4) payload MUST be accepted\n'
if run_attack_test 2>&1 | tee "$LAB_DIR/02_mu2_accept.log"; then
    if ! grep -Fq '1 passed' "$LAB_DIR/02_mu2_accept.log"; then
        echo 'ERROR: test command succeeded but did not report 1 passed' >&2
        exit 1
    fi
    echo 'RESULT: MU2_ACCEPT=PASS'
else
    echo 'RESULT: MU2_ACCEPT=FAIL (do not claim exploit is reproduced)' >&2
    exit 1
fi

printf '\n[3/4] Negative control: SAME (+5,-4) payload, only mu changes from 2 to 1\n'
FILE="crates/latticefold/src/nifs/folding/utils.rs"
BACKUP="$LAB_DIR/utils_mu2_backup.rs"
cp "$FILE" "$BACKUP"
restore_mu2() {
    if [[ -f "$BACKUP" ]]; then
        cp "$BACKUP" "$FILE"
    fi
}
trap restore_mu2 EXIT
python3 - <<'PY'
from pathlib import Path
p = Path('crates/latticefold/src/nifs/folding/utils.rs')
s = p.read_text()
old = 'mu_s.push(NTT::ONE + NTT::ONE);'
assert s.count(old) == 1
p.write_text(s.replace(old, 'mu_s.push(NTT::ONE);', 1))
print('CONTROL: changed only the final mu 2 -> 1; no new transcript squeezes')
PY
if run_attack_test > "$LAB_DIR/03_mu1_reject.log" 2>&1; then
    tail -n 30 "$LAB_DIR/03_mu1_reject.log"
    echo 'RESULT: NEGATIVE_CONTROL=FAIL (unexpected acceptance with mu=1)' >&2
    exit 1
else
    if grep -Fq 'SumCheckFailed' "$LAB_DIR/03_mu1_reject.log"; then
        tail -n 14 "$LAB_DIR/03_mu1_reject.log"
        echo 'RESULT: NEGATIVE_CONTROL=PASS (rejected by SumCheckFailed)'
    else
        tail -n 45 "$LAB_DIR/03_mu1_reject.log"
        echo 'RESULT: NEGATIVE_CONTROL=INCONCLUSIVE (failure was not SumCheckFailed)' >&2
        exit 1
    fi
fi
restore_mu2
trap - EXIT
if ! grep -Fq 'mu_s.push(NTT::ONE + NTT::ONE);' "$FILE"; then
    echo 'ERROR: original mu=2 code was not restored' >&2
    exit 1
fi

printf '\n[4/4] Restoration check: fixed mu=2, SAME payload MUST be accepted again\n'
if run_attack_test 2>&1 | tee "$LAB_DIR/04_mu2_restored_accept.log"; then
    if ! grep -Fq '1 passed' "$LAB_DIR/04_mu2_restored_accept.log"; then
        echo 'ERROR: restoration test did not report 1 passed' >&2
        exit 1
    fi
    echo 'RESULT: MU2_RESTORED_ACCEPT=PASS'
else
    echo 'RESULT: MU2_RESTORED_ACCEPT=FAIL' >&2
    exit 1
fi

cat > "$LAB_DIR/RESULTS.txt" <<EOF
Nethermind LatticeFold fixed-mu=2 end-to-end local regression
UTC time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
Source: bundled Nethermind source snapshot; all 3 patches in SHA256_INPUTS.txt
A: fixed mu=2, payload (+5,-4) -> verifier accepts; strengthened target assertions pass
B: fixed mu=1, SAME payload -> verifier rejects with SumCheckFailed
A: restored fixed mu=2 -> verifier accepts again
PASS: 3/3 controls, plus independent algebra check
IMPORTANT LIMIT: test setup uses A=I and test-only GoldilocksDP; it does not
establish a standard random-Ajtai setup attack or an attack on the original
paper's independently randomized mu.
EOF
printf '\n================ SUMMARY ================\n'
cat "$LAB_DIR/RESULTS.txt"
printf '\nSaved complete logs: %s\n' "$LAB_DIR"
