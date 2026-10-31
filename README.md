# MicroStructAI reproducible benchmark

A self-contained Python experiment comparing **global Otsu** and **local Gaussian thresholding** on synthetic images with known geometric ground truth. The project demonstrates experimental design, numerical verification, failure analysis, and technical communication.

**Review status:** the owner explicitly approved publication of this separate audited benchmark. The technical article remains an AI-assisted draft awaiting substantive author review and editing; publication does not establish independent authorship or completed scientific review. No real biological images, private algorithms, or source-repository history are included. All images and results in this directory are synthetic demonstrations.

Read the [technical article](docs/ARTICLE.md), [experiment plan](docs/EXPERIMENT_PLAN.md), [validation record](docs/VALIDATION.md), [release review](docs/RELEASE_REVIEW.md), and [final audit](docs/FINAL_AUDIT.md).

## The problem

A global intensity threshold can be affected by uneven illumination. A local threshold can adapt to illumination but depend strongly on scale and offset. This benchmark compares fixed implementations across 24 combinations of contrast, noise, illumination gradient and object radius range, with 20 independently seeded images per condition. Both methods process exactly the same 480 images, with the same initial smoothing and evaluation procedure.

The test is intentionally modest. It does not establish performance on microscopy, clinical validity, or a universal ranking of segmentation methods. The parameters were not optimized on the evaluation data. Larger shapes also change foreground occupancy and overlap, so the size factor is not an isolated causal comparison.

## Observed reference result

| Method | Mean image IoU | Mean image F1 | IoU below 0.5 |
|---|---:|---:|---:|
| Global Otsu | 0.581701 | 0.639368 | 212 / 480 |
| Local Gaussian | 0.642703 | 0.747756 | 124 / 480 |

These are actual results from the fixed 480-image grid. The ranking reverses in several conditions; see the [full condition table](results/reference/tables.md). Fifty-two tests passed, and all 960 result rows plus 4,800 timing observations passed the pixel-level verification and regeneration checks.

[![Tests](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark/actions/workflows/tests.yml/badge.svg)](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark/actions/workflows/tests.yml)

## Installation

Clone this repository and enter its root before running the commands below:

```bash
git clone https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark.git
cd microstructai-reproducible-benchmark
```

Use CPython 3.12 (the reference run records its exact patch version). `requirements.in` lists direct dependencies and installer tooling; `requirements.txt` pins the full tested environment. No API keys, account, GPU, private repository, or downloaded image datasets are required. Installation needs access to PyPI unless you already have matching wheels.

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip==26.2.2
python -m pip install -r requirements.txt
python -m pip check
```

Windows PowerShell, with Python 3.12 available as `python`:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip==26.2.2
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip check
```

Use `.\.venv\Scripts\python.exe` in place of `python` in the commands below on Windows. Run commands from this project root.

## Reproduce the experiment

For comparable timing, set the listed thread limits before starting Python. On Linux/macOS:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q
python -m segbench.run --config configs/default.json --output runs/reproduce
python -m segbench.report runs/reproduce
python -m segbench.verify runs/reproduce --regenerate
```

On Windows PowerShell:

```powershell
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m segbench.run --config configs/default.json --output runs/reproduce
& .\.venv\Scripts\python.exe -m segbench.report runs/reproduce
& .\.venv\Scripts\python.exe -m segbench.verify runs/reproduce --regenerate
```

The runner refuses to overwrite an existing output directory. Use a new path for another run. It saves completion metadata only after all evaluations finish; the report command rejects incomplete runs.

Accuracy should reproduce with the recorded software stack. Exact floating point array equality is checked by `--regenerate` in the tested environment; bitwise equality across different numerical libraries or operating systems is not promised. Timing is machine- and load-dependent and will change. The [GitHub Actions workflow](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark/actions/workflows/tests.yml) runs the automated tests, including a small end-to-end benchmark, on Linux and Windows. The badge shows the current CI outcome; the archived full 480-image experiment was executed on Windows as recorded in its metadata.

## Verify the supplied evidence

```bash
python -m segbench.verify results/reference --regenerate
python -m segbench.report results/reference
python tools/release_audit.py
```

The verifier independently reconstructs each confusion table from the archived masks using a four-bin encoding, checks the metric formulas and the Dice/IoU identity, recalculates summary means and sample SDs, checks timing medians and array hashes, and regenerates every image and prediction when requested. It checks code hashes against the run metadata. That routine verifier does not independently implement segmentation or bootstrap endpoints. The additional `python tools/independent_science_audit.py runs/reproduce` command checks the full default grid against the reference and separately reconstructs geometry, kernels, configured thresholds, metrics and bootstrap endpoints. See [the executed audit](docs/audit/independent_science.json) for precision details and independence limits.

## Find any reported number

Every article accuracy value comes from `results/reference/raw.csv`, grouped in `summary.csv`. Overall macro values are in `overall.csv`; within-condition paired differences and bootstrap intervals are in `paired.csv`. Exact machine-readable headline values are in `claims.json`. Counts of IoU < 0.5 are descriptive diagnostics, not validated scientific pass criteria.

To trace a number, locate its condition and method in `summary.csv`, select the corresponding 20 rows in `raw.csv`, and follow each row's `artifact` to its arrays in `data/`. The verifier performs this check for all rows. [Generated tables](results/reference/tables.md) provide the full condition mapping and mean ± SD values. The [data dictionary](docs/DATA_DICTIONARY.md) defines every output.

## Project layout

```text
configs/default.json             Fixed design, seeds, and parameters
segbench/core.py                  Generator, methods, validation, and metrics
segbench/run.py                   Experiment runner and metadata capture
segbench/report.py                CSV summaries, bootstrap intervals, plots
segbench/verify.py                Independent arithmetic and artifact checks
tests/                           Analytical, input, and end-to-end tests
tools/release_audit.py            Public-directory scan and file manifest
results/reference/data/          All synthetic images, labels, predictions
results/reference/*.csv          Raw results, timing repeats, and summaries
results/reference/figures/       Robustness, runtime, and failure-case plots
docs/ARTICLE.md                   Complete technical article draft
docs/EXPERIMENT_PLAN.md           Design decisions and limitations
docs/VALIDATION.md                Executed checks and setup issues
docs/RELEASE_REVIEW.md            Publication boundary and audit limitations
.github/workflows/tests.yml       Automated tests on Linux and Windows
```

## Scope, provenance, and license

All project code was written afresh around public scientific Python implementations. All images are generated from ellipses; their labels are exact geometric support before blur. This is not a reimplementation of an unpublished research pipeline or a reproduction of numerical results in a scientific paper. Real biological validation would require appropriately licensed representative data, defensible annotations, and a separate protocol.

The project is released under [MIT](LICENSE) with the owner's publication approval. Dependencies retain their own licenses; see [third-party notices](docs/THIRD_PARTY_NOTICES.md). The full scientific and authorship review remains with the owner. See the article for what the measurements do and do not establish.
