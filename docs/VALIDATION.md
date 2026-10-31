# Final executed validation record

> Publication update: the owner explicitly approved publishing this separate audited project after this local audit. Historical statements below about publication being unauthorized, the repository remaining local, or hosted CI being unexecuted describe the audit-time state. The current [repository](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark) and [Actions runs](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark/actions/workflows/tests.yml) show the publication state. The article remains an AI-assisted draft awaiting substantive author review; application-readiness limitations still apply.

Audit date: 31 October 2026. All checks described as passed were executed locally. The original review archive was preserved unchanged; this candidate contains a new reference run after dependency remediation.

## Three complete benchmark executions

| Run | Environment | Otsu median ms | Local median ms | Accuracy |
|---|---|---:|---:|---|
| Original reference | Original pinned environment | 0.30500 | 0.48705 | Archived original |
| Clean original-stack rerun | Fresh venv, original pins | 0.28470 | 0.46960 | Exact original match |
| Final candidate reference | Separate fresh venv, security fixes | 0.30215 | 0.44900 | Exact original match |

All three runs used CPython 3.12.14 on the same Windows 11 AMD64 host with 32 logical CPUs. Each completed 24 conditions, 480 images, 960 evaluations and 4,800 timing observations. Each method-image observation had one warm-up and five interleaved measurements. Machine load, frequency and affinity were not controlled. Timing observations are genuine, but their exact values are not reproducible constants. All accuracy rows, 1,920 arrays per run, condition summaries and paired intervals reproduced; timing and execution metadata appropriately differ.

The fresh environments excluded system and user site packages. The final full benchmark, reporting and regeneration ran with a Python audit hook rejecting network connection, address lookup and bind events; none were attempted. Loaded modules were restricted to the candidate, fresh venv and Python installation. This is evidence of standalone execution, not a clean-OS certification. See [execution record](audit/standalone_execution.json) and [complete run output](audit/full_run.txt).

## Executed tests and numerical checks

The clean original-stack test run passed **52 tests in 12.31 seconds**. The final security-fixed environment passed **52 tests in 11.83 seconds**. The [final test output](audit/tests.txt) is retained. Earlier development had 50 tests, followed by two additional tamper tests and a 52-test run in 7.69 seconds. No complete pytest run failed. Tests cover metric edge cases, malformed inputs, deterministic seeds, an exact noiseless oracle, non-mutation, complete small runs, corrupted timing and summary evidence, existing-output refusal and incomplete-run rejection.

The routine verifier checked all 960 confusion tables, metrics, summaries, source hashes, 4,800 observations and all regenerated arrays. See [verification.json](../results/reference/verification.json). Regeneration shares production code, so it alone is not independent method validation.

The additional [independent checker](../tools/independent_science_audit.py) imports neither the benchmark nor SciPy/scikit-image. It separately computes quadratic-form ellipse membership, finite Gaussian kernels and reflected convolution, Otsu class separation with the pinned float32 weight-product behavior, Gaussian local thresholds, scalar confusion counts, means, sample SDs, resampling means and interpolated percentiles. NumPy supplies arrays and the specified RNG. It matched all generated float32 images and truth masks exactly, matched all 960 prediction masks, and checked all 48 interval endpoints with maximum absolute discrepancy **1.1102230246251565e-16**, below the declared statistics tolerance of 1e-12. Image tolerance was 1e-7; observed image discrepancy was zero. [Executed result](audit/independent_science.json).

The first independent-checker attempt used float64 Otsu weight products and disagreed by three pixels in c00_s005. Inspection of the pinned library identified float32 histogram weights as the cause; independently reproducing that precision resolved the disagreement. The relative objective loss against float64 was 1.4572219742259571e-08. This was an audit finding, not a changed experimental parameter or concealed algorithm failure. The article documents it. The Gaussian block-size interpretation was also clarified: 41 determines sigma 40/6, and four-sigma truncation produces 55-pixel support.

The checker was written by the same AI reviewer in a separate implementation. It is independent arithmetic, not independent human peer review. Linux/macOS execution, a clean OS, hosted CI and a multi-machine timing campaign remain unexecuted. Public platform wheel availability was checked; that does not substitute for platform tests.

## Dependency remediation and provenance

The first release candidate failed the dependency-security check. Published advisories affected Pillow 12.3.0, Pygments 2.19.2, pytest 8.4.2 and installer pip 25.0.1. The final environment uses Pillow 13.0.0, Pygments 2.21.0, pytest 9.0.3 and pip 26.2.2. All 23 final pins were available from public PyPI and returned no advisories in the current OSV query. [Query record](audit/dependencies_security.json), [dependency/license inventory](audit/dependency_inventory.json).

All 23 resolved wheel digests were checked against official PyPI metadata; 5,904 installed files matched their distribution RECORD hashes. Dependencies are not vendored in this repository. No license conflict was identified for distributing the new source and synthetic artifacts. This is not a legal opinion or proof that every dependency is vulnerability-free.

Large ordinary wheel downloads stalled during setup. Public wheels were retrieved in verified byte ranges where necessary. The original development also included an early pytest launch before installation completed (`No module named pytest`); no tests ran in that launch. These setup failures did not change benchmark parameters. An audit helper initially encountered Windows text-decoding defaults; UTF-8 was made explicit, affected candidate prose was restored from the preserved source, and its final numerical claims and encoding were checked.

All three final figures were inspected for layout and data provenance. They are generated from CSV/arrays, without manually edited data. The file audit validates NPZ structure, PNG metadata, text contents, hashes and dependency provenance. No private repository is needed for any public reproduction command.
