# Major Project Research Paper

Research Paper: *Empirical Analysis of Optimization Phase Ordering Trade-offs in a Custom Compiler Using Micro-Benchmarks*

## Active Files
- **`Revised Paper (Final) - Copy.tex`** / **`Revised Paper (Final) - Copy.pdf`** — Updated A4 copy with:
  1. "Keywords" heading instead of "Index Terms"
  2. Copyright pubid aligned flush to the bottom-left of column 1
  3. Balanced two-column layout on the final references page (both columns end on the exact same line)
  4. Page size set to A4 (`a4paper`)
  5. Continuous email id for Dr. Suhas (`suhasabhyraatae.cs@sahyadri.edu.in`) with no break or space after `@`
- **`Revised Paper (Final).tex`** / **`Revised Paper (Final).pdf`** — Original letter-size final revision.
- **`fig/`** — High-resolution figures and benchmark plots referenced by the paper.
- **`build.ps1`** — PowerShell script to build the papers using `pdflatex`.

## Build
Run in PowerShell:
```powershell
.\build.ps1               # Builds the updated copy (Revised Paper (Final) - Copy.pdf)
.\build.ps1 -Target all   # Builds both original and copy
```

## Archive
- **`archived/`** — Contains older drafts, experiments, and intermediate revisions.
