#!/usr/bin/env python3
"""Run every standalone algebra check in the artifact repository."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
CHECKS = [
    *sorted((ROOT / "latticefold" / "algebra").glob("*.py")),
    ROOT / "latticefold" / "mu2" / "fixed_mu2_sumcheck_model.py",
    *sorted((ROOT / "latticefold-plus" / "algebra").glob("*.py")),
]


def main() -> int:
    failures: list[Path] = []
    for check in CHECKS:
        relative = check.relative_to(ROOT)
        print(f"\n=== {relative.as_posix()} ===", flush=True)
        result = subprocess.run([sys.executable, str(check)], cwd=ROOT, check=False)
        if result.returncode == 0:
            print(f"PASS: {relative.as_posix()}")
        else:
            failures.append(relative)
            print(f"FAIL: {relative.as_posix()} (exit {result.returncode})")

    if failures:
        print("\nFAILED CHECKS:")
        for failure in failures:
            print(f"- {failure.as_posix()}")
        return 1

    print("\nALL ALGEBRA CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
