# Final quality and safety audit

> Publication update: the owner explicitly approved publishing this separate audited project after this local audit. Historical statements below about publication being unauthorized, the repository remaining local, or hosted CI being unexecuted describe the audit-time state. The current [repository](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark) and [Actions runs](https://github.com/dimitrispasias57-eng/microstructai-reproducible-benchmark/actions/workflows/tests.yml) show the publication state. The article remains an AI-assisted draft awaiting substantive author review; application-readiness limitations still apply.

Audit date: 31 October 2026. **Technical benchmark candidate: PASS after remediation. SearchApi application readiness: FAIL / owner review outstanding. Publication: NOT AUTHORIZED.** These are separate decisions. Passing reproducibility checks does not establish personal authorship or API benchmarking experience.

This was a fresh computational audit with a separately written numerical implementation, performed by the same AI reviewer. It was not an independent human review. The environments were clean virtual environments on the existing Windows host, not fresh operating systems. Findings apply to the inventoried candidate, default configuration, inspected source revision and dependency-advisory snapshot.

## Requested checks

| # | Check | Result | Evidence and boundary |
|---|---|---|---|
| 1 | Clean rerun and reproducibility | PASS for accuracy and statistics | Two fresh environments completed the entire benchmark. All 480 inputs, labels and both predictions matched the original; 960 metric rows and 24 paired intervals reproduced. Timing was remeasured and differs, as expected; original times were real observations, not portable constants. |
| 2 | Formulas, generation, statistics, comparisons and conclusions | PASS within stated design | Separate geometry, Gaussian, threshold, count, SD and bootstrap calculations agree. Forty-eight interval endpoints differ by at most 1.11e-16. Fixed-parameter comparison, confounded size/occupancy, clipping and pointwise uncertainty are disclosed. |
| 3 | Article claims and output agreement | PASS after corrections | Every condition table, selected paired comparison, headline, example count, percentage range and runtime is traced to final output. Added float32 Otsu and 55-pixel Gaussian-support details. Replaced stale timing/test numbers with the executed candidate values. AI assistance remains disclosed. |
| 4 | Proprietary code, private data, credentials and confidential material | PASS for inspected evidence; bounded assurance | All 43 files at a fixed private-source revision were compared in memory. No identical files, substantial identical functions, 80-token sequences or long copied lines were detected. All data are independently regenerated synthetic scenes. Credential/path scans and archive/PNG inspections found no release issue. This cannot certify conceptual IP, unseen material or ownership obligations. |
| 5 | Dependencies, licenses and release files | PASS after fixes | Original candidate failed security review. Four packages/tool versions were updated. All 23 final pins have public artifacts, verified wheel digests and no currently returned OSV advisories. Installed license files were inventoried. Fresh code/data use proposed MIT; no dependencies, datasets or publisher PDFs are redistributed. |
| 6 | No inherited private Git history | PASS | Final directory is an isolated, newly initialized local Git root with no commits, refs, remotes, objects, alternates, worktrees or submodules. The delivery ZIP excludes Git internals. Surrounding-workspace history is outside the release boundary. |
| 7 | Standalone public-ready reproduction | PASS on tested Windows environment | Full run succeeded with network connections blocked after public dependency installation. No private source, dataset, credentials or account was required. Candidate, environment and standard-library module origins were checked. Other OS executions remain untested. |
| 8 | Honest limitations and real executed tests | PASS | 52 tests passed in the final environment; full logs and raw timings are retained. Synthetic scope, fixed parameters, no real biological validation, uncertainty limits, machine effects and audit independence are explicit. |
| 9 | SearchApi requirements | FAIL for a ready-to-submit application; research artifact foundation passes | Long-form article, real code/data and an exactly reproducible accuracy number are present. The employer asks for a piece the applicant wrote. The current draft still needs the owner's substantive review and editing; this audit cannot attest that happened. No live API study, service measurements over time, or hands-on no-code/agent comparison was executed. |
| 10 | Final report and unresolved concerns | PASS | This report distinguishes tested facts, repaired failures, remaining application gaps and the explicit publication boundary. |

## Reproduced headline values

| Method | Mean image IoU | Mean image F1 | IoU < 0.5 | Final median ms |
|---|---:|---:|---:|---:|
| Global Otsu | 0.5817012037935931 | 0.6393677567189995 | 212 / 480 | 0.30215 |
| Local Gaussian | 0.6427029660041174 | 0.7477564109222271 | 124 / 480 | 0.44900 |

The source is [overall.csv](../results/reference/overall.csv). These are means of image ratios, not pooled-pixel scores. The global ranking reverses in several conditions. [Full article](ARTICLE.md), [all conditions](../results/reference/tables.md), [execution and independence details](VALIDATION.md), [independent calculations](audit/independent_science.json).

## Failures fixed during the audit

The original security pins are superseded: Pillow 12.3.0 → 13.0.0; Pygments 2.19.2 → 2.21.0; pytest 8.4.2 → 9.0.3; pip 25.0.1 → 26.2.2. Scientific-library versions, generator, seeds, parameters and evaluation code stayed unchanged. Example upstream records: [Pillow release](https://github.com/python-pillow/Pillow/releases/tag/13.0.0), [Pygments fix release](https://github.com/pygments/pygments/releases/tag/2.20.0), [pytest fix release](https://github.com/pytest-dev/pytest/releases/tag/9.0.3). The entire final environment was rerun after these changes.

The article now distinguishes Gaussian sigma from actual finite support and specifies the Otsu floating-point behavior. Neither discovery invalidates the configured-library comparison. Three differing pixels under an alternative arithmetic implementation are disclosed rather than silently redefining the benchmark. Test duration and runtime claims now describe the final candidate, while historical run values remain in the validation record.

## SearchApi assessment and remaining work

The [official Technical Researcher / Writer posting](https://jobs.ashbyhq.com/SearchApi/5202d0e3-e0c4-4a77-82e2-a8982f270de3), checked on the audit date, asks for personally written technical work with reproducible supporting code/data and emphasizes hands-on API/tool comparisons and repeated measurement. This project supplies the numerical artifact and honest negative results. It cannot establish the owner's authorship, understanding or broader experience by itself.

Before representing the article as a writing sample, the owner needs to review the methods and evidence, edit the article in their own voice, confirm their contribution and retain accurate AI disclosure. A complete API demonstration remains future work: fixed versioned queries, interleaved providers, success and quality definitions, latency distributions, retries, timeouts, concurrency, rate limits, cost per useful success and repeated measurements across days. No API provider was tested, and no API performance claims are justified here. API experience is a role-fit gap, not a claim that an image benchmark can never be a valid writing sample.

Before release, the owner must decide the proposed MIT license and any employer/institution/confidentiality obligations that cannot be inferred from code comparison. No known leak was found, but this audit cannot provide absolute absence-of-IP or legal certification. A separate human peer reviewer and additional operating-system executions would strengthen evidence; neither is falsely reported as completed or treated as a hidden completed check.

## Publication boundary

**Not every requested readiness check passes: check 9 remains unresolved. Do not publish or submit this candidate as a completed personal writing sample yet.** The corrected project and honest application draft are prepared locally for review. No GitHub repository was created, pushed, made public or shared by this audit. No project or private-source files were uploaded to package/advisory services; only public package names and versions were queried. Private source comparison was read-only and its source contents were not saved into the candidate.

Publication requires the owner's explicit approval after review. The approval must identify this final candidate, not the superseded original archive. Private audit notes, application draft, wheel caches, virtual environments and the surrounding workspace are outside the publication boundary. [Release inventory](release_audit.json) and [release rules](RELEASE_REVIEW.md) describe exactly what is included.
