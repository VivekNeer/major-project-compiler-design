# Major Project Research Paper

Research Paper: *Empirical Analysis of Optimization Phase Ordering Trade-offs in a Custom Compiler Using Micro-Benchmarks*

## Active Files
- **`Revised Paper (Final) - Copy 2.tex`** / **`Revised Paper (Final) - Copy 2.pdf`** — **Recommended A4 version**:
  1. All 6 author emails formatted in the **exact same font size (`9.8 pt`)** on a single line with balanced box widths (`0.29\textwidth` / `0.33\textwidth` / `0.29\textwidth`).
  2. "Keywords" heading instead of "Index Terms".
  3. Copyright pubid aligned flush to the bottom-left of column 1.
  4. Balanced two-column layout on the final references page (both columns end on the exact same line).
  5. Page size set to A4 (`a4paper`).
- **`Revised Paper (Final) - Copy.tex`** / **`Revised Paper (Final) - Copy.pdf`** — A4 copy using `{\small ...}` on Dr. Suhas's email.
- **`Revised Paper (Final).tex`** / **`Revised Paper (Final).pdf`** — Original letter-size final revision.
- **`fig/`** — High-resolution figures and benchmark plots referenced by the paper.
- **`build.ps1`** — PowerShell script to build the papers using `pdflatex`.

## Build
Run in PowerShell:
```powershell
.\build.ps1                 # Builds Copy 2 (Revised Paper (Final) - Copy 2.pdf)
.\build.ps1 -Target copy    # Builds Copy 1
.\build.ps1 -Target all     # Builds all versions
```

## Archive
- **`archived/`** — Contains older drafts, experiments, and intermediate revisions.
