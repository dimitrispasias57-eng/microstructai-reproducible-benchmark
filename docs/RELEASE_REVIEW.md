# Proposed public-release review

> Publication update: the owner explicitly approved publishing this separate audited project after this local audit. Historical statements below about publication being unauthorized, the repository remaining local, or hosted CI being unexecuted describe the audit-time state. The current [repository](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark) and [Actions runs](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark/actions/workflows/tests.yml) show the publication state. The article remains an AI-assisted draft awaiting substantive author review; application-readiness limitations still apply.

Status: **local review candidate; publication and owner scientific review are pending**. This document records the release boundary. It does not grant publication approval.

## What is in scope

Only this new directory is proposed for release: fresh benchmark code, tests, fixed settings, synthetic arrays, generated CSV tables and charts, dependency pins, documentation, and a test workflow. The article is explicitly an AI-assisted draft for the owner's review. The suggested project license is MIT, subject to the owner's approval of the new material.

The benchmark has no dependency on a private repository. No original source files, original Git history, real biological images, unpublished manuscripts, collaborator data, specialized research algorithms, or private calibration settings were copied into this directory. No existing private repository was modified, forked, or made public.

## Audit procedure

1. Inspect the full proposed file inventory, not just the README.
2. Scan text and CSV files for selected credential formats, private keys, credential assignments, absolute home paths, and private source identifiers.
3. Inspect every NPZ archive with `allow_pickle=False`, require the four documented numeric/Boolean arrays, and verify its evaluated arrays against the synthetic generation procedure.
4. Open the generated PNG figures; verify that they show only synthetic images and aggregate charts.
5. Review dependency metadata and provenance, confirm that no dependencies are vendored, and retain the proposed project license separately from third-party licenses.
6. Save a SHA-256 inventory of every candidate file in `release_audit.json`. The inventory excludes itself, Git internals, virtual environments, caches, and locally repeated runs.

Run `python tools/release_audit.py` from the project root. Its [JSON result](release_audit.json) records the actual scan outcome, exact file count, sizes, issues, and hashes. Read that executed artifact for the current result; any later file change requires a fresh scan. The synthetic provenance audit is independently recorded in [verification.json](../results/reference/verification.json).

## Privacy and rights decisions

- All exported data are mathematical synthetic scenes; no donor or patient images were used.
- Metadata records software versions and generic machine descriptors. It omits usernames, hostnames, IP addresses, home paths, device identifiers, and arbitrary environment variables.
- No tokens or credentials are needed by the benchmark. `.gitignore` excludes environment files, keys, caches and virtual environments; the audit checks the staged-candidate contents separately.
- Original research source licensing was not relied upon because no original source was redistributed. Public methods are used through installed dependencies. The [dependency notes](THIRD_PARTY_NOTICES.md) record declared licenses and the limits of that review.
- No publisher PDF or third-party dataset is included. Public references are linked and paraphrased.
- Private investigation notes, application drafts, download caches and the execution environment are kept in sibling local directories and are outside this release candidate.

## Remaining review and publication boundary

The owner should review the scientific interpretation, authorship disclosure, code, proposed MIT license, and application statements before approving publication. Pattern matching cannot prove absence of all secrets or confidential ideas, and dependency metadata is not a comprehensive legal or security certification. No license conflict was identified for the freshly written, non-vendored release; ownership approval and any institution-specific obligations remain the owner's review items.

A fresh, empty Git root was initialized locally inside this candidate during the audit. It has no commits or remotes; no private history was imported. Publication remains subject to explicit approval. Do not publish the surrounding workspace. Exact GitHub publication commands are supplied separately in the local review package. No new GitHub repository was created or pushed during preparation. Hosted CI remains unexecuted until a repository is created.

The final audit repaired dependency-security findings and separately checked the numerical methods. Read [FINAL_AUDIT.md](FINAL_AUDIT.md) for the PASS/FAIL decisions and application-readiness gap. The original review archive is superseded.
