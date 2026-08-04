/* Chained 2-Matrix-Multiply: D := alpha*A*B*C + beta*D.
 * Adapted from PolyBench/C's linear-algebra/kernels/2mm kernel.
 * Computes tmp := alpha*A*B, then D := tmp*C + beta*D. All matrices
 * are fixed-size (4x4) flattened 1D arrays (row-major).
 * Exercises: five distinct arrays live at once, back-to-back
 * triple-nested loops feeding one result into the next stage.
 * Optimization opportunities: common subexpression elimination
 * across the two matmul stages, dead code elimination of any
 * initialization overwritten before use.
 */
int main() {
    int ni = 4;
    int nj = 4;
    int nk = 4;
    int nl = 4;
    int alpha = 2;
    int beta = 3;

    int a[16];
    int b[16];
    int c[16];
    int d[16];
    int tmp[16];

    int i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nk) {
            a[i * nk + j] = (i + j) % 4 + 1;
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < nk) {
        int j = 0;
        while (j < nj) {
            b[i * nj + j] = (i * 2 + j) % 4 + 1;
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < nj) {
        int j = 0;
        while (j < nl) {
            c[i * nl + j] = (i + j * 2) % 4 + 1;
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nl) {
            d[i * nl + j] = (i + j) % 3;
            j = j + 1;
        }
        i = i + 1;
    }

    /* tmp := alpha * A * B */
    i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nj) {
            tmp[i * nj + j] = 0;
            j = j + 1;
        }
        i = i + 1;
    }
    i = 0;
    while (i < ni) {
        int k = 0;
        while (k < nk) {
            int j = 0;
            while (j < nj) {
                tmp[i * nj + j] = tmp[i * nj + j] + alpha * a[i * nk + k] * b[k * nj + j];
                j = j + 1;
            }
            k = k + 1;
        }
        i = i + 1;
    }

    /* D := tmp * C + beta * D */
    i = 0;
    while (i < ni) {
        int j = 0;
        while (j < nl) {
            d[i * nl + j] = d[i * nl + j] * beta;
            j = j + 1;
        }
        i = i + 1;
    }
    i = 0;
    while (i < ni) {
        int k = 0;
        while (k < nj) {
            int j = 0;
            while (j < nl) {
                d[i * nl + j] = d[i * nl + j] + tmp[i * nj + k] * c[k * nl + j];
                j = j + 1;
            }
            k = k + 1;
        }
        i = i + 1;
    }

    int sum = 0;
    i = 0;
    while (i < ni * nl) {
        print(d[i]);
        sum = sum + d[i];
        i = i + 1;
    }

    return sum;
}
