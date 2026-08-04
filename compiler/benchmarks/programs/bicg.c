/* BiCG Sub-Kernel: s := r^T * A, q := A * p.
 * Adapted from PolyBench/C's linear-algebra/kernels/bicg kernel.
 * Fixed-size (5x5) matrix stored as a flattened 1D array. Computes
 * two independent reductions over the same matrix in a single pass.
 * Exercises: two accumulator arrays updated inside one shared
 * nested loop, reuse of the same loaded matrix element for both.
 * Optimization opportunities: common subexpression elimination on
 * the shared `a[i * n + j]` load feeding both accumulations.
 */
int main() {
    int n = 5;

    int a[25];
    int r[5];
    int p[5];
    int s[5];
    int q[5];

    int i = 0;
    while (i < n) {
        int j = 0;
        while (j < n) {
            a[i * n + j] = (i * 2 + j) % 4 + 1;
            j = j + 1;
        }
        r[i] = i + 1;
        p[i] = n - i;
        s[i] = 0;
        i = i + 1;
    }

    i = 0;
    while (i < n) {
        q[i] = 0;
        int j = 0;
        while (j < n) {
            s[j] = s[j] + r[i] * a[i * n + j];
            q[i] = q[i] + a[i * n + j] * p[j];
            j = j + 1;
        }
        i = i + 1;
    }

    int sum = 0;
    i = 0;
    while (i < n) {
        print(s[i]);
        print(q[i]);
        sum = sum + s[i] + q[i];
        i = i + 1;
    }

    return sum;
}
