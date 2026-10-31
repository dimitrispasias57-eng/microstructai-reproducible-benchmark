"""Run a fixed experiment, retaining every image, mask, row, and timing repeat."""

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

import numpy as np

from .core import Config, METHODS, conditions, confusion, sample_seed, scores, segment, synthetic_sample
from .io import array_hash, file_hash, write_csv, write_json


def run(config, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}; choose a fresh directory")
    output.mkdir(parents=True)
    (output / "data").mkdir()
    rows, times, manifest = [], [], []
    started = datetime.now(timezone.utc).isoformat()
    config_hash = __import__("hashlib").sha256(json.dumps(config.as_dict(), sort_keys=True).encode()).hexdigest()
    write_json(output / "config.json", config.as_dict())
    order_rng = np.random.default_rng(np.random.SeedSequence([config.master_seed, 923]))
    for condition in conditions(config):
        for sample_index in range(config.samples_per_condition):
            seed = sample_seed(config.master_seed, condition["condition_index"], sample_index)
            sample_id = f'{condition["condition_id"]}_s{sample_index:03d}'
            image, truth, clipped = synthetic_sample(config, condition, seed)
            image.setflags(write=False)
            truth.setflags(write=False)
            predictions = {}
            # One untimed warm-up per method per image, then interleaved random order.
            for method in METHODS:
                predictions[method] = segment(image, method, config)
            durations = {method: [] for method in METHODS}
            for repeat in range(config.timing_repeats):
                for position, method in enumerate(order_rng.permutation(METHODS)):
                    begin = time.perf_counter_ns()
                    prediction = segment(image, method, config)
                    elapsed = time.perf_counter_ns() - begin
                    if not np.array_equal(prediction, predictions[method]):
                        raise RuntimeError(f"nondeterministic prediction: {sample_id} {method}")
                    durations[method].append(elapsed/1e6)
                    times.append({"sample_id": sample_id, "method": method,
                                  "repeat": repeat, "position": position, "elapsed_ns": elapsed})
            artifact = f"data/{sample_id}.npz"
            np.savez_compressed(output / artifact, image=image, truth=truth, **predictions)
            entry = {"sample_id": sample_id, **condition, "sample_index": sample_index,
                     "seed": seed, "artifact": artifact, "image_sha256": array_hash(image),
                     "truth_sha256": array_hash(truth), "foreground_fraction": float(truth.mean()),
                     "clipped_fraction": clipped}
            manifest.append(entry)
            for method in METHODS:
                counts = confusion(truth, predictions[method])
                rows.append({**entry, "method": method, "status": "ok", **counts, **scores(counts),
                             "runtime_ms": statistics.median(durations[method]),
                             "prediction_sha256": array_hash(predictions[method])})
        print(f'Completed {condition["condition_id"]}', flush=True)
    write_csv(output / "raw.csv", rows)
    write_csv(output / "timings.csv", times)
    write_csv(output / "manifest.csv", manifest)
    root = Path(__file__).resolve().parent.parent
    sources = {p.relative_to(root).as_posix(): file_hash(p)
               for p in sorted((root / "segbench").glob("*.py"))}
    metadata = {
        "schema_version": 1, "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "python_implementation": platform.python_implementation(),
        "os": platform.system(), "os_release": platform.release(), "architecture": platform.machine(),
        "processor": platform.processor(), "logical_cpu_count": os.cpu_count(),
        "packages": dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())),
        "thread_environment": {k: os.environ.get(k, "unset") for k in
                               ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]},
        "random_generator": "NumPy PCG64", "config_sha256": config_hash,
        "source_sha256": sources, "sample_count": len(manifest), "method_count": len(METHODS),
        "timing_scope": "input validation, float64 conversion, common smoothing, threshold, Boolean mask",
        "timing_excludes": "imports, image synthesis, file I/O, metrics, equality checks, plots",
        "timing_protocol": "one warm-up per method/image; randomized interleaved repeats; median per image",
        "machine_privacy": "no hostname, username, home path, IP, environment dump, or device identifier",
        "synthetic_only": True,
    }
    write_json(output / "metadata.json", metadata)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/default.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        config = Config(**json.loads(args.config.read_text(encoding="utf-8")))
        run(config, args.output)
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"Benchmark stopped: {exc}\n")


if __name__ == "__main__":
    main()
