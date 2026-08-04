/* Scalar, Vector and Matrix Multiplication: y := alpha*A*x + beta*B*x.
 * Adapted from PolyBench/C's linear-algebra/blas/gesummv kernel.
 * Fixed-size (5x5) matrices stored as flattened 1D arrays.
 * Exercises: two matrix-vector products accumulated in the same
 * inner loop, followed by a scalar combine step per row.
 * Optimization opportunities: constant folding of alpha/beta into
 * the combine step, common subexpression elimination on the shared
 * `i * n + j` index used for both matrices.
 */
int main() {
    int n = 5;
    int alpha = 2;
    int beta = 3;

    int a[25];
    int b[25];
    int x[5];
    int tmp[5];
    int y[5];

    int i = 0;
    while (i < n) {
        int j = 0;
        while (j < n) {
            a[i * n + j] = (i + j) % 4 + 1;
            b[i * n + j] = (i * 2 + j) % 3 + 1;
            j = j + 1;
        }
        x[i] = i + 1;
        i = i + 1;
    }

    i = 0;
    while (i < n) {
        tmp[i] = 0;
        y[i] = 0;
        int j = 0;
        while (j < n) {
            tmp[i] = tmp[i] + a[i * n + j] * x[j];
            y[i] = y[i] + b[i * n + j] * x[j];
            j = j + 1;
        }
        y[i] = alpha * tmp[i] + beta * y[i];
        i = i + 1;
    }

    int sum = 0;
    i = 0;
    while (i < n) {
        print(y[i]);
        sum = sum + y[i];
        i = i + 1;
    }

    return sum;
}
