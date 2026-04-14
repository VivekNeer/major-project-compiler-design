/* Modular Exponentiation (Fast Power).
 * Adapted from MiBench security/blowfish and security/pgp
 * families, which rely on modular exponentiation as a core
 * cryptographic primitive.
 * Uses the square-and-multiply algorithm.
 * Exercises: while loops, conditionals, modulo, multiplication.
 * Optimization opportunities: strength reduction on mod/mul,
 * constant folding of test values, CSE on repeated modulo.
 */
int mod_exp(int base, int exp, int mod) {
    int result = 1;
    base = base % mod;
    while (exp > 0) {
        int remainder = exp % 2;
        if (remainder == 1) {
            result = (result * base) % mod;
        }
        exp = exp / 2;
        base = (base * base) % mod;
    }
    return result;
}

int main() {
    /* RSA-style modular exponentiation tests */
    int r1 = mod_exp(2, 10, 1000);
    print(r1);

    int r2 = mod_exp(3, 13, 100);
    print(r2);

    int r3 = mod_exp(7, 5, 37);
    print(r3);

    /* Common subexpression: same base and mod */
    int b = 5;
    int m = 97;
    int r4 = mod_exp(b, 20, m);
    int r5 = mod_exp(b, 21, m);
    print(r4);
    print(r5);

    return 0;
}
