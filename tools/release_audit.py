"""Inspect the proposed public tree and record a bounded release manifest.

This is a useful heuristic check, not a guarantee that no secret or IP issue exists.
Run from the project root: python tools/release_audit.py
"""

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "release_audit.json"
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "runs"}
PATTERNS = {
    "github_token": re.compile(r"(?:gh" + r"[pousr]_[A-Za-z0-9]{20,}|github" + r"_pat_[A-Za-z0-9_]{20,})"),
    "private_key": re.compile(r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"AK" + r"IA[0-9A-Z]{16}"),
    "credential_assignment": re.compile(r'''(?i)(?:api_key|password|client_secret)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{16,}["']'''),
    "absolute_user_path": re.compile(r"(?i)(?:[A-Z]:[\\/]Us" + r"ers[\\/]|/ho" + r"me/|/Us" + r"ers/)"),
    "private_source_reference": re.compile("microstructai" + "-v3-web|PAT" + "END|Rheo" + "Scan|SAS" + "I_"),
}
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".in", ".yml", ".yaml", ".ini"}


def main():
    files, issues, excluded = [], [], []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            excluded.append(rel.as_posix())
            continue
        if path == OUTPUT:
            continue  # Manifest does not hash itself.
        if path.is_symlink():
            issues.append({"file": rel.as_posix(), "issue": "symlink"})
        if path.name.startswith(".env") or path.suffix in {".pem", ".key", ".docx", ".pdf"}:
            issues.append({"file": rel.as_posix(), "issue": "excluded file class"})
        raw = path.read_bytes()
        if path.suffix in TEXT_SUFFIXES or path.name in {".gitignore", ".gitattributes", "LICENSE"}:
            text = raw.decode("utf-8")
            for label, pattern in PATTERNS.items():
                if pattern.search(text):
                    issues.append({"file": rel.as_posix(), "issue": label})
        elif path.suffix == ".npz":
            import numpy as np
            with np.load(path, allow_pickle=False) as archive:
                if set(archive.files) != {"image", "truth", "otsu", "local_gaussian"}:
                    issues.append({"file": rel.as_posix(), "issue": "unexpected archive keys"})
                for key in archive.files:
                    if archive[key].dtype.kind not in "bf":
                        issues.append({"file": rel.as_posix(), "issue": "unexpected array type"})
        elif path.suffix == ".png":
            from PIL import Image
            with Image.open(path) as im:
                im.verify()
        elif path.suffix != ".csv":
            issues.append({"file": rel.as_posix(), "issue": "unreviewed file extension"})
        else:
            text = raw.decode("utf-8")
            for label, pattern in PATTERNS.items():
                if pattern.search(text):
                    issues.append({"file": rel.as_posix(), "issue": label})
        files.append({"path": rel.as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    result = {"status": "passed" if not issues else "needs_review", "files_scanned": len(files),
              "total_bytes": sum(f["bytes"] for f in files), "issues": issues,
              "excluded_paths": excluded, "file_manifest": files,
              "limitations": "Pattern scan and artifact schema inspection only; does not certify ownership, patent clearance, security, dependency integrity, or scientific validity. Human review and publication approval remain required."}
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"file_manifest", "excluded_paths"}}, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
