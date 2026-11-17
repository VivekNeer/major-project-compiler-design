# Project Phase-II Report — LaTeX source

Report: *Benchmarking Phase Ordering Trade-offs in a Custom Compiler Infrastructure using MiBench*
(Sahyadri College of Engineering & Management, Dept. of CSE, VTU Phase-II template).

## Build

Any TeX Live 2023+ works (no BibTeX step; the bibliography is inline):

    pdflatex report && pdflatex report && pdflatex report

or upload this folder to Overleaf and compile `report.tex` with pdfLaTeX.
The reference build used TeX Live 2025 from nix
(`nix build nixpkgs#texliveMedium`, then `<store-path>/bin/pdflatex`).

## Before submitting — fill in / verify

All names are macros at the top of `report.tex`:

- `\UsnA` … `\UsnD` — the four USNs (currently `4SF23CSXXX` placeholders)
- `\AcademicYear`, `\Semester` — currently `2026 - 27`, `VII`
- `\GuideName`, `\GuideDesignation` — Dr. Suhas A Bhyratae, Associate Professor (from the IEEE paper)
- `\CoordinatorName`, `\CoordinatorDesignation` — Ms. Prapulla G (taken from the sample report; verify)
- `\HodName`, `\PrincipalName` — taken from the sample report; verify

## Layout

- `report.tex` — preamble, page styles, front matter order
- `chapters/00_*.tex` — cover, certificate, declaration, abstract, acknowledgement
- `chapters/01_…06_*.tex` — the six chapters; `07_references.tex`; `08_appendix.tex`
- `figures/` — logos, benchmark plots (from `python -m compiler.main --benchmark-all`),
  custom charts (`scripts/make_charts.py`), GUI screenshots (`scripts/take_screenshots.py`,
  needs the web app running on :8080 and Playwright)
- `data/` — JSON summaries of the benchmark numbers used in the tables

Run the two scripts from the `major-project-compiler-design/` directory with
`PYTHONPATH=.` so that the `compiler` package is importable.
