import { PASS_NAMES } from '../api'

const PASS_DESCR: Record<string, string> = {
  CF: 'Evaluates constant expressions at compile time and propagates known constant values; rewrites constant-condition branches.',
  CP: 'Substitutes copy chains (t1 = t0; use t1 → use t0), exposing further folding and dead-code opportunities.',
  CSE: 'Reuses previously computed expressions instead of recomputing them within a basic block.',
  DCE: 'Removes assignments whose results are never read and code made unreachable by unconditional jumps.',
  SR: 'Replaces expensive operations with cheaper equivalents (x*2 → x+x, x*1 → x, x%x → 0).',
  AS: 'Applies algebraic identities (x==x → 1, x&&0 → 0, !constant folding).',
}

const COSTS: [string, string][] = [
  ['ADD / SUB / comparisons / logic / COPY', '1 cycle'],
  ['MUL', '3 cycles'],
  ['DIV / MOD', '12 cycles'],
  ['JUMP / conditional jumps', '2 cycles'],
  ['ARR_LOAD / ARR_STORE / GLOBAL_LOAD / GLOBAL_STORE', '2 cycles'],
  ['CALL', '5 cycles'],
  ['RETURN', '3 cycles'],
  ['PRINT (I/O)', '10 cycles'],
  ['LABEL / NOP / declarations / function markers', 'free'],
]

export default function Reference() {
  return (
    <div className="ref-section" style={{ maxWidth: 820 }}>
      <h1 className="page-title">Reference</h1>
      <p className="page-sub">
        Language, optimization passes, and the cost model behind the metrics.
      </p>

      <h3>The phase-ordering problem</h3>
      <p>
        Optimization passes interact: constant folding can create dead code,
        copy propagation can expose common subexpressions, and dead-code
        elimination can only remove what earlier passes made removable. The
        <em> order </em> in which passes run therefore changes the result.
        With 6 passes there are 6! = 720 full orderings; this tool runs all of
        them (plus the unoptimized baseline) and measures each one — the
        exhaustive approach of Kulkarni et&nbsp;al. (CGO 2006).
      </p>

      <h3>Optimization passes</h3>
      <table className="data">
        <thead>
          <tr>
            <th>Abbr</th>
            <th>Pass</th>
            <th>What it does</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(PASS_NAMES).map(([abbr, name]) => (
            <tr key={abbr}>
              <td>{abbr}</td>
              <td>{name}</td>
              <td style={{ fontFamily: 'var(--sans)', color: 'var(--text-2)' }}>
                {PASS_DESCR[abbr]}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Cost model (ARM Cortex-M class)</h3>
      <table className="data">
        <thead>
          <tr>
            <th>IR operation</th>
            <th>Weight</th>
          </tr>
        </thead>
        <tbody>
          {COSTS.map(([op, cost]) => (
            <tr key={op}>
              <td>{op}</td>
              <td>{cost}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Language: supported C subset</h3>
      <pre>{`int g = 5;                      // globals (constant initializers)

int classify(int x) {
    if (x > 100)      { return 3; }
    else if (x > 10)  { return 2; }      // else-if chains
    else              { return 0; }
}

int main() {
    int a[10];                            // fixed-size arrays
    int sum = 0;
    for (int i = 0; i < 10; i = i + 1) {  // for loops
        a[i] = i * i;
        sum = sum + a[i];
    }
    // && and || short-circuit like real C:
    if (sum > 0 && classify(sum) > 1) { g = g + 1; }
    print(sum);                           // built-in output
    return 0;
}`}</pre>
      <p>
        Everything is a 32-bit <code>int</code>. Division and modulo by zero
        yield 0 (in the interpreter <em>and</em> in generated RISC-V, via an
        explicit guard). Semantic analysis reports all errors at once:
        undeclared variables, undefined functions, wrong argument counts,
        duplicate declarations, and array/scalar misuse.
      </p>

      <h3>Pipeline</h3>
      <p>
        <code>source → lexer → parser → semantic analyzer → IR generator →
        (optimization passes)* → IR interpreter / RISC-V RV32IM backend</code>
      </p>
      <p>
        Dynamic instruction counts come from executing the three-address IR
        directly; every optimized ordering is validated against the
        unoptimized program's output before its metrics are trusted.
      </p>
    </div>
  )
}
