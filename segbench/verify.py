"""Independent pixel-level arithmetic audit; does not import production metrics."""

import argparse
from collections import defaultdict
import json
import hashlib
import math
from pathlib import Path
import statistics

import numpy as np

from .io import array_hash, file_hash, read_csv, write_json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, message):
    require(math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12), message)


def independent_counts(truth, pred):
    # Four-bin encoding is separate from the production Boolean conjunctions.
    tn, fp, fn, tp = np.bincount((2*truth.astype(np.uint8) + pred).ravel(), minlength=4)
    return dict(tp=int(tp), fp=int(fp), fn=int(fn), tn=int(tn))


def independent_scores(counts):
    a, b, c = (counts[k] for k in ("tp", "fp", "fn"))
    union = a+b+c
    return {"iou": a/union if union else 1.,
            "precision": a/(a+b) if a+b else (0. if c else 1.),
            "recall": a/(a+c) if a+c else 1.,
            "f1": 2*a/(2*a+b+c) if union else 1.}


def verify(run_dir, regenerate=False):
    run_dir = Path(run_dir)
    rows = read_csv(run_dir / "raw.csv")
    manifest = read_csv(run_dir / "manifest.csv")
    config = json.loads((run_dir / "config.json").read_text())
    meta = json.loads((run_dir / "metadata.json").read_text())
    require(hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest() == meta["config_sha256"],
            "configuration hash mismatch")
    expected_conditions = len(config["contrasts"])*len(config["noise_sigmas"])*len(config["gradient_amplitudes"])*len(config["radius_ranges"])
    expected_samples = expected_conditions * config["samples_per_condition"]
    require(len(manifest) == expected_samples == meta["sample_count"], "sample count mismatch")
    require(len(rows) == 2*expected_samples, "raw row count mismatch")
    require(len({r["sample_id"] for r in manifest}) == expected_samples, "duplicate manifest sample")
    require(len({r["seed"] for r in manifest}) == expected_samples, "seed collision")
    require(len({(r["sample_id"], r["method"]) for r in rows}) == len(rows), "duplicate result row")
    require({r["method"] for r in rows} == {"otsu", "local_gaussian"}, "method set mismatch")
    expected_ids = {r["sample_id"] for r in manifest}
    require({r["sample_id"] for r in rows} == expected_ids, "manifest/result mismatch")
    timing = defaultdict(list)
    for row in read_csv(run_dir / "timings.csv"):
        require(int(row["elapsed_ns"]) > 0, "nonpositive runtime")
        timing[(row["sample_id"], row["method"])].append(row)
    require(set(timing) == {(r["sample_id"], r["method"]) for r in rows}, "timing key mismatch")
    computed = defaultdict(list)
    paired = defaultdict(dict)
    manifest_map = {r["sample_id"]: r for r in manifest}
    for row in rows:
        sid, method = row["sample_id"], row["method"]
        entry = manifest_map[sid]
        require(all(row[k] == v for k, v in entry.items()), f"manifest drift: {sid}")
        require(row["status"] == "ok", f"failed result: {sid}")
        with np.load(run_dir / row["artifact"], allow_pickle=False) as data:
            truth, pred, image = data["truth"], data[method], data["image"]
        require(truth.dtype == pred.dtype == bool and truth.shape == pred.shape == image.shape ==
                (config["image_size"], config["image_size"]), f"invalid arrays: {sid}")
        for array, key in [(truth, "truth_sha256"), (pred, "prediction_sha256"), (image, "image_sha256")]:
            require(array_hash(array) == row[key], f"array hash mismatch: {sid} {key}")
        counts = independent_counts(truth, pred)
        require(sum(counts.values()) == truth.size, "pixel count mismatch")
        for key, value in counts.items():
            require(int(row[key]) == value, f"confusion mismatch: {sid} {key}")
        measured = independent_scores(counts)
        for metric, value in measured.items():
            close(row[metric], value, f"metric mismatch: {sid} {metric}")
        close(measured["f1"], 2*measured["iou"]/(1+measured["iou"]), "Dice/IoU identity failed")
        tt = timing[(sid, method)]
        require(len(tt) == config["timing_repeats"], "timing repeat count mismatch")
        require({int(t["repeat"]) for t in tt} == set(range(config["timing_repeats"])), "timing repeat ID mismatch")
        close(row["runtime_ms"], statistics.median(int(t["elapsed_ns"])/1e6 for t in tt), "runtime median mismatch")
        computed[(row["condition_id"], method)].append(measured)
        paired.setdefault(row["condition_id"], {}).setdefault(sid, {})[method] = measured["iou"]
    summary = read_csv(run_dir / "summary.csv")
    require(len(summary) == expected_conditions*2, "summary count mismatch")
    require({(r["condition_id"], r["method"]) for r in summary} == set(computed), "summary keys mismatch")
    for row in summary:
        values = computed[(row["condition_id"], row["method"])]
        require(len(values) == int(row["n"]) == config["samples_per_condition"], "group size mismatch")
        for metric in ("iou", "precision", "recall", "f1"):
            close(row[metric+"_mean"], statistics.mean(v[metric] for v in values), "summary mean mismatch")
            close(row[metric+"_sd"], statistics.stdev(v[metric] for v in values), "summary SD mismatch")
        subset = [r for r in rows if r["condition_id"] == row["condition_id"] and r["method"] == row["method"]]
        close(row["runtime_ms_median"], statistics.median(float(r["runtime_ms"]) for r in subset), "summary runtime mismatch")
        require(int(row["iou_below_0_5_count"]) == sum(v["iou"] < .5 for v in values), "summary failure count mismatch")
    pair_rows = read_csv(run_dir / "paired.csv")
    require(len(pair_rows) == expected_conditions and {r["condition_id"] for r in pair_rows} == set(paired), "paired keys mismatch")
    for row in pair_rows:
        values = paired[row["condition_id"]]
        differences = [v["local_gaussian"]-v["otsu"] for v in values.values()]
        close(row["mean_iou_delta_local_minus_otsu"], statistics.mean(differences), "paired mean mismatch")
        close(row["delta_sd"], statistics.stdev(differences), "paired SD mismatch")
        require(int(row["n"]) == len(differences), "paired n mismatch")
        for key, count in [("local_wins", sum(v > 0 for v in differences)),
                           ("otsu_wins", sum(v < 0 for v in differences)), ("ties", sum(v == 0 for v in differences))]:
            require(int(row[key]) == count, "paired win count mismatch")
    overall = read_csv(run_dir / "overall.csv")
    require(len(overall) == 2 and {r["method"] for r in overall} == {"otsu", "local_gaussian"}, "overall keys mismatch")
    for row in overall:
        subset = [r for r in rows if r["method"] == row["method"]]
        close(row["macro_iou"], statistics.mean(float(r["iou"]) for r in subset), "overall IoU mismatch")
        close(row["macro_f1"], statistics.mean(float(r["f1"]) for r in subset), "overall F1 mismatch")
        close(row["median_runtime_ms"], statistics.median(float(r["runtime_ms"]) for r in subset), "overall runtime mismatch")
        require(int(row["n"]) == len(subset), "overall n mismatch")
        require(int(row["iou_below_0_5_count"]) == sum(float(r["iou"]) < .5 for r in subset), "overall failure count mismatch")
    claims = json.loads((run_dir / "claims.json").read_text())
    for key, table, id_field in [("overall", overall, "method"), ("paired_by_condition", pair_rows, "condition_id")]:
        require(len(claims[key]) == len(table), "claim count mismatch")
        table_map = {r[id_field]: r for r in table}
        for claim in claims[key]:
            require(claim[id_field] in table_map, "unknown claim identifier")
            for field, value in claim.items():
                if field == id_field:
                    continue
                close(value, table_map[claim[id_field]][field], "claim/table mismatch")
    failures = read_csv(run_dir / "failure_cases.csv")
    require(len(failures) == 2, "failure case count mismatch")
    for row in failures:
        expected = min((r for r in rows if r["method"] == row["method"]), key=lambda r: (float(r["iou"]), r["sample_id"]))
        require(row == expected, "failure selection mismatch")
    if regenerate:
        # Additional reproducibility test. Arithmetic above remains independent.
        from .core import Config, conditions, sample_seed, segment, synthetic_sample
        cfg = Config(**config)
        by_condition = {c["condition_id"]: c for c in conditions(cfg)}
        for entry in manifest:
            condition = by_condition[entry["condition_id"]]
            seed = sample_seed(cfg.master_seed, condition["condition_index"], int(entry["sample_index"]))
            require(seed == int(entry["seed"]), "seed derivation mismatch")
            image, truth, clipped = synthetic_sample(cfg, condition, seed)
            close(entry["clipped_fraction"], clipped, "clipping fraction mismatch")
            close(entry["foreground_fraction"], truth.mean(), "foreground fraction mismatch")
            with np.load(run_dir / entry["artifact"], allow_pickle=False) as saved:
                require(np.array_equal(saved["image"], image) and np.array_equal(saved["truth"], truth), "regeneration mismatch")
                for method in ("otsu", "local_gaussian"):
                    require(np.array_equal(saved[method], segment(image, method, cfg)), "prediction regeneration mismatch")
    root = Path(__file__).resolve().parent.parent
    source_matches = all(file_hash(root / path) == expected for path, expected in meta["source_sha256"].items())
    require(source_matches, "source differs from run metadata; rerun with current code")
    result = {"status": "passed", "samples_checked": expected_samples, "result_rows_checked": len(rows),
              "timing_observations_checked": sum(map(len, timing.values())),
              "independent_confusion_and_metrics": True, "summary_means_and_sd_checked": True,
              "source_hashes_match": source_matches, "all_images_and_predictions_regenerated": regenerate,
              "limits": "Shares NumPy and file loader; regeneration reuses generator/methods; not an independent implementation of either segmentation algorithm. Bootstrap endpoints are not independently reimplemented."}
    write_json(run_dir / "verification.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--regenerate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.run_dir, args.regenerate), indent=2))


if __name__ == "__main__":
    main()
