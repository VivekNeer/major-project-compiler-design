/* Factorial computation.
 * Adapted from MiBench basicmath patterns.
 * Computes factorial iteratively — exercises multiplication loops.
 * Also demonstrates dead code and constant folding opportunities.
 */
int factorial(int n) {
    int result = 1;
    int i = 1;
    while (i <= n) {
        result = result * i;
        i = i + 1;
    }
    return result;
}

int main() {
    /* Constant expressions that can be folded */
    int base = 2 + 3;
    int extra = 10 - 5;

    int val = factorial(base);
    print(val);

    /* Dead code: result never used */
    int unused = 42 * 2;
    int also_unused = unused + 100;

    /* Common subexpression: base + extra computed twice */
    int sum1 = base + extra;
    int sum2 = base + extra;
    print(sum1);
    print(sum2);

    return 0;
}
