# Project Phase-II Report — LaTeX source

Report: *Benchmarking Phase Ordering Trade-offs in a Custom Compiler Infrastructure using MiBench*
(Sahyadri College of Engineering & Management, Dept. of CSE, VTU Phase-II template 2026-27).

## Build

    ./build.sh            # team copy + four individual copies -> out/
    ./build.sh team       # team copy only
    ./build.sh C          # individual copy for student C (A..D, see report.tex)

`build.sh` needs `pdflatex` (TeX Live 2023+) on PATH, or `TEXBIN=<dir>` pointing at
a TeX Live `bin` directory. No BibTeX step; the bibliography is inline. The reference
build used TeX Live 2025 from nix (`nix build nixpkgs#texliveMedium`).

Manual build of the team copy: `pdflatex report` three times.
Manual build of an individual copy:

    pdflatex -jobname=report_Manas_S "\def\Individual{C}\input{report.tex}"

The individual copy differs only in the certificate, declaration and
acknowledgement (one name, I/me wording); the cover lists all team members in every copy, exactly as in the department's sample pair.

## Names and placeholders

All names are macros at the top of `report.tex`: students and USNs, guide, the two
project coordinators (`\CoordinatorTwo`, `\CoordinatorName`), HOD, principal, year,
semester. Verify spellings against the department's current list before submission.

## Structure (follows the official template `prism-uploads/PROJECT_PHASE___II__REPORT_LaTeX_CSE-2.pdf`)

- Front matter: cover, certificate, declaration, abstract (+keywords), acknowledgement, TOC, LoF, LoT
- 1 Introduction · 2 Literature Survey · 3 Problem Formulation · 4 Project Design and Implementation
- 5 Results and Discussion: 5.1 Performance Evaluation (experimental setup + empirical study),
  5.2 FR results, 5.3 NFR results, 5.4 Result Analysis and Discussion, 5.5 Snapshots of the Results,
  5.6 Societal Impact, 5.7 Technology Readiness Level, 5.8 SDG Mapping
- 6 Conclusion and Future Scope: 6.1 Conclusion (6.1.1 Limitations), 6.2 Future Scope
- References
- APPENDIX A Plagiarism Report Front Page · B Paper Publication Details · C Paper Copy ·
  D Code Snippets of Major Modules (verbatim excerpts from the compiler repository)

## Files

- `report.tex` — preamble, name macros, team/individual switch, page styles
- `chapters/` — one file per front-matter page and per chapter; `08_appendix.tex` holds A–D
- `figures/` — logos, benchmark plots, custom charts, GUI screenshots, plagiarism/paper images, TRL and SDG figures
- `scripts/` — `make_charts.py` (custom charts) and `take_screenshots.py` (GUI shots); run from
  `major-project-compiler-design/` with `PYTHONPATH=.` and the web app on :8080
- `data/` — JSON summaries of the benchmark numbers used in the tables
- `out/` — built PDFs (`report_team.pdf`, `report_<Name>.pdf`); `report.pdf` in the root is a copy of the team PDF
