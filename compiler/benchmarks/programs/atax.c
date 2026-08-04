/* Matrix Transpose and Vector Multiplication: y := A^T * (A * x).
 * Adapted from PolyBench/C's linear-algebra/kernels/atax kernel.
 * Fixed-size (5x5) matrix stored as a flattened 1D array.
 * Exercises: two sequential reduction loops sharing an intermediate
 * array, accumulation into array elements across an outer loop.
 * Optimization opportunities: copy propagation and CSE on the
 * repeated `i * n + j` index expression, strength reduction on the
 * multiplication inside it.
 */
int main() {
    int n = 5;

    int a[25];
    int x[5];
    int tmp[5];
    int y[5];

    int i = 0;
    while (i < n) {
        int j = 0;
        while (j < n) {
            a[i * n + j] = (i + j) % 4 + 1;
            j = j + 1;
        }
        x[i] = i + 1;
        tmp[i] = 0;
        y[i] = 0;
        i = i + 1;
    }

    i = 0;
    while (i < n) {
        int j = 0;
        while (j < n) {
            tmp[i] = tmp[i] + a[i * n + j] * x[j];
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < n) {
        int j = 0;
        while (j < n) {
            y[j] = y[j] + a[i * n + j] * tmp[i];
            j = j + 1;
        }
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
