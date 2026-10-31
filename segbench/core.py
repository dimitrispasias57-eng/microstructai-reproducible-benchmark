"""Validated experiment configuration, synthetic scenes, methods, and metrics."""

from dataclasses import asdict, dataclass, field
from itertools import product
import math

import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.filters import threshold_local, threshold_otsu


METHODS = ("otsu", "local_gaussian")
METRICS = ("iou", "precision", "recall", "f1")


def finite_number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be finite and in [{low}, {high}]")


@dataclass
class Config:
    master_seed: int = 20261031
    samples_per_condition: int = 20
    image_size: int = 128
    object_count: int = 6
    background: float = 0.2
    contrasts: list = field(default_factory=lambda: [0.15, 0.45])
    noise_sigmas: list = field(default_factory=lambda: [0.0, 0.04, 0.1])
    gradient_amplitudes: list = field(default_factory=lambda: [0.0, 0.4])
    radius_ranges: dict = field(default_factory=lambda: {"small": [4., 8.], "large": [12., 18.]})
    optical_blur_sigma: float = 1.0
    preprocess_sigma: float = 1.0
    local_block_size: int = 41
    local_offset: float = -0.025
    timing_repeats: int = 5
    bootstrap_repeats: int = 5000

    def __post_init__(self):
        for name, low, high in [("master_seed", 0, 2**32-1), ("samples_per_condition", 2, 10000),
                                ("image_size", 32, 2048), ("object_count", 1, 1000),
                                ("timing_repeats", 1, 100), ("bootstrap_repeats", 100, 100000)]:
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer in [{low}, {high}]")
        for name in ("contrasts", "noise_sigmas", "gradient_amplitudes"):
            values = getattr(self, name)
            if not isinstance(values, list) or not values:
                raise ValueError(f"{name} must be a nonempty list")
            for value in values:
                finite_number(value, name, 0, 1)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicates")
        if any(v == 0 for v in self.contrasts):
            raise ValueError("contrasts must be positive")
        finite_number(self.background, "background", 0, 1)
        for name in ("optical_blur_sigma", "preprocess_sigma"):
            finite_number(getattr(self, name), name, 0, self.image_size / 4)
        finite_number(self.local_offset, "local_offset", -1, 1)
        if (type(self.local_block_size) is not int or self.local_block_size % 2 != 1
                or not 3 <= self.local_block_size <= self.image_size):
            raise ValueError("local_block_size must be odd and between 3 and image_size")
        if not isinstance(self.radius_ranges, dict) or not self.radius_ranges:
            raise ValueError("radius_ranges must be a nonempty mapping")
        for name, pair in self.radius_ranges.items():
            if not isinstance(name, str) or not name.isidentifier():
                raise ValueError("radius labels must be identifiers")
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError("radius ranges must contain two numbers")
            for value in pair:
                finite_number(value, "radius", 1, self.image_size / 4)
            if pair[0] > pair[1]:
                raise ValueError("radius range is reversed")

    def as_dict(self):
        return asdict(self)


def conditions(config):
    """Stable ordering is part of the seed protocol; radius labels are sorted."""
    for i, (contrast, noise, gradient, size) in enumerate(product(
            config.contrasts, config.noise_sigmas, config.gradient_amplitudes,
            sorted(config.radius_ranges))):
        yield {"condition_id": f"c{i:02d}", "condition_index": i,
               "contrast": contrast, "noise_sigma": noise,
               "gradient_amplitude": gradient, "size_class": size}


def sample_seed(master, condition_index, sample_index):
    return int(np.random.SeedSequence([master, condition_index, sample_index])
               .generate_state(1, dtype=np.uint64)[0])


def synthetic_sample(config, condition, seed):
    """Union of six rotated ellipses; ground truth precedes blur and noise.

    Objects may overlap and meet image boundaries. The labels are semantic
    foreground, not instance IDs. There is no rejection of difficult samples.
    """
    rng = np.random.Generator(np.random.PCG64(seed))
    n = config.image_size
    yy, xx = np.mgrid[:n, :n]
    truth = np.zeros((n, n), dtype=bool)
    for _ in range(config.object_count):
        cy, cx = rng.uniform(0, n-1, 2)
        a = rng.uniform(*config.radius_ranges[condition["size_class"]])
        b = a * rng.uniform(0.65, 1.0)
        theta = rng.uniform(0, np.pi)
        u = (xx-cx)*np.cos(theta) + (yy-cy)*np.sin(theta)
        v = -(xx-cx)*np.sin(theta) + (yy-cy)*np.cos(theta)
        truth |= (u/a)**2 + (v/b)**2 <= 1.0
    signal = gaussian_filter(truth.astype(np.float64), config.optical_blur_sigma, mode="reflect")
    gradient = condition["gradient_amplitude"] * (xx/(n-1) - 0.5)
    raw = config.background + condition["contrast"]*signal + gradient
    raw += rng.normal(0.0, condition["noise_sigma"], size=(n, n))
    clipped_fraction = float(np.mean((raw < 0) | (raw > 1)))
    image = np.clip(raw, 0, 1).astype(np.float32)
    return image, truth, clipped_fraction


def validate_image(image):
    if not isinstance(image, np.ndarray) or image.ndim != 2 or image.size == 0:
        raise ValueError("image must be a nonempty 2D NumPy array")
    if image.dtype.kind not in "fiu" or not np.isfinite(image).all():
        raise ValueError("image must contain finite numeric values")
    if np.min(image) < 0 or np.max(image) > 1:
        raise ValueError("image values must be in [0, 1]")


def segment(image, method, config):
    """Includes identical smoothing; neither method sees labels or condition."""
    validate_image(image)
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    smooth = gaussian_filter(image.astype(np.float64), config.preprocess_sigma, mode="reflect")
    if method == "otsu":
        threshold = threshold_otsu(smooth, nbins=256)
    else:
        threshold = threshold_local(smooth, block_size=config.local_block_size,
                                    method="gaussian", offset=config.local_offset, mode="reflect")
    return smooth > threshold


def confusion(truth, prediction):
    for name, mask in (("truth", truth), ("prediction", prediction)):
        if not isinstance(mask, np.ndarray) or mask.ndim != 2 or not mask.size or mask.dtype != bool:
            raise ValueError(f"{name} must be a nonempty 2D Boolean array")
    if truth.shape != prediction.shape:
        raise ValueError("mask shapes differ")
    return {"tp": int(np.count_nonzero(truth & prediction)),
            "fp": int(np.count_nonzero(~truth & prediction)),
            "fn": int(np.count_nonzero(truth & ~prediction)),
            "tn": int(np.count_nonzero(~truth & ~prediction))}


def scores(counts):
    """Both empty = perfect overlap; undefined precision/recall handled explicitly."""
    tp, fp, fn = (counts[k] for k in ("tp", "fp", "fn"))
    return {"iou": tp/(tp+fp+fn) if tp+fp+fn else 1.,
            "precision": tp/(tp+fp) if tp+fp else (1. if tp+fn == 0 else 0.),
            "recall": tp/(tp+fn) if tp+fn else 1.,
            "f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1.}
