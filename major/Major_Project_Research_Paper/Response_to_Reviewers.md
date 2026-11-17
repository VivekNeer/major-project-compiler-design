# Author Response to Reviewers

**Paper ID:** 1021  
**Paper Title:** Empirical Analysis of Optimization Phase Ordering Trade-offs in a Custom Compiler Using Micro-Benchmarks  
**Track:** Computing (COSMIC 2026)  
**Authors:** Aniket De, Kushal S M, Manas S, Vivek Neeralagi, Suhas A Bhyratae, Harisha  

---

## Executive Summary & Overview of Revisions

We sincerely thank the Track Chair, Associate Editors, and Reviewers for their thoughtful, rigorous, and constructive feedback on our submission. We are greatly encouraged by the positive reception—including evaluations of **Accept**, **Accept**, and **Weak Accept**—and by the reviewers' recognition of our clean modular compiler architecture, the utility of our independently reorderable pass framework, and our clear visualization of pass-ordering dynamics.

The reviewers highlighted crucial areas where the initial draft needed expansion, specifically:
1. **Generalizability beyond a single benchmark:** Evaluating across the full promised suite of MiBench and PolyBench kernels rather than focusing primarily on `factorial`.
2. **Explicit specification of the execution cost model:** Formally defining the per-instruction cycle weights and introducing model-free validation.
3. **Rigorous statistical substantiation:** Formally reporting statistical tests, test statistics, $p$-values, and effect sizes.
4. **Clarification of pairwise interaction matrices and units:** Explaining the derivation, sample space, and interpretation of Table IV.
5. **Baseline transparency:** Providing complete source code and intermediate representation (IR) line-by-line accounting for the baseline measurements.
6. **Clarification of the speed–size trade-off and novelty scope:** Explaining the Pareto characteristics of code-shrinking passes and explicitly delimiting our contribution.

In response, we undertook an exhaustive overhaul of the experimental evaluation and manuscript. Below is a summary of the major additions in the final paper:

* **From 1 Benchmark to 15 Benchmarks (10,815 Executions):** We expanded our evaluation from `factorial` to **fifteen benchmark programs** (8 scalar kernels adapted from MiBench and 7 array/matrix kernels adapted from PolyBench/C). We evaluated **all $6! = 720$ phase orderings** across all 15 programs, generating **10,800 optimized configurations** (plus 15 baselines). Every single optimized binary was dynamically executed and verified against baseline output by an automated test harness to guarantee semantic equivalence.
* **Formal Instruction Cost Model & Model-Free Dynamic Validation:** We added Section III-C and Table II, explicitly detailing the per-opcode cycle latency for all 21 3AC instructions based on an in-order ARM Cortex-M architecture. Furthermore, we integrated an IR execution interpreter to measure **Dynamic Instruction Count** on fixed inputs as an independent, model-free runtime metric ($\rho = 0.88$ correlation with cycle estimates).
* **Complete Statistical Validation:** We added Section IV-D reporting non-parametric hypothesis tests across the 15 program blocks: Friedman tests for code size ($\chi^2(23) = 304.6, p = 5.3 \times 10^{-51}, W = 0.88$), estimated cycles ($p = 3.0 \times 10^{-49}, W = 0.86$), and dynamic instructions ($p = 8.5 \times 10^{-51}, W = 0.88$), followed by an exact Wilcoxon signed-rank post-hoc test ($p = 3.1 \times 10^{-5}, r = 1.00$).
* **Formalization of Pairwise Interaction Matrix:** Section IV-B and Table IV define the exact derivation across all 720 orderings, specifying units (mean IR instructions saved/lost) and explaining marginal vs. unconfounded effects.
* **Baseline Line-by-Line Breakdown:** Section IV-A and Listing 1 provide the complete source code, unoptimized IR breakdown (40 instructions, 81 cycles), and optimized IR (16 instructions, 55 cycles) for `factorial`.
* **Single-Command Full Reproducibility:** The entire compiler, benchmark suite, and figure-generation scripts are open-sourced at [GitHub](https://github.com/VivekNeer/major-project-compiler-design). All 10,815 compilations and tests can be reproduced with a single command (`python -m compiler.main --benchmark-all`) in ~23 seconds.

Below is our point-by-point response detailing how every reviewer comment was addressed.

---

## Detailed Response to Reviewer #1

### Reviewer #1 — Comment 1: Single Benchmark
> **Reviewer Comment:**  
> *"Single benchmark. All reported results (Tables II–V, Figs. 2–5) come from one program (factorial), despite the stated objective of validating against MiBench and PolyBench benchmarks. This significantly limits the generalizability of the conclusions."*

**Author Response:**  
We completely agree with the reviewer. In the revised manuscript, we have addressed this comprehensively by expanding our empirical evaluation to **fifteen benchmark programs** (Table V and Section IV-C):
* **8 MiBench-derived scalar kernels:** `factorial`, `isqrt`, `bitcount`, `fibonacci`, `collatz`, `sha_mix`, `power`, and `gcd`.
* **7 PolyBench/C-derived array and stencil kernels:** `jacobi1d`, `jacobi2d`, `gemm`, `2mm`, `gesummv`, `atax`, and `bicg`.

Rather than testing a subset of sequences, we executed **all $6! = 720$ permutations across all 15 benchmarks**, totaling **10,800 optimized configurations** (10,815 total runs with baselines). 

Key findings across the 15 benchmarks:
1. **Per-Program Reductions (Table V):** The best ordering achieves a geometric-mean reduction of **35.7% in static code size** (ranging from 22.3% on `bicg` to 60.0% on `factorial`), **20.5% in estimated cycles** (11.9% to 33.9%), and **23.2% in dynamic instruction count** (12.9% to 34.6%).
2. **Distribution across Orderings (Figure 3):** Box plots illustrate the spread across all 720 orderings for each of the 15 kernels. On 13 of the 15 programs, the worst orderings produce 0% reduction, confirming that poor phase ordering completely nullifies optimization opportunities.
3. **Universality of Equivalence Classes (Table VI):** Across all 15 programs, the 720 orderings collapse into exactly **nine equivalence classes** determined by the relative order of the four size-relevant passes ($\text{CF}, \text{CSE}, \text{CP}, \text{DCE}$). The optimal relative order ($\text{CF} \to \text{CSE} \to \text{CP} \to \text{DCE}$) is identical across all 15 benchmarks.

`factorial` is now retained strictly as an introductory worked example in Section IV-A to allow readers to verify the line-by-line mechanics before presenting the cross-benchmark results in Sections IV-C, IV-D, and IV-E.

---

### Reviewer #1 — Comment 2: Undefined Cost Model
> **Reviewer Comment:**  
> *"'Estimated execution cycles' is a primary metric but the weighted instruction-cost model behind it is never specified (what does each instruction type cost?), making the cycle results unverifiable."*

**Author Response:**  
We thank the reviewer for highlighting this omission. In the revised paper, we added **Section III-C ("Metrics and Cost Model")** and **Table II ("Per-instruction cost model for the estimated-cycle metric")**, which fully specifies the per-opcode cycle latency model:

| IR Opcodes | Cycle Cost | Architecture Rationale |
|:---|:---:|:---|
| `ADD`, `SUB`, `NEG`, comparisons, `AND`, `OR`, `NOT`, `COPY`, `LOAD_CONST`, `PARAM` | 1 | Single-cycle ALU / register operations |
| `MUL` | 3 | Multi-cycle hardware multiplier latency |
| `DIV`, `MOD` | 12 | Iterative hardware divider latency |
| `JUMP`, `JUMP_IF_TRUE`, `JUMP_IF_FALSE` | 2 | Branch instruction + pipeline penalty |
| `ARR_LOAD`, `ARR_STORE`, `GLOBAL_LOAD`, `GLOBAL_STORE` | 2 | Memory load/store latency |
| `CALL` / `RETURN` / `PRINT` | 5 / 3 / 10 | Call overhead, stack frame adjust, host output |
| `LABEL`, `NOP`, `FUNC_BEGIN`, `FUNC_END`, `FUNC_PARAM`, `ARR_DECL`, `GLOBAL_DECL` | 0 | Non-executable metadata / markers |

**Model Rationale & Model-Free Validation:**
1. **Target Architecture:** The weights reflect the typical in-order execution latencies of an ARM Cortex-M embedded core, directly aligned with embedded workloads represented by MiBench.
2. **Model-Free Validation:** To ensure our conclusions do not depend on synthetic latency weights, we introduced **Dynamic Instruction Count**—the exact count of 3AC instructions executed at runtime by our interpreter on fixed inputs. As shown in Section IV-E and Table VI, the static cycle metric and the dynamic instruction count are strongly correlated ($\rho = 0.88$), confirming that the cycle model reliably tracks execution cost without distorting ordering ranks.

---

### Reviewer #1 — Comment 3: Unsubstantiated Statistical Claims
> **Reviewer Comment:**  
> *"Unsubstantiated statistical claims. Section IV.D states that statistical tests assessed significance, but no test, p-value, or effect size is reported anywhere in the results section."*

**Author Response:**  
We apologize for the omission of statistical reporting in the initial submission. In the revised paper, we added **Section IV-D ("Statistical Significance")**, presenting a complete non-parametric statistical evaluation treating the fifteen benchmark programs as independent blocks/replications:

1. **Friedman Test (Repeated-Measures Non-Parametric ANOVA):**  
   We tested whether phase ordering significantly influences compiler performance across the 15 benchmark programs, evaluating the 24 relative orderings of the four size-relevant passes ($\text{CF}, \text{CSE}, \text{CP}, \text{DCE}$):
   * **Static Code Size:** $\chi^2(23) = 304.6,\; p = 5.3 \times 10^{-51},\; \text{Kendall's } W = 0.88$
   * **Estimated Cycles:** $\chi^2(23) = 296.0,\; p = 3.0 \times 10^{-49},\; \text{Kendall's } W = 0.86$
   * **Dynamic Instruction Count:** $\chi^2(23) = 303.6,\; p = 8.5 \times 10^{-51},\; \text{Kendall's } W = 0.88$  
   *Interpretation:* The null hypothesis of equal performance across orderings is rejected at $p < 10^{-48}$. Kendall’s $W \in [0.86, 0.88]$ indicates exceptionally strong concordance across all fifteen programs, formally proving that the ordering hierarchy is consistent across diverse programs.

2. **Post-Hoc Pairwise Comparison (Wilcoxon Signed-Rank Test):**  
   An exact Wilcoxon signed-rank test comparing Class 1 (optimal) against Class 9 (worst) across the 15 paired programs yielded:
   $$W = 0,\quad p = 3.1 \times 10^{-5} \text{ (one-sided exact)},\quad \text{rank-biserial } r = 1.00$$
   Class 1 achieved superior reduction over Class 9 on every single program ($15/15$), yielding the minimum possible $p$-value for $n = 15$ with maximal effect size ($r = 1.00$) and a median paired improvement of 34% of baseline code size.

3. **Spearman Rank Correlation ($\rho$):**  
   Reported across all 10,800 optimized configurations: $\rho = 0.79$ between code size and estimated cycles; $\rho = 0.88$ between code size and dynamic instruction count (median within-program $\rho = 1.00$).

---

### Reviewer #1 — Comment 4: Table IV Underspecified
> **Reviewer Comment:**  
> *"Table IV is underspecified. The pairwise pass-interaction values are not explained in terms of derivation or units; with only 6 evaluated sequences it is unclear how a full 6×6 interaction matrix was populated."*

**Author Response:**  
We thank the reviewer for identifying this ambiguity. In the revised paper, we clarified this in **Section IV-B ("Pairwise Pass Interactions")** and the caption of **Table IV**:

1. **Derivation & Sample Size:**  
   The pairwise matrix is **not** computed from the 6 illustrative sequences; it is computed across **all 720 full permutations** on `factorial`.
2. **Mathematical Definition & Units:**  
   For each ordered pair of passes $(A, B)$, the entry $M_{AB}$ is defined as:
   $$M_{AB} = \overline{\text{Size}}_{A \prec B} - \overline{\text{Size}}_{B \prec A}$$
   where $\overline{\text{Size}}_{A \prec B}$ is the mean static code size (in **IR instructions**) across the 360 orderings in which pass $A$ precedes pass $B$, and $\overline{\text{Size}}_{B \prec A}$ is the mean over the 360 orderings in which $B$ precedes $A$.
3. **Interpretation:**  
   * Negative values mean placing pass $A$ before pass $B$ produces fewer instructions (e.g., $M_{\text{CF}, \text{DCE}} = -10.7$, indicating that running Constant Folding before Dead Code Elimination saves $10.7$ instructions on average).
   * The matrix is anti-symmetric ($M_{AB} = -M_{BA}$) with diagonal elements equal to 0 by construction.
4. **Marginality Caveat:**  
   We explicitly discuss in Section IV-B that this pairwise matrix is a marginal statistic averaging over the positions of the other four passes. We explain why passes like Algebraic Simplification (AS) and Strength Reduction (SR) show small non-zero values ($+2.9$): in the permutation space, having AS before CF correlates with DCE appearing later in the pipeline. We guide the reader to the unconfounded Equivalence Class analysis (Section IV-C / Table VI) for exact causal attribution.

---

### Reviewer #1 — Comment 5: Baseline Plausibility
> **Reviewer Comment:**  
> *"Baseline plausibility. A baseline instruction count of 40 for an unoptimized factorial routine is not shown in source or IR form, making it hard for readers to verify the reported 60%/32% reduction figures."*

**Author Response:**  
We have made the entire derivation transparent in **Section IV-A** and **Listing 1**:

1. **Source Code Included (Listing 1):**  
   The full source code of the `factorial` program (containing both `factorial(n)` and `main()`) is shown in Listing 1. It explicitly contains constant folding opportunities (`base = 2 + 3`, `extra = 10 - 5`), dead code assignments (`unused = 42 * 2`, `also_unused = unused + 100`), and repeated subexpressions (`sum1 = base + extra`, `sum2 = base + extra`).
2. **Instruction Breakdown of the 40 Baseline Instructions:**  
   Because the unoptimized 3AC lowering places every constant and intermediate into a dedicated temporary (e.g., `t6 = 2; t7 = 3; t8 = t6 + t7; base = t8`), the 40 countable instructions consist of:
   * 11 constant loads (`LOAD_CONST`)
   * 11 variable copies (`COPY`)
   * 5 additions (`ADD`), 2 multiplications (`MUL`), 1 subtraction (`SUB`), 1 comparison (`LTE`)
   * 2 jumps (`JUMP`, `JUMP_IF_FALSE`)
   * 1 parameter setup (`PARAM`), 1 function call (`CALL`), 2 returns (`RETURN`), 3 prints (`PRINT`)  
   *(13 instructions in `factorial()`, 27 instructions in `main()`)*.
3. **Cycle Accounting:**  
   Applying Table II:
   $$\text{Cycles} = (30 \times 1) + (2 \times 3) + (2 \times 2) + 5 + (2 \times 3) + (3 \times 10) = 30 + 6 + 4 + 5 + 6 + 30 = 81 \text{ cycles}.$$
4. **Optimized Code:**  
   The optimal sequence reduces the loop in `factorial` to 10 instructions and `main()` to 6 instructions (`param 5; t12 = call factorial; print t12; print 10; print 10; return 0`), yielding **16 instructions** and **55 cycles**.
   * Size reduction: $(40 - 16) / 40 = 60.0\%$.
   * Cycle reduction: $(81 - 55) / 81 = 32.1\%$.

---

### Reviewer #1 — Comment 6: Minor Inconsistencies
> **Reviewer Comment:**  
> *"Minor: inconsistent table/sequence labeling (Table II sequences aren't explicitly numbered 'Seq 1–6' as referenced later in Tables III/V); normalization method for Table V is not stated explicitly."*

**Author Response:**  
Both minor issues have been resolved:
* In **Table III**, all evaluated sequence rows are explicitly and consistently labeled `Base`, `Seq 1`, `Seq 2`, `Seq 3`, `Seq 4`, `Seq 5`, and `Seq 6`.
* In **Section III-C**, the normalization formula is explicitly stated:
  * Percentage reduction: $100 \times (1 - m_{\mathrm{opt}} / m_{\mathrm{base}})$.
  * Normalized ratio: $m_{\mathrm{opt}} / m_{\mathrm{base}}$ (where 1.0 represents baseline; smaller is better).
  * Cross-program averages (Table VI) explicitly use the **geometric mean** of normalized ratios, following Fleming & Wallace (1986).

---

## Detailed Response to Reviewer #2

### Reviewer #2 — Comment 1: Evaluation Scope, Cost Model, and Statistical Tests
> **Reviewer Comment:**  
> *"The evaluation relies mainly on one factorial benchmark, unvalidated cycle estimates, and statistical tests whose design and results are not reported, limiting support for general claims about phase ordering."*

**Author Response:**  
We thank the reviewer for these critical observations. We have resolved all three concerns in depth:
1. **15 Diverse Benchmarks & 10,815 Runs:** Evaluated 8 scalar kernels from MiBench and 7 array/stencil kernels from PolyBench/C across all 720 orderings (Table V, Fig. 3, Table VI).
2. **Explicit Cost Model & Model-Free Dynamic Validation:** Defined the full ARM Cortex-M latency model (Table II) and validated it against dynamic instruction counts executed by an IR interpreter ($\rho = 0.88$). In addition, in Section IV-F, we lowered baseline and optimized IR to physical RV32IM RISC-V assembly, confirming that the optimizations translate to hardware code generation with a 26.0% geometric-mean reduction in assembly instructions.
3. **Rigorous Non-Parametric Statistics:** Formally reported the Friedman test ($\chi^2 = 304.6, p < 10^{-48}, W = 0.88$) and Wilcoxon signed-rank test ($p = 3.1 \times 10^{-5}, r = 1.00$) in Section IV-D.

---

### Reviewer #2 — Comment 2: Speed–Size Trade-Off, Pass Descriptions, and Contribution
> **Reviewer Comment:**  
> *"The paper should clarify the claimed speed–size trade-off, describe the added passes and evaluation in reproducible detail, and distinguish its contribution from established compiler techniques."*

**Author Response:**  
We have addressed each of these three points:

1. **Clarification of Speed–Size Trade-Off (Section IV-E):**  
   We clarified why the Pareto front between code size and execution performance is narrow in this study. The six passes evaluated here (CF, DCE, CSE, CP, SR, AS) are **strictly code-shrinking transformations**. Unlike code-expanding optimizations (such as loop unrolling, function inlining, or loop tiling) that trade larger binary footprint for fewer runtime branches or higher ILP, code-shrinking passes reduce execution cycles proportionally by eliminating redundant operations. Consequently, Class 1 simultaneously minimizes code size (0.643), estimated cycles (0.795), and dynamic instructions (0.768) on all 15 programs ($\rho = 0.79 \text{ to } 0.88$). We explicitly contrast this with multi-objective frameworks like POSET-RL on LLVM, noting that the absence of a size-vs-speed conflict is an intrinsic property of this pass set.

2. **Detailed Pass Descriptions & Reproducibility (Section III-B & Section IV):**  
   * Section III-B details the preconditions, liveness analysis, available-expression computation, and rewriting rules for each pass.
   * All passes are implemented as block-local, side-effect-free transformations that preserve semantic correctness under any ordering.
   * The complete pure-Python compiler, test suite (161 unit tests), and benchmarking pipeline are open-sourced at [GitHub](https://github.com/VivekNeer/major-project-compiler-design). The entire experiment (10,815 compile-and-execute cycles) can be regenerated with a single command (`python -m compiler.main --benchmark-all`) in ~23 seconds.

3. **Distinguishing Our Contribution:**  
   We explicitly state in Section I and Section VI that our contribution is **not** the invention of new transformation passes (which are textbook techniques), but rather:
   * **Orthogonal Compiler Architecture:** Designing an infrastructure where passes are strictly isolated and side-effect free, allowing all $6! = 720$ orderings to run without compiler crashes or semantic divergence.
   * **Exhaustive Empirical Structure:** Discovering that the 720 orderings collapse into exactly 9 equivalence classes governed by 4 fundamental ordering rules.
   * **Universality Proof:** Proving empirically and statistically that the relative ordering $\text{CF} \to \text{CSE} \to \text{CP} \to \text{DCE}$ is universally optimal across both scalar and polyhedral benchmark suites.

---

## Detailed Response to Reviewer #4

> **Reviewer Comment:**  
> *"The paper demonstrates a clean and modular compiler architecture, as illustrated in Fig. 1, where each optimization pass is implemented as an independently reorderable component, providing a useful framework for controlled experimentation and analysis of pass interactions. The use of Three-Address Code (3AC) as the intermediate representation is appropriate for supporting classical data-flow optimizations such as liveness analysis for Dead Code Elimination and available-expression analysis for Common Subexpression Elimination. The study also makes effective use of visualizations, including scatter plots, heatmaps, and normalized bar charts, to clearly communicate the trade-offs between code size and estimated execution cycles across different optimization sequences."*  
> *(Overall Decision: Accept)*

**Author Response:**  
We warmly thank Reviewer #4 for the positive evaluation and for recommending **Accept**. We appreciate the reviewer's recognition of our modular architecture, the suitability of 3AC IR for classical data-flow analyses, and our visual presentation.

*(Note: In the review submission system, the text under "Weaknesses" was an exact duplicate of "Strengths".)* We have preserved all the architectural clarity and visual representations praised by the reviewer, while expanding the visualizations to include:
* Figure 2: The $6 \times 6$ pairwise pass-interaction heatmap.
* Figure 3: Full-width box plot distributions across all 720 orderings for all 15 benchmark programs.

---

## Summary Mapping of Review Comments to Manuscript Locations

| Reviewer & Issue | Description of Issue | Resolution in Revised Paper | Location in Final Paper |
|:---|:---|:---|:---|
| **R1.1, R2.1** | Single benchmark limitation (`factorial`) | Expanded to 15 benchmarks (MiBench + PolyBench/C), 720 orderings, 10,800 runs | Section IV-C, Table V, Fig. 3 |
| **R1.2, R2.1** | Undefined cycle cost model | Added complete opcode cost table (Table II) and dynamic instruction count | Section III-C, Table II, Section IV-E |
| **R1.3, R2.1** | Unsubstantiated statistical claims | Friedman test ($\chi^2 = 304.6, p < 10^{-48}$), Wilcoxon test ($p = 3.1 \times 10^{-5}$), Kendall's $W$ | Section IV-D |
| **R1.4** | Table IV interaction matrix underspecified | Formal mathematical definition, units (IR instructions), and marginality caveats | Section IV-B, Table IV, Fig. 2 |
| **R1.5** | Baseline 40-instruction plausibility | Full source code listing (Listing 1), line-by-line IR opcode and cycle breakdown | Section IV-A, Listing 1 |
| **R1.6** | Sequence labeling & normalization | Standardized labels (`Base`, `Seq 1–6`), geometric-mean normalization stated | Section III-C, Table III, Table VI |
| **R2.2** | Speed–size trade-off clarification | Explained absence of Pareto conflict for code-shrinking passes | Section IV-E |
| **R2.2** | Pass details & reproducibility | Formal pass specifications and 1-command reproducible open-source release | Section III-B, Section IV, Section VI |
| **R2.2** | Distinction of contribution | Clarified focus on exhaustive measurement, equivalence classes, and architecture | Section I, Section VI |
| **R4** | Positive evaluation of architecture & IR | Preserved strengths; expanded cross-program plots and equivalence class tables | Section III-A, Section IV-C, Figs. 1–3 |

---
*We believe these substantial expansions comprehensively address all comments raised by the reviewers and make the paper significantly stronger, more rigorous, and fully reproducible.*
