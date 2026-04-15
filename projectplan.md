 **"Benchmarking Phase Ordering Trade-offs in a Custom Compiler Infrastructure using MiBench"**

### **Phase 1: Front-End Infrastructure (Language, Lexer, & Parser)**

In this phase, we build the "ears" and "eyes" of our compiler. we define our language rules and create a system to read and understand them.

* **What to Make:**
* **Language Specification:** Define a small subset of C (e.g., integers, basic arithmetic, `if` statements, and `while` loops).
* **Lexical Analyzer (Lexer):** A program that converts raw text into a stream of "tokens" like `TOKEN_WHILE`, `TOKEN_INT`, or `TOKEN_PLUS`.
* **Syntax Analyzer (Parser):** A **Recursive Descent Parser** is recommended for its simplicity. It checks if the tokens follow our language's grammar and builds an **Abstract Syntax Tree (AST)**.


* **Guide Materials & Links:**
* **[Writing a C Compiler (Part 1)](https://norasandler.com/2017/11/29/Write-a-Compiler.html)**: A step-by-step guide to building a tiny C subset compiler.
* **[LLVM Kaleidoscope Tutorial](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/index.html)**: Explains lexing and parsing concepts clearly (Chapter 1 & 2).
* **[Recursive Descent Parsing Guide](https://iitd.github.io/col728/lec/parsing.html)**: A detailed algorithm for building a parser by hand.



---

### **Phase 2: Intermediate Representation (IR) Generation**

The IR is a simplified, neutral version of the code that is easier to optimize than the raw source.

* **What to Make:**
* **Three-Address Code (3AC) Generator:** Translate our AST into a series of simple instructions like `t1 = a + b`.
* **Symbol Table:** A data structure that keeps track of variable names, types, and scopes.


* **Guide Materials & Links:**
* **[Three-Address Code (3AC) Tutorial](https://www.naukri.com/code360/library/three-address-code)**: Learn how to break complex expressions into simple IR instructions.
* **[Stanford CS143 IR Slides](https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/13/Slides13.pdf)**: Visual examples of translating control flow (if/while) into IR jumps.



---

### **Phase 3: Reorderable Optimization Passes**

This is the core "research" part of our project where we build the cleanup scripts.

* **What to Make:**
* **Constant Folding:** Evaluate math like `2 + 2` at compile time.
* **Dead Code Elimination (DCE):** Remove variables or branches that never affect the output.
* **Common Subexpression Elimination (CSE):** Find and reuse repeated calculations.
* **The "Pass Manager":** A simple script that lets we run these optimizations in different orders (e.g., DCE then CF vs. CF then DCE).


* **Guide Materials & Links:**
* **[Compiler Optimization Techniques Overview](https://opencs.aalto.fi/en/courses/modern-and-emerging-programming-languages/part-7/3-compiler-optimization-techniques)**: Explains CF, DCE, and CSE with simple examples.
* **[Sarah Chasins' Optimization Notes](https://schasins.com/berkeley-cs164-fall-2022/notes/20-Optimization.html)**: A hands-on look at implementing constant folding recursively.



---

### **Phase 4: Benchmarking & Trade-off Analysis**

In the final phase, we run the experiments and collect the data for our paper.

* **What to Make:**
* **Test Bench:** Manually translate 3-5 small logic blocks from **MiBench** into our custom language.
* **Metric Collector:** A script to count the number of instructions in our final IR (Code Size) and estimate the execution time (Performance).
* **Trade-off Visualization:** Create graphs (like Scatter Plots) showing how different "Phase Orders" affect Speed vs. Size.


* **Guide Materials & Links:**
* **[MiBench Official Site](https://www.google.com/search?q=http://vhosts.eecs.umich.edu/mibench/)**: Download the benchmark source code to find simple C files to adapt.
* **[IEEE POSET-RL Study](https://www.google.com/search?q=https://ieeexplore.org/document/9804673/)**: A research paper that benchmarks phase ordering for both size and speed—perfect for our literature review.

