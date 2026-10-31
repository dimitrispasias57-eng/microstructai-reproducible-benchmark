"""Independent audit: no imports from segbench, SciPy, or scikit-image.

NumPy supplies array I/O and the documented random generator. Gaussian kernels,
ellipse membership, Otsu's objective, local thresholds, scalar confusion counts,
sample variance and bootstrap percentiles are calculated here separately.
"""
from collections import defaultdict
import csv
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("comparison_run", type=Path, help="Completed full default benchmark to compare with results/reference")
parser.add_argument("--output", type=Path, help="JSON audit result; defaults to comparison_run/independent_verification.json")
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
REF = ROOT/"results/reference"
NEW = args.comparison_run.resolve()
OUTPUT = args.output or NEW/"independent_verification.json"


def table(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check(actual, expected, message, tolerance=1e-12):
    if not math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{message}: {actual} != {expected}")


def mean(values):
    return math.fsum(values)/len(values)


def sd(values):
    mu = mean(values)
    return math.sqrt(math.fsum((x-mu)**2 for x in values)/(len(values)-1))


def median(values):
    v = sorted(values)
    mid = len(v)//2
    return v[mid] if len(v)%2 else (v[mid-1]+v[mid])/2


def percentile(values, p):
    v = sorted(values)
    position = (len(v)-1)*p
    low = int(math.floor(position))
    fraction = position-low
    return v[low]*(1-fraction) + v[min(low+1, len(v)-1)]*fraction


def blur(image, sigma):
    if not sigma:
        return image.astype(float).copy()
    radius = int(4*sigma + .5)
    kernel = [math.exp(-.5*(x/sigma)**2) for x in range(-radius, radius+1)]
    total = math.fsum(kernel)
    kernel = [x/total for x in kernel]
    result = image.astype(float).copy()
    for axis in (0, 1):
        pads = [(0, 0), (0, 0)]
        pads[axis] = (radius, radius)
        padded = np.pad(result, pads, mode="symmetric")
        result = np.zeros_like(result)
        for j, weight in enumerate(kernel):
            slices = [slice(None), slice(None)]
            slices[axis] = slice(j, j+image.shape[axis])
            result += weight*padded[tuple(slices)]
    return result


otsu_precision_checks = []


def otsu(image):
    if image.max() == image.min():
        return np.zeros_like(image, dtype=bool)
    counts, edges = np.histogram(image, bins=256)
    centers = (edges[1:]+edges[:-1])/2
    total = image.size
    total_sum = math.fsum(int(n)*float(c) for n,c in zip(counts,centers))
    best = (-1., 0)
    exact_best = (-1., 0)
    objectives = []
    left_count, left_sum = 0, 0.
    for split in range(255):
        left_count += int(counts[split])
        left_sum += int(counts[split])*float(centers[split])
        right_count = total-left_count
        if not left_count or not right_count:
            continue
        mean_difference = left_sum/left_count-(total_sum-left_sum)/right_count
        exact_objective = left_count*right_count*mean_difference**2
        # scikit-image 0.25.2 stores histogram weights as float32, including
        # their product. Reproduce that documented implementation arithmetic.
        objective = float(np.float32(left_count)*np.float32(right_count))*mean_difference**2
        objectives.append((split,exact_objective))
        if exact_objective > exact_best[0]:
            exact_best = (exact_objective,split)
        if objective > best[0]:
            best = (objective, split)
    mask = image > centers[best[1]]
    exact_mask = image > centers[exact_best[1]]
    loss = (exact_best[0]-dict(objectives)[best[1]])/exact_best[0]
    assert loss <= 1e-6
    otsu_precision_checks.append({'pixel_differences':int(np.count_nonzero(mask!=exact_mask)),
                                 'relative_objective_loss':loss})
    return mask


def regenerate(cfg, cond, seed):
    rng = np.random.Generator(np.random.PCG64(seed))
    n = cfg["image_size"]
    ys, xs = np.indices((n, n))
    mask = np.zeros((n, n), bool)
    for _ in range(cfg["object_count"]):
        cy, cx = rng.uniform(0, n-1, 2)
        major = rng.uniform(*cfg["radius_ranges"][cond[3]])
        minor = major*rng.uniform(.65, 1.)
        angle = rng.uniform(0, np.pi)
        cosine, sine = math.cos(angle), math.sin(angle)
        a = (cosine/major)**2 + (sine/minor)**2
        b = cosine*sine*(1/major**2-1/minor**2)
        c = (sine/major)**2 + (cosine/minor)**2
        dx, dy = xs-cx, ys-cy
        mask |= a*dx**2 + 2*b*dx*dy + c*dy**2 <= 1.
    image = cfg["background"] + cond[0]*blur(mask, cfg["optical_blur_sigma"])
    image += cond[2]*(xs/(n-1)-.5)
    image += rng.normal(0., cond[1], (n, n))
    clipping = np.count_nonzero((image<0)|(image>1))/image.size
    return np.clip(image, 0, 1).astype(np.float32), mask, clipping


cfg = json.loads((REF/"config.json").read_text())
all_conditions = list(itertools.product(cfg["contrasts"], cfg["noise_sigmas"],
                                       cfg["gradient_amplitudes"], sorted(cfg["radius_ranges"])))
rows = table(REF/"raw.csv")
new_rows = table(NEW/"raw.csv")
manifest = table(REF/"manifest.csv")
assert len(rows) == len(new_rows) == 960 and len(manifest) == 480
for old, new in zip(rows,new_rows):
    for key in old:
        if key != "runtime_ms":
            assert old[key] == new[key], (key,old["sample_id"])
for filename in ("manifest.csv", "paired.csv", "tables.md", "config.json"):
    # Text generated on Windows and Linux can differ only in newline bytes.
    assert (REF/filename).read_text(encoding="utf-8") == (NEW/filename).read_text(encoding="utf-8"), filename
for filename in ("summary.csv", "overall.csv", "failure_cases.csv"):
    for old, new in zip(table(REF/filename), table(NEW/filename)):
        for key in old:
            if "runtime" not in key:
                assert old[key] == new[key], (filename, key)

by_sample = defaultdict(dict)
for row in rows:
    by_sample[row["sample_id"]][row["method"]] = row
groups = defaultdict(list)
counts_by_sample = {}
max_image_error = 0.
independent_mask_differences = {"otsu": 0, "local_gaussian": 0}
exact_clean_arrays = 0
for entry in manifest:
    sid = entry["sample_id"]
    ci, si = int(entry["condition_index"]), int(entry["sample_index"])
    assert ci in range(len(all_conditions)) and si in range(cfg["samples_per_condition"])
    cond = all_conditions[ci]
    assert [float(entry[k]) for k in ("contrast","noise_sigma","gradient_amplitude")] == list(cond[:3])
    assert entry["size_class"] == cond[3]
    seed = int(np.random.SeedSequence([cfg["master_seed"],ci,si]).generate_state(1,dtype=np.uint64)[0])
    assert seed == int(entry["seed"])
    with np.load(REF/entry["artifact"],allow_pickle=False) as z:
        data = {k:z[k] for k in z.files}
    with np.load(NEW/entry["artifact"],allow_pickle=False) as z:
        assert set(z.files) == set(data)
        for key in z.files:
            assert np.array_equal(data[key],z[key]), (sid,key)
            exact_clean_arrays += 1
    own_image, own_mask, clipped = regenerate(cfg,cond,seed)
    assert np.array_equal(data["truth"],own_mask), (sid,"independent ellipse mask")
    error = float(np.max(np.abs(own_image.astype(float)-data["image"].astype(float))))
    max_image_error = max(max_image_error,error)
    assert error <= 1e-7, (sid,error)
    check(entry["clipped_fraction"],clipped,"clipping")
    check(entry["foreground_fraction"],float(own_mask.mean()),"foreground fraction")
    smooth = blur(data["image"],cfg["preprocess_sigma"])
    own_predictions = {"otsu":otsu(smooth),
                       "local_gaussian":smooth > blur(smooth,(cfg["local_block_size"]-1)/6)-cfg["local_offset"]}
    for method in ("otsu","local_gaussian"):
        difference = int(np.count_nonzero(own_predictions[method] != data[method]))
        independent_mask_differences[method] += difference
        assert difference == 0,(sid,method,difference)
        counts = {"tp":0,"fp":0,"fn":0,"tn":0}
        for truth,pred in zip(data["truth"].ravel().tolist(),data[method].ravel().tolist()):
            counts[("t" if truth==pred else "f")+("p" if pred else "n")] += 1
        row = by_sample[sid][method]
        for key,value in counts.items():
            assert int(row[key])==value,(sid,key)
        tp,fp,fn,tn = (counts[k] for k in ("tp","fp","fn","tn"))
        measured = {"iou":tp/(tp+fp+fn),"precision":tp/(tp+fp) if tp+fp else 0.,
                    "recall":tp/(tp+fn),"f1":2*tp/(2*tp+fp+fn)}
        for key,value in measured.items():
            check(row[key],value,f"{sid} {method} {key}")
        groups[(row["condition_id"],method)].append(measured)
    if si == 19:
        print(f"Independent reconstruction and arithmetic passed c{ci:02d}",flush=True)

for row in table(REF/"summary.csv"):
    values = groups[row["condition_id"],row["method"]]
    for key in ("iou","precision","recall","f1"):
        check(row[key+"_mean"],mean([v[key] for v in values]),"summary mean")
        check(row[key+"_sd"],sd([v[key] for v in values]),"sample SD")

bootstrap_max_error = 0.
for i,row in enumerate(table(REF/"paired.csv")):
    cid = row["condition_id"]
    samples = sorted(sid for sid in by_sample if sid.startswith(cid+"_"))
    differences = [float(by_sample[sid]["local_gaussian"]["iou"])-float(by_sample[sid]["otsu"]["iou"]) for sid in samples]
    rng = np.random.default_rng(np.random.SeedSequence([cfg["master_seed"],811,i]))
    # Same specified resampling stream; separate scalar summation and quantile implementation.
    indices = rng.integers(0,len(differences),(cfg["bootstrap_repeats"],len(differences)))
    bootstrap = [math.fsum(differences[int(j)] for j in index)/len(differences) for index in indices]
    for key,p in (("bootstrap_95_low",.025),("bootstrap_95_high",.975)):
        expected = percentile(bootstrap,p)
        bootstrap_max_error = max(bootstrap_max_error,abs(expected-float(row[key])))
        check(row[key],expected,"independent bootstrap endpoint")
    check(row["mean_iou_delta_local_minus_otsu"],mean(differences),"paired mean")
    check(row["delta_sd"],sd(differences),"paired SD")

for run in (REF,NEW):
    timing = defaultdict(list)
    positions = defaultdict(list)
    for row in table(run/"timings.csv"):
        timing[row["sample_id"],row["method"]].append(int(row["elapsed_ns"])/1e6)
        positions[row["sample_id"],row["repeat"]].append(int(row["position"]))
    assert all(sorted(v)==[0,1] for v in positions.values())
    for row in table(run/"raw.csv"):
        check(row["runtime_ms"],median(timing[row["sample_id"],row["method"]]),"timing median")
    for row in table(run/"overall.csv"):
        values = [r for r in table(run/"raw.csv") if r["method"]==row["method"]]
        check(row["macro_iou"],mean([float(r["iou"]) for r in values]),"overall macro IoU")
        check(row["macro_f1"],mean([float(r["f1"]) for r in values]),"overall macro F1")
        check(row["median_runtime_ms"],median([float(r["runtime_ms"]) for r in values]),"overall timing")

result = {"status":"passed","images":480,"method_evaluations":960,"exact_arrays_between_runs":exact_clean_arrays,
          "reference_and_comparison_accuracy_identical":True,"independent_ground_truth_masks_identical":True,
          "independent_generated_image_max_abs_error":max_image_error,
          "independent_segmentation_pixel_differences":independent_mask_differences,
          "independent_bootstrap_endpoints":48,"bootstrap_max_abs_error":bootstrap_max_error,
          "otsu_float32_vs_float64":{'images_with_pixel_differences':sum(x['pixel_differences']>0 for x in otsu_precision_checks),
                                     'total_pixel_differences':sum(x['pixel_differences'] for x in otsu_precision_checks),
                                     'max_relative_objective_loss':max(x['relative_objective_loss'] for x in otsu_precision_checks)},
          "statistics_tolerance":1e-12,"independent_image_tolerance":1e-7,
          "reference_overall":table(REF/"overall.csv"),"comparison_overall":table(NEW/"overall.csv"),
          "limitations":"Same AI reviewer, new audit code; shares NumPy RNG/I/O. Independent arithmetic/kernel implementations, not independent human peer review. Clean environment is a fresh venv on the same Windows host, not a fresh OS."}
OUTPUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
