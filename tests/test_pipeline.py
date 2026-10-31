"""An actual small experiment and adversarial edits to its audit trail."""

import json
from dataclasses import replace

import pytest

from segbench.core import Config
from segbench.io import read_csv, write_csv
from segbench.report import report
from segbench.run import run
from segbench.verify import verify


@pytest.fixture
def tiny_run(tmp_path):
    cfg = replace(Config(), samples_per_condition=2, contrasts=[.45], noise_sigmas=[0.],
                  gradient_amplitudes=[0., .4], radius_ranges={"small": [4., 8.]},
                  timing_repeats=2, bootstrap_repeats=100)
    output = tmp_path / "experiment"
    run(cfg, output)
    report(output)
    return output


def test_complete_roundtrip_and_regeneration(tiny_run):
    result = verify(tiny_run, regenerate=True)
    assert result["samples_checked"] == 4
    assert result["result_rows_checked"] == 8
    assert result["timing_observations_checked"] == 16
    assert result["all_images_and_predictions_regenerated"] is True
    assert (tiny_run / "figures" / "failure_cases.png").stat().st_size > 1000


@pytest.mark.parametrize("tamper", ["metric", "count", "duplicate", "summary", "seed", "timing", "overall"])
def test_audit_rejects_corrupted_evidence(tiny_run, tamper):
    if tamper == "summary":
        path = tiny_run / "summary.csv"
        rows = read_csv(path)
        rows[0]["iou_mean"] = "0.123456"
    elif tamper == "overall":
        path = tiny_run / "overall.csv"
        rows = read_csv(path)
        rows[0]["macro_iou"] = "0.123456"
    elif tamper == "timing":
        path = tiny_run / "timings.csv"
        rows = read_csv(path)
        rows[0]["elapsed_ns"] = "-1"
    elif tamper == "seed":
        path = tiny_run / "manifest.csv"
        rows = read_csv(path)
        rows[0]["seed"] = rows[1]["seed"]
    else:
        path = tiny_run / "raw.csv"
        rows = read_csv(path)
        if tamper == "metric":
            rows[0]["iou"] = "0.123456"
        elif tamper == "count":
            rows[0]["tp"] = str(int(rows[0]["tp"])+1)
        else:
            rows[1] = rows[0].copy()
    write_csv(path, rows)
    with pytest.raises(ValueError):
        verify(tiny_run)


def test_output_overwrite_is_rejected(tmp_path):
    with pytest.raises(FileExistsError):
        run(Config(), tmp_path)


def test_incomplete_run_not_reported(tmp_path):
    with pytest.raises(ValueError, match="incomplete"):
        report(tmp_path)
