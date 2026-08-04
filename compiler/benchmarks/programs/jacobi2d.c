/* 2D Jacobi Stencil Iteration.
 * Adapted from PolyBench/C's stencils/jacobi-2d kernel.
 * Repeatedly averages each interior grid cell with its four
 * neighbours across several time steps, alternating between two
 * buffers. The grid is fixed-size (5x5), flattened into a 1D array
 * (row-major: A[i][j] -> a[i * n + j]).
 * Exercises: 2D-style index arithmetic on a flattened array, a
 * five-point stencil read pattern, double buffering across time
 * steps (as in jacobi1d, but with a second spatial dimension).
 * Optimization opportunities: common subexpression elimination on
 * the repeated `i * n + j` base offset, strength reduction on the
 * division by a constant.
 */
int main() {
    int n = 5;
    int steps = 3;

    int a[25];
    int b[25];

    int i = 0;
    while (i < n) {
        int j = 0;
        while (j < n) {
            a[i * n + j] = (i * 3 + j * 2) % 6 + 1;
            j = j + 1;
        }
        i = i + 1;
    }

    int t = 0;
    while (t < steps) {
        i = 1;
        while (i < n - 1) {
            int j = 1;
            while (j < n - 1) {
                b[i * n + j] = (a[(i - 1) * n + j] + a[(i + 1) * n + j]
                    + a[i * n + j - 1] + a[i * n + j + 1] + a[i * n + j]) / 5;
                j = j + 1;
            }
            i = i + 1;
        }

        i = 1;
        while (i < n - 1) {
            int j = 1;
            while (j < n - 1) {
                a[i * n + j] = b[i * n + j];
                j = j + 1;
            }
            i = i + 1;
        }

        t = t + 1;
    }

    int sum = 0;
    i = 0;
    while (i < n * n) {
        print(a[i]);
        sum = sum + a[i];
        i = i + 1;
    }

    return a[(n / 2) * n + n / 2];
}
