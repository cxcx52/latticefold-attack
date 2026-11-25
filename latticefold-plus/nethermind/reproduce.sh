#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
CASE="${1:-help}"
SOURCE="$ROOT/vendor/nethermind-latticefold-snapshot.zip"
PATCH_DIR="$HERE/patches"
OUTROOT="${LFPLUS_RUN_ROOT:-$HOME/latticefold-plus-audit-runs}"

usage() {
  cat <<'USAGE'
Usage: bash latticefold-plus/nethermind/reproduce.sh r1cs|range|commitment|parameters|all

Each case extracts an isolated original Nethermind ZIP, applies the relevant
Rust test patch, and runs cargo test with the repository's pinned toolchain.
No project files outside the run directory are altered.
USAGE
}
case "$CASE" in
  r1cs|range|commitment|parameters|all) ;;
  *) usage; exit 2 ;;
esac
[[ -f "$SOURCE" ]] || { echo "Missing source: $SOURCE" >&2; exit 2; }
command -v unzip >/dev/null || { echo 'unzip not found' >&2; exit 2; }
command -v git >/dev/null || { echo 'git not found' >&2; exit 2; }
if ! command -v cargo >/dev/null; then
  [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
fi
command -v cargo >/dev/null || { echo 'cargo not found' >&2; exit 2; }

mkdir -p "$OUTROOT"
RUN="$(mktemp -d "$OUTROOT/lfplus-${CASE}.XXXXXXXX")"
echo "REPRO_DIR=$RUN"
printf '%s\n' "$RUN" > "$OUTROOT/LAST_${CASE}_RUN.txt"
sha256sum "$SOURCE" "$PATCH_DIR/"*.patch > "$RUN/INPUT_SHA256SUMS.txt"
unzip -q "$SOURCE" -d "$RUN"
cd "$RUN/latticefold-main"

apply_patch() {
  local patch="$PATCH_DIR/$1"
  git apply --check "$patch"
  git apply "$patch"
  echo "APPLIED_PATCH=$(basename "$patch")"
}

if [[ "$CASE" == r1cs || "$CASE" == all ]]; then apply_patch r1cs_public_input_binding.patch; fi
if [[ "$CASE" == range || "$CASE" == commitment || "$CASE" == all ]]; then apply_patch noncanonical_range_and_commitment.patch; fi
if [[ "$CASE" == parameters || "$CASE" == all ]]; then apply_patch public_parameter_binding.patch; fi

cargo +nightly-2025-08-19 --version | tee "$RUN/toolchain.log"
rustc +nightly-2025-08-19 --version | tee -a "$RUN/toolchain.log"

test_case() {
  local id="$1" filter="$2"
  echo "===== TEST $id ====="
  RUST_BACKTRACE=1 cargo +nightly-2025-08-19 test --locked \
    -p latticefold-plus --lib "$filter" -- --exact --nocapture 2>&1 \
    | tee "$RUN/${id}.log"
  # Fails if cargo failed, and also if filter inadvertently selected zero tests.
  grep -Eq '^test result: ok\. 1 passed; 0 failed' "$RUN/${id}.log" \
    || { echo "ERROR: Did not observe 1 passed for $id" >&2; exit 1; }
}

if [[ "$CASE" == r1cs || "$CASE" == all ]]; then
  test_case r1cs_public_input r1cs::tests::attack_appendix_a_public_input_unbound
fi
if [[ "$CASE" == range || "$CASE" == all ]]; then
  test_case noncanonical_range rgchk::tests::attack_noncanonical_digit_range_check
fi
if [[ "$CASE" == commitment || "$CASE" == all ]]; then
  test_case noncanonical_cm rgchk::tests::attack_noncanonical_digit_commitment_transform
fi
if [[ "$CASE" == parameters || "$CASE" == all ]]; then
  test_case wrong_A plus::tests::test_prove
fi

echo "PASS case=$CASE; full logs: $RUN"
