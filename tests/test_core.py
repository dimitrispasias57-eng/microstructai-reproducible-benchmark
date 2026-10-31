"""Analytical fixtures, invalid inputs, and generator invariants."""

from dataclasses import replace

import numpy as np
import pytest

from segbench.core import Config, METHODS, conditions, confusion, sample_seed, scores, segment, synthetic_sample


def test_hand_calculated_confusion_and_scores():
    truth = np.array([[1, 1, 0], [1, 0, 0]], dtype=bool)
    pred = np.array([[1, 0, 1], [1, 0, 0]], dtype=bool)
    counts = confusion(truth, pred)
    assert counts == {"tp": 2, "fp": 1, "fn": 1, "tn": 2}
    assert scores(counts) == {"iou": .5, "precision": 2/3, "recall": 2/3, "f1": 2/3}


@pytest.mark.parametrize("truth,pred,expected", [
    (False, False, (1., 1., 1., 1.)),
    (True, False, (0., 0., 0., 0.)),
    (False, True, (0., 0., 1., 0.)),
    (True, True, (1., 1., 1., 1.)),
])
def test_empty_and_full_conventions(truth, pred, expected):
    result = scores(confusion(np.full((2, 2), truth), np.full((2, 2), pred)))
    assert tuple(result[k] for k in ("iou", "precision", "recall", "f1")) == expected


@pytest.mark.parametrize("truth,pred", [
    (np.zeros((2, 2)), np.zeros((2, 2), bool)),
    (np.zeros((2, 2), bool), np.zeros((3, 2), bool)),
    (np.array([], bool), np.array([], bool)),
    (np.zeros((2, 2), bool), np.zeros((2, 2), np.uint8)),
])
def test_invalid_masks_rejected(truth, pred):
    with pytest.raises(ValueError):
        confusion(truth, pred)


@pytest.mark.parametrize("field,value", [
    ("samples_per_condition", 1), ("samples_per_condition", True), ("master_seed", -1),
    ("image_size", 10), ("object_count", 0), ("timing_repeats", 0),
    ("bootstrap_repeats", 0), ("local_block_size", 40), ("local_block_size", 201),
    ("noise_sigmas", [-.1]), ("noise_sigmas", [float("nan")]),
    ("contrasts", [0]), ("contrasts", []), ("contrasts", [.1, .1]),
    ("gradient_amplitudes", [float("inf")]), ("local_offset", "0"),
    ("preprocess_sigma", -1), ("radius_ranges", {"small": [8, 4]}),
    ("radius_ranges", {"../unsafe": [4, 8]}), ("radius_ranges", {}),
])
def test_invalid_configuration_rejected(field, value):
    with pytest.raises(ValueError):
        Config(**{field: value})


@pytest.mark.parametrize("image", [np.array([]), np.ones((2, 2, 2)), np.array([[np.nan]]),
                                  np.array([[np.inf]]), np.array([[-.1]]), np.array([[1.1]]),
                                  np.array([["hello"]]), np.array([[1+2j]])])
def test_invalid_image_rejected(image):
    with pytest.raises(ValueError):
        segment(image, "otsu", Config())


def test_seed_protocol_reproducible_and_independent():
    cfg = Config()
    cond = next(conditions(cfg))
    seed = sample_seed(cfg.master_seed, 0, 0)
    a, mask_a, clipping = synthetic_sample(cfg, cond, seed)
    b, mask_b, _ = synthetic_sample(cfg, cond, seed)
    c, mask_c, _ = synthetic_sample(cfg, cond, sample_seed(cfg.master_seed, 0, 1))
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(mask_a, mask_b)
    assert not np.array_equal(mask_a, mask_c)
    assert a.dtype == np.float32 and mask_a.dtype == bool
    assert 0 < mask_a.mean() < 1 and 0 <= clipping <= 1
    assert 0 <= a.min() <= a.max() <= 1
    all_seeds = [sample_seed(cfg.master_seed, k, j) for k in range(24) for j in range(20)]
    assert len(set(all_seeds)) == 480


def test_noiseless_two_level_otsu_has_exact_oracle():
    truth = np.zeros((128, 128), bool)
    truth[20:50, 20:50] = True
    image = .2 + .45*truth.astype(float)
    result = segment(image, "otsu", replace(Config(), preprocess_sigma=0))
    np.testing.assert_array_equal(result, truth)


@pytest.mark.parametrize("method", METHODS)
def test_uniform_image_is_empty_and_input_unchanged(method):
    image = np.full((128, 128), .2, dtype=np.float32)
    before = image.copy()
    assert not segment(image, method, Config()).any()
    np.testing.assert_array_equal(image, before)


def test_unknown_method_rejected():
    with pytest.raises(ValueError, match="unknown method"):
        segment(np.zeros((128, 128)), "made_up", Config())
