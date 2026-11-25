# On the Security of LatticeFold and LatticeFold+

This repository contains executable algebra checks and test-only patches for the LatticeFold and LatticeFold+ security analysis.

The repository is organized around reproducibility. Every Python program uses only the standard library. The Rust artifacts are patches against the bundled Nethermind source snapshot and are applied only to isolated copies created by the reproduction scripts.

## Artifact map

| Paper location | Artifact | Purpose |
| --- | --- | --- |
| Section 3.1 | [`latticefold/algebra/generic_folding_counterexample.py`](latticefold/algebra/generic_folding_counterexample.py) | Checks the generic folding counterexample. |
| Section 3.2 | [`latticefold/algebra/batch_soundness_counterexample.py`](latticefold/algebra/batch_soundness_counterexample.py) | Checks the optimized batched relation. |
| Section 3.2 | [`latticefold/algebra/optimized_soundness_counterexample.py`](latticefold/algebra/optimized_soundness_counterexample.py) | Reproduces the optimized soundness calculation. |
| Section 3.2 | [`latticefold/algebra/tensor_orientation_counterexample.py`](latticefold/algebra/tensor_orientation_counterexample.py) | Checks the tensor-orientation inconsistency. |
| Section 3.3 | [`latticefold/algebra/`](latticefold/algebra/) | Contains the auxiliary error-bound, semantic, and transcript checks. |
| Section 3.4 | [`latticefold/nethermind/`](latticefold/nethermind/) | Contains the Rust regression test, patch, and the controlled mu=1/mu=2/mu=1 runner. |
| Section 3.4 | [`latticefold/mu2/`](latticefold/mu2/) | Contains the fixed-mu=2 arithmetic model and end-to-end Rust runner. |
| Section 4.1 | [`latticefold-plus/nethermind/patches/r1cs_public_input_binding.patch`](latticefold-plus/nethermind/patches/r1cs_public_input_binding.patch) | Adds the R1CS public-input regression test. |
| Section 4.2 | [`latticefold-plus/algebra/noncanonical_decomposition_check.py`](latticefold-plus/algebra/noncanonical_decomposition_check.py) | Checks the noncanonical decomposition algebra. |
| Sections 4.2-4.3 | [`latticefold-plus/nethermind/patches/noncanonical_range_and_commitment.patch`](latticefold-plus/nethermind/patches/noncanonical_range_and_commitment.patch) | Adds range-check and commitment-transformation regression tests. |
| Section 4.3 | [`latticefold-plus/nethermind/patches/public_parameter_binding.patch`](latticefold-plus/nethermind/patches/public_parameter_binding.patch) | Adds the public-parameter invariance test. |

## Quick start

Requirements for the algebra checks:

- Python 3.10 or newer
- No third-party Python packages

Run every standalone algebra check:

```bash
python3 run_algebra_checks.py
```

Run one check directly:

```bash
python3 latticefold/algebra/generic_folding_counterexample.py
python3 latticefold-plus/algebra/noncanonical_decomposition_check.py
```

The runner reports each program as `PASS` only when it exits with status 0. Its final line is `ALL ALGEBRA CHECKS PASSED` when all checks succeed.

## Rust reproduction

The Rust tests require Linux or WSL, `git`, `unzip`, and Rust `nightly-2025-08-19`. The source snapshot is stored at [`vendor/nethermind-latticefold-snapshot.zip`](vendor/nethermind-latticefold-snapshot.zip). Each runner extracts a fresh copy into a new temporary directory and does not modify the repository.

### LatticeFold implementation checks

Apply the baseline patch and run the controlled mu experiment:

```bash
unzip -q vendor/nethermind-latticefold-snapshot.zip -d /tmp/latticefold-audit
cd /tmp/latticefold-audit/latticefold-main
git apply /path/to/latticefold-security-audit/latticefold/nethermind/range_cancellation.patch
bash /path/to/latticefold-security-audit/latticefold/nethermind/reproduce_mu_aba.sh
```

For the fixed-mu=2 end-to-end test:

```bash
bash latticefold/mu2/run_end_to_end.sh
```

The end-to-end runner performs three controls: acceptance with fixed mu=2, rejection of the same payload with mu=1, and acceptance after restoring mu=2. It also runs the independent finite-field model before compiling the Rust test.

### LatticeFold+ implementation checks

Run one case or all cases:

```bash
bash latticefold-plus/nethermind/reproduce.sh r1cs
bash latticefold-plus/nethermind/reproduce.sh range
bash latticefold-plus/nethermind/reproduce.sh commitment
bash latticefold-plus/nethermind/reproduce.sh parameters
bash latticefold-plus/nethermind/reproduce.sh all
```

Each command requires the matching test to report exactly one passing Rust test. Logs, hashes, and toolchain versions are written to an isolated directory under `~/latticefold-plus-audit-runs/` by default.

## Directory structure

```text
.
|-- latticefold/
|   |-- algebra/       # Standalone Python checks for Section 3
|   |-- nethermind/    # Baseline Rust regression and controlled experiment
|   `-- mu2/           # Fixed-mu=2 model and end-to-end runner
|-- latticefold-plus/
|   |-- algebra/       # Standalone Python check for Section 4
|   `-- nethermind/    # Rust patches and isolated reproduction runner
|-- vendor/            # Pinned Nethermind source snapshot
|-- run_algebra_checks.py
`-- SHA256SUMS.txt
```

## Scope and limitations

- The Python programs check explicit finite-ring or finite-field calculations; they do not execute the Rust verifier.
- The Rust patches are test artifacts, not production exploit code.
- The LatticeFold NIFS regression uses an identity commitment matrix to isolate verifier logic. This setup is not a standard random-Ajtai parameter generation experiment.
- The fixed-mu=2 test studies the implementation variant encoded by the patches. It is not a claim about a protocol that samples all batching coefficients independently.
- The LatticeFold+ tests target the stated auxiliary relations and the corresponding implementation paths. They do not by themselves establish a failure of a repaired relation.

## Provenance

The bundled Nethermind source snapshot has SHA-256 digest `b3867672bf3673a088476bcf5569e916f266a0995d0dcc0c5b55ba2aa9bfe1b0`. It retains the upstream Apache-2.0 and MIT license files. The repository-level [`SHA256SUMS.txt`](SHA256SUMS.txt) records the exact digest of every code file, patch, runner, and source snapshot.

## Responsible disclosure

Implementation findings should be reported through the private channel described in the upstream Nethermind `SECURITY.md` before broader disclosure.

## License

This repository is released under the MIT License. See [`LICENSE`](LICENSE).
