# Experiment plan fixed before inspecting results

This plan was written during project construction on 31 October 2026, before executing the full benchmark. It is a local design record, not an externally timestamped preregistration. The default configuration and evaluated source hashes are retained with the run.

## Question

How do two fixed, established thresholding pipelines behave as synthetic image noise, contrast, illumination, and object scale change? The intended result is a conditional comparison with failure analysis, not a universal winner.

## Methods

Both methods take only the image and the same static configuration. Both convert the input to float64 and apply a Gaussian filter with sigma 1 pixel and reflected boundaries. No ground truth or condition settings are passed into threshold selection, and neither pipeline gets per-image manual tuning or postprocessing.

- **Global Otsu:** `skimage.filters.threshold_otsu`, 256 histogram bins. Foreground is strictly above the threshold. Otsu chooses a global threshold by optimizing separation of two intensity classes.
- **Local Gaussian:** `skimage.filters.threshold_local`, method `gaussian`, block size 41, offset −0.025, reflected boundaries. The library computes Gaussian local thresholds with default sigma (41−1)/6. The threshold is the weighted local mean minus the offset, so this negative offset places the threshold 0.025 above the local mean. Foreground is strictly above this spatially varying threshold.

The scale 41 spans several small objects' radii. The fixed negative offset discourages weak background fluctuations from being classified as foreground. These are explicit engineering choices, not optima estimated from this evaluation set. They can disadvantage low-contrast or large filled objects. No parameter search is performed. If parameters are later selected using these results, evaluate that new selection on new seeds and label the follow-up separately.

## Dataset and design

The full factorial grid has two contrasts (0.15, 0.45), three noise standard deviations (0, 0.04, 0.10), two horizontal peak-to-peak illumination gradients (0, 0.4), and two radius ranges (small 4–8 pixels, large 12–18 pixels). Twenty independently seeded scenes per condition yield 480 images and 960 method-image evaluations. Each image is 128 × 128 pixels.

Each scene places six ellipses with continuous centers uniformly within the image, a uniformly sampled major radius, minor/major ratio uniform on [0.65, 1], and angle uniform on [0, π). The binary union is the ideal ground truth. Ellipses can overlap or meet the border; no difficult scenes are rejected. Consequently the size factor also changes foreground prevalence and overlap. It is not an isolated causal study of radius.

Intensities are generated as background 0.2 plus contrast times a Gaussian-blurred ground-truth mask (optical sigma 1), plus the horizontal gradient, plus independent zero-mean Gaussian noise. Intensities are clipped to [0, 1] and stored as float32. The clipping fraction is recorded because clipping changes the realized noise distribution near the range limits. The ground truth is deliberately the pre-blur geometric support.

Master seed: 20261031. A per-image uint64 seed is derived from `SeedSequence([master_seed, condition_index, sample_index])`. Each image uses PCG64 with that explicit seed; it is recorded in the manifest. Contrast, noise and gradient lists retain configuration order; radius labels are sorted alphabetically. Thus `large` precedes `small`. Changing configuration order changes condition indices and seeds. The same image is paired across methods; different conditions use different scenes. A follow-up isolating nuisance effects on identical geometry would require a different design.

## Evaluation and uncertainty

Evaluate every pixel at native resolution without border cropping or resizing. Report integer confusion counts and per-image IoU, precision, recall and F1. Average the per-image ratios; do not pool pixels across images. Report sample SD within each condition. Resample image pairs 5,000 times for percentile intervals on local-minus-Otsu mean IoU differences. Use a separate bootstrap seed namespace `[master_seed, 811, condition_position]`. These are pointwise exploratory intervals; there is no multiplicity correction and no confirmatory hypothesis test.

Accuracy repetitions are the independent images. Timing repetitions are five warm measurements of the same pipeline on the same image, following one warm-up per method/image. Randomize the order of the two methods independently for each repetition with a separate RNG namespace `[master_seed, 923]`. Keep all elapsed nanoseconds, use a median per image, and report the distribution of those medians. Timing includes input validation, conversion, smoothing, threshold calculation and Boolean comparison; it excludes imports, generation, disk I/O, metrics and plotting. Results are specific to the recorded machine and its load.

## Negative findings and integrity

Retain all generated samples. Automatically display the minimum-IoU image for each method, breaking ties by sample ID. Count IoU < 0.5 as a descriptive failure diagnostic, without implying an accepted scientific quality threshold. A software exception aborts the run and leaves no completion metadata; the report command refuses incomplete runs. The runner refuses to overwrite an existing output directory.

The core code is new. Standard library and scientific Python dependencies supply public algorithms. There are no private research methods, real biological data, manually adjusted outcomes, or claims of clinical validity. The article is an AI-assisted draft for scientific review, and must not be described as personally authored and verified by the owner until the owner has reviewed and approved it.

## Public method references

- [scikit-image thresholding guide](https://scikit-image.org/docs/0.25.x/auto_examples/applications/plot_thresholding_guide.html).
- [Otsu API](https://scikit-image.org/docs/0.25.x/api/skimage.filters.html#skimage.filters.threshold_otsu) and [local threshold API](https://scikit-image.org/docs/0.25.x/api/skimage.filters.html#skimage.filters.threshold_local).
- N. Otsu, *A Threshold Selection Method from Gray-Level Histograms* (1979), [DOI: 10.1109/TSMC.1979.4310076](https://doi.org/10.1109/TSMC.1979.4310076).

## Implementation clarification added during final audit

The original design and parameters above are unchanged. For the Gaussian method, block size 41 implies sigma 40/6; the pinned Gaussian implementation truncates at four sigma, so the support is 55 pixels per axis. The original phrase “scale 41” refers to the API parameter. The Otsu implementation uses float32 histogram weights. A float64 weight-product alternative changes three pixels in one image; the benchmark retains the preselected library implementation. These clarifications were added after inspecting audit results and are not part of a claim of external preregistration.
