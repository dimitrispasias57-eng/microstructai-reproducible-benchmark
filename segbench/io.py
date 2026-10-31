"""Small, explicit artifact I/O helpers."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError("cannot write an empty table without a schema")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_hash(array):
    """Hash canonical little-endian C-order bytes plus dtype and shape."""
    arr = np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"), copy=False))
    header = f"{arr.dtype.str}:{arr.shape}:".encode("ascii")
    return hashlib.sha256(header + arr.tobytes()).hexdigest()
