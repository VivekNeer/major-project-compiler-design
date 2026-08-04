/* 1D Jacobi Stencil Iteration.
 * Adapted from PolyBench/C's stencils/jacobi-1d kernel.
 * Repeatedly averages each interior element with its two neighbours
 * across several time steps, alternating between two buffers.
 * Exercises: fixed-size arrays, array load/store, nested loops,
 * index arithmetic (i-1, i+1), integer averaging via division.
 * Optimization opportunities: common subexpression elimination on
 * repeated index expressions, strength reduction on the division by
 * a constant, dead code elimination of unused temporaries.
 */
int main() {
    int n = 8;
    int steps = 4;

    int a[8];
    int b[8];

    int i = 0;
    while (i < n) {
        a[i] = (i * i) % 7 + 1;
        i = i + 1;
    }

    int t = 0;
    while (t < steps) {
        i = 1;
        while (i < n - 1) {
            b[i] = (a[i - 1] + a[i] + a[i + 1]) / 3;
            i = i + 1;
        }

        i = 1;
        while (i < n - 1) {
            a[i] = b[i];
            i = i + 1;
        }

        t = t + 1;
    }

    i = 0;
    while (i < n) {
        print(a[i]);
        i = i + 1;
    }

    return a[n / 2];
}
