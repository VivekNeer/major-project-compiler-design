/* General Matrix Multiply: C := alpha*A*B + beta*C.
 * Adapted from PolyBench/C's linear-algebra/blas/gemm kernel.
 * Matrices are fixed-size (4x4) and stored as flattened 1D arrays
 * (row-major: A[i][j] -> a[i * cols + j]) since the language has no
 * native 2D array type.
 * Exercises: triple-nested loops, repeated index arithmetic,
 * multiply-accumulate into an array element.
 * Optimization opportunities: common subexpression elimination on
 * the repeated `i * nk + j`-style index expressions, strength
 * reduction on the multiplications inside the index arithmetic.
 */
int main() {
    int ni = 4;
    int nj = 4;
    int nk = 4;
    int alpha = 2;
    int beta = 3;

    int a[16];
    int b[16];
    int c[16];

    int i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nk) {
            a[i * nk + j] = (i + j) % 5 + 1;
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < nk) {
        int j = 0;
        while (j < nj) {
            b[i * nj + j] = (i * 2 + j) % 5 + 1;
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nj) {
            c[i * nj + j] = (i + j) % 3;
            j = j + 1;
        }
        i = i + 1;
    }

    /* C := beta * C */
    i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nj) {
            c[i * nj + j] = c[i * nj + j] * beta;
            j = j + 1;
        }
        i = i + 1;
    }

    /* C := C + alpha * A * B */
    i = 0;
    while (i < ni) {
        int k = 0;
        while (k < nk) {
            int j = 0;
            while (j < nj) {
                c[i * nj + j] = c[i * nj + j] + alpha * a[i * nk + k] * b[k * nj + j];
                j = j + 1;
            }
            k = k + 1;
        }
        i = i + 1;
    }

    int sum = 0;
    i = 0;
    while (i < ni * nj) {
        print(c[i]);
        sum = sum + c[i];
        i = i + 1;
    }

    return sum;
}
