"""Derive tables, paired uncertainty, and figures from raw observations."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .core import METHODS, METRICS
from .io import read_csv, write_csv, write_json


COLORS = {"otsu": "#14647f", "local_gaussian": "#c15b20"}
LABELS = {"otsu": "Global Otsu", "local_gaussian": "Local Gaussian"}


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["condition_id"], row["method"])].append(row)
    summary = []
    for (cid, method), values in sorted(groups.items()):
        first = values[0]
        out = {k: first[k] for k in ["condition_id", "contrast", "noise_sigma", "gradient_amplitude", "size_class"]}
        out.update(method=method, n=len(values))
        for metric in METRICS:
            scores = [float(v[metric]) for v in values]
            out[f"{metric}_mean"] = statistics.mean(scores)
            out[f"{metric}_sd"] = statistics.stdev(scores)
        out["runtime_ms_median"] = statistics.median(float(v["runtime_ms"]) for v in values)
        out["iou_below_0_5_count"] = sum(float(v["iou"]) < .5 for v in values)
        summary.append(out)
    return summary


def paired_summary(rows, seed, repeats):
    groups = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        groups[row["condition_id"]][row["sample_id"]][row["method"]] = float(row["iou"])
    result = []
    for i, (cid, samples) in enumerate(sorted(groups.items())):
        differences = np.array([m["local_gaussian"] - m["otsu"] for _, m in sorted(samples.items())])
        rng = np.random.default_rng(np.random.SeedSequence([seed, 811, i]))
        bootstrap = differences[rng.integers(0, len(differences), (repeats, len(differences)))].mean(axis=1)
        low, high = np.quantile(bootstrap, [.025, .975])
        result.append({"condition_id": cid, "n": len(differences),
                       "mean_iou_delta_local_minus_otsu": float(differences.mean()),
                       "delta_sd": float(differences.std(ddof=1)),
                       "bootstrap_95_low": float(low), "bootstrap_95_high": float(high),
                       "local_wins": int((differences > 0).sum()),
                       "otsu_wins": int((differences < 0).sum()), "ties": int((differences == 0).sum())})
    return result


def report(run_dir):
    run_dir = Path(run_dir)
    if not (run_dir / "metadata.json").is_file():
        raise ValueError("run is incomplete: metadata.json is missing")
    config = json.loads((run_dir / "config.json").read_text())
    rows = read_csv(run_dir / "raw.csv")
    summary = summarize(rows)
    pairs = paired_summary(rows, config["master_seed"], config["bootstrap_repeats"])
    write_csv(run_dir / "summary.csv", summary)
    write_csv(run_dir / "paired.csv", pairs)
    overall = []
    for method in METHODS:
        subset = [r for r in rows if r["method"] == method]
        overall.append({"method": method, "n": len(subset),
                        "macro_iou": statistics.mean(float(r["iou"]) for r in subset),
                        "macro_f1": statistics.mean(float(r["f1"]) for r in subset),
                        "median_runtime_ms": statistics.median(float(r["runtime_ms"]) for r in subset),
                        "iou_below_0_5_count": sum(float(r["iou"]) < .5 for r in subset)})
    write_csv(run_dir / "overall.csv", overall)
    write_json(run_dir / "claims.json", {"overall": overall, "paired_by_condition": pairs,
               "qualification": "Fixed synthetic grid; image-level macro averages; not clinical or API validation."})
    figures = run_dir / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "savefig.facecolor": "white"})
    contrasts = config["contrasts"]
    gradients = config["gradient_amplitudes"]
    sizes = sorted(config["radius_ranges"])
    fig, axes = plt.subplots(len(sizes), len(gradients), figsize=(11, 4*len(sizes)),
                             squeeze=False, sharex=True, sharey=True, layout="constrained")
    for i, size in enumerate(sizes):
        for j, gradient in enumerate(gradients):
            ax = axes[i, j]
            for method in METHODS:
                for k, contrast in enumerate(contrasts):
                    subset = sorted([s for s in summary if s["method"] == method and s["size_class"] == size
                                     and float(s["gradient_amplitude"]) == gradient
                                     and float(s["contrast"]) == contrast], key=lambda s: float(s["noise_sigma"]))
                    x = np.array([float(s["noise_sigma"]) for s in subset])
                    y = np.array([s["iou_mean"] for s in subset])
                    sd = np.array([s["iou_sd"] for s in subset])
                    ax.plot(x, y, marker="o", ls=["--", "-", ":"][k % 3], color=COLORS[method],
                            label=f"{LABELS[method]}, contrast {contrast:g}")
                    ax.fill_between(x, np.maximum(0, y-sd), np.minimum(1, y+sd), color=COLORS[method], alpha=.09)
            ax.set(title=f"{size.capitalize()} objects | gradient {gradient:g}", ylim=(0, 1.04),
                   xlabel="Noise standard deviation", ylabel="Mean image IoU")
            ax.grid(alpha=.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
    fig.suptitle(f"Fixed-parameter robustness | {config['samples_per_condition']} independent images per condition\nShading: ±1 sample SD (clipped to [0, 1]); not confidence intervals", fontsize=14)
    fig.savefig(figures / "robustness.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    timing = [[float(r["runtime_ms"]) for r in rows if r["method"] == m] for m in METHODS]
    ax.boxplot(timing, tick_labels=[LABELS[m] for m in METHODS], showfliers=True)
    ax.set(yscale="log", ylabel="Per-image median runtime (ms, log scale)",
           title="Local wall-clock timing across the fixed synthetic grid\nIncludes smoothing and thresholding; excludes I/O")
    ax.grid(axis="y", alpha=.2)
    fig.savefig(figures / "runtime.png", dpi=160)
    plt.close(fig)
    worst = [min((r for r in rows if r["method"] == m), key=lambda r: (float(r["iou"]), r["sample_id"])) for m in METHODS]
    write_csv(run_dir / "failure_cases.csv", worst)
    fig, axes = plt.subplots(len(worst), 4, figsize=(11, 6), layout="constrained")
    for i, row in enumerate(worst):
        with np.load(run_dir / row["artifact"], allow_pickle=False) as data:
            image, truth, pred = data["image"], data["truth"], data[row["method"]]
        error = np.zeros((*truth.shape, 3)) + .94
        error[truth & pred] = (.15, .55, .48)
        error[~truth & pred] = (.85, .3, .1)
        error[truth & ~pred] = (.28, .36, .8)
        for ax, value, title in zip(axes[i], [image, truth, pred, error],
                                    [f"{row['sample_id']} | input", "Ideal ground truth",
                                     f"{LABELS[row['method']]} | IoU {float(row['iou']):.3f}", "TP teal · FP orange · FN blue"]):
            ax.imshow(value, cmap="gray", vmin=0, vmax=1)
            ax.set_title(title, fontsize=10)
            ax.axis("off")
    fig.suptitle("Lowest-IoU image for each method across the full experiment\nSelection is automatic; full sample IDs and settings are in failure_cases.csv", fontsize=13)
    fig.savefig(figures / "failure_cases.png", dpi=170)
    plt.close(fig)
    table = ["# Generated benchmark tables", "", "Mean ± sample SD over images; each method uses the same images.", "",
             "| Condition | Size | Contrast | Noise | Gradient | Otsu IoU | Local IoU |", "|---|---|---:|---:|---:|---:|---:|"]
    for cid in sorted({r["condition_id"] for r in summary}):
        by_method = {r["method"]: r for r in summary if r["condition_id"] == cid}
        s = by_method["otsu"]
        table.append(f"| {cid} | {s['size_class']} | {float(s['contrast']):g} | {float(s['noise_sigma']):g} | {float(s['gradient_amplitude']):g} | "
                     + " | ".join(f"{by_method[m]['iou_mean']:.4f} ± {by_method[m]['iou_sd']:.4f}" for m in METHODS) + " |")
    (run_dir / "tables.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    report(args.run_dir)
    print("Generated summary, paired intervals, claims, tables, and figures.")


if __name__ == "__main__":
    main()
