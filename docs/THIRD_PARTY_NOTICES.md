# Dependency and authorship notes

This directory contains newly written project code, documentation, and generated synthetic artifacts. It does not vendor dependency source trees, wheels, trained weights, external images, or research application code. The proposed MIT license covers the new project only, subject to owner approval before public release; it does not relicense any dependency or published paper.

The installed packages were inspected using their distribution metadata. The exact environment is pinned in `requirements.txt` and recorded in the run's `metadata.json`. These are summaries of the packages' declared licenses, not substitutes for their complete license texts. See the linked release metadata and the `licenses` or license files in each installed `.dist-info` directory.

| Dependency | Tested version | Declared license / qualification |
|---|---|---|
| [NumPy](https://pypi.org/project/numpy/2.5.4/) | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 (metadata expression); wheels can contain additional runtime components |
| [SciPy](https://pypi.org/project/scipy/1.18.1/) | 1.18.1 | BSD-family; complete distribution includes bundled-component notices |
| [scikit-image](https://pypi.org/project/scikit-image/0.25.2/) | 0.25.2 | BSD-family with per-file notices |
| [Matplotlib](https://pypi.org/project/matplotlib/3.11.2/) | 3.11.2 | Matplotlib license agreement, PSF-derived; included fonts and other components retain their notices |
| [pytest](https://pypi.org/project/pytest/9.0.3/) | 9.0.3 | MIT |
| [colorama](https://pypi.org/project/colorama/0.4.6/) | 0.4.6 | BSD-family |
| [contourpy](https://pypi.org/project/contourpy/1.4.0/) | 1.4.0 | BSD-3-Clause |
| [cycler](https://pypi.org/project/cycler/0.12.1/) | 0.12.1 | BSD-family |
| [fonttools](https://pypi.org/project/fonttools/4.66.1/) | 4.66.1 | MIT |
| [ImageIO](https://pypi.org/project/imageio/2.37.4/) | 2.37.4 | BSD-2-Clause |
| [iniconfig](https://pypi.org/project/iniconfig/2.3.0/) | 2.3.0 | MIT |
| [kiwisolver](https://pypi.org/project/kiwisolver/1.5.1/) | 1.5.1 | BSD-family |
| [lazy-loader](https://pypi.org/project/lazy-loader/0.4/) | 0.4 | BSD-3-Clause |
| [networkx](https://pypi.org/project/networkx/3.6.1/) | 3.6.1 | BSD-3-Clause |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [Pillow](https://pypi.org/project/pillow/13.0.0/) | 13.0.0 | MIT-CMU |
| [pluggy](https://pypi.org/project/pluggy/1.6.0/) | 1.6.0 | MIT |
| [Pygments](https://pypi.org/project/pygments/2.21.0/) | 2.21.0 | BSD-2-Clause |
| [pyparsing](https://pypi.org/project/pyparsing/3.3.3/) | 3.3.3 | MIT |
| [python-dateutil](https://pypi.org/project/python-dateutil/2.9.0.post0/) | 2.9.0.post0 | Dual Apache/BSD |
| [six](https://pypi.org/project/six/1.17.0/) | 1.17.0 | MIT |
| [tifffile](https://pypi.org/project/tifffile/2025.10.4/) | 2025.10.4 | BSD-3-Clause |

The final environment uses [pip 26.2.2](https://pypi.org/project/pip/26.2.2/) (MIT) as pinned installation tooling. The complete requirements file has 23 pins including pip. The original pip 25.0.1 installer, Pillow 12.3.0, Pygments 2.19.2 and pytest 8.4.2 had published security advisories and were replaced before this final run. The current OSV query returned no known advisories for any of the 23 final pins; this is a database snapshot, not a security guarantee. See [audit details](FINAL_AUDIT.md). GitHub Actions checkout and setup-python are external MIT-licensed actions referenced by the workflow, not vendored here. No dependency license conflict was identified in this non-vendored source-and-synthetic-data release. This inspection is not a complete legal audit of binary dependencies or a patent-clearance opinion. If future releases redistribute wheels or executable bundles, review all bundled license texts and associated obligations before release.

The initial scientific package pins were revised before the first benchmark run to use locally cached compatible wheels, after network downloads stalled. Before that original run, all 22 installed dependency wheel contents were checked against their official PyPI SHA-256 values; the local-only verification record lists each filename and digest. No experimental parameter was adjusted after observing evaluation scores.

All prose is an AI-assisted draft for the owner's review. A link to a published scientific paper in application materials denotes coauthored work, not sole authorship, and no publisher PDF is redistributed in this project.
