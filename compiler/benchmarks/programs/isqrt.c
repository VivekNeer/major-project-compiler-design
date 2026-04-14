/* Integer Square Root via Newton's Method.
 * Directly adapted from MiBench automotive/basicmath.
 * The isqrt function is the core kernel of basicmath's
 * integer square root computation.
 * Exercises: while loops, division, convergence iteration.
 * Optimization opportunities: constant folding of test inputs,
 * strength reduction on division, dead code elimination.
 */
int isqrt(int n) {
    int x = n;
    int y = 1;
    while (x > y) {
        x = (x + y) / 2;
        y = n / x;
    }
    return x;
}

int main() {
    /* Test with several values from basicmath workload */
    int r1 = isqrt(144);
    print(r1);

    int r2 = isqrt(1000000);
    print(r2);

    int r3 = isqrt(2 * 2 * 3 * 3 * 5 * 5);
    print(r3);

    int r4 = isqrt(1);
    print(r4);

    int r5 = isqrt(81);
    print(r5);

    return 0;
}
