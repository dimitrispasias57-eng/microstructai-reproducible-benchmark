# Data and result dictionary

All files are generated locally. There are no downloaded image datasets.

## Per-image files

`results/reference/data/cNN_sNNN.npz` is a NumPy archive with four arrays. Always load with `allow_pickle=False`.

| Array | Type / shape | Meaning |
|---|---|---|
| `image` | float32, 128 × 128 in the default run | Clipped synthetic intensity in [0, 1] |
| `truth` | Boolean, same shape | Union of ideal ellipses before optical blur or noise |
| `otsu` | Boolean, same shape | Global threshold prediction |
| `local_gaussian` | Boolean, same shape | Local threshold prediction |

Floating point images preserve the actual evaluated input. PNG plots are for visualization only and are not the source of measurements. NPZ container byte hashes can differ after regeneration because container metadata can vary; array hashes cover canonical little-endian array bytes, dtype, and shape.

## Tabular outputs

`manifest.csv`: one row per image, including `sample_id`, `condition_id`, condition index, contrast, noise sigma, gradient amplitude, size class, sample index, explicit integer seed, artifact path, image/truth array SHA-256 hashes, foreground fraction and clipping fraction. Clipping fraction is the fraction outside [0, 1] before clipping. All intensity parameters are dimensionless; radii and blur scales use pixels.

`raw.csv`: the same identifying fields plus method, completion status, integer `tp`, `fp`, `fn`, `tn`, IoU, precision, recall, F1, runtime in milliseconds (median of the timing repeats for that image/method), and prediction hash. Each input has exactly one row for each method. Ground truth is the positive class; the entire image is evaluated, including its border. Rows have equal weight in the macro averages.

`timings.csv`: sample, method, repeat index, randomized method position (0 or 1), and elapsed integer nanoseconds. Repeated timings are not independent accuracy samples.

`summary.csv`: image-level mean and sample SD (denominator n−1) for each accuracy metric within a condition and method; median of per-image runtime medians; count of IoU < 0.5. This cutoff is a descriptive diagnostic, not an externally validated acceptance criterion.

`paired.csv`: within-condition mean and sample SD of local-minus-Otsu IoU differences; percentile bootstrap 95% interval; per-image wins and ties. The resampling unit is the image pair. These are exploratory pointwise intervals without correction for inspecting many conditions.

`overall.csv`: macro IoU and F1 across the exact balanced condition grid, median of image runtime medians, and low-IoU count. It is not a population estimate for microscopy images. It must not be interpreted as a universal method ranking.

`failure_cases.csv`: the lowest-IoU image for each method; ties break by sample ID. All other samples remain in the raw dataset.

`claims.json`: machine-readable values derived from raw results. `tables.md`: readable condition table. `metadata.json`: completion marker, UTC times, Python/dependency versions, safe machine descriptors, thread settings, code/configuration hashes, and timing scope. `verification.json`: the executed verification outcome and its limitations.

## Missing or failed runs

An exception stops execution. A run without `metadata.json` is incomplete and the reporting command refuses it; do not report its partial artifacts as a completed experiment. Existing output directories are never overwritten by the runner. Choose a new directory for a rerun.
