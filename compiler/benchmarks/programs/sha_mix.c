/* SHA-inspired Integer Mixing.
 * Adapted from MiBench security/sha.
 * Captures the iterative mixing/hashing structure of SHA's
 * compression function using integer arithmetic. The original
 * SHA uses bitwise operations; we approximate with modular
 * arithmetic to stay within our language subset.
 * Exercises: deeply nested conditionals, while loop, modulo,
 * heavy arithmetic, function calls.
 * Optimization opportunities: constant folding of modular constants,
 * algebraic simplification, common subexpressions in conditional arms.
 */
int sha_mix(int a, int b, int c, int rounds) {
    int i = 0;
    int h = a;
    while (i < rounds) {
        int f = 0;
        int phase = i % 4;
        if (phase == 0) {
            f = (b * c) % 65536;
        } else {
            if (phase == 1) {
                f = (b + c) % 65536;
            } else {
                if (phase == 2) {
                    f = (b - c + 65536) % 65536;
                } else {
                    f = (b * 3 + c * 7) % 65536;
                }
            }
        }
        h = (h + f) % 65536;
        b = (b + h) % 65536;
        c = (c + b) % 65536;
        i = i + 1;
    }
    return h;
}

int main() {
    /* SHA-like mixing with different round counts */
    int r1 = sha_mix(12345, 67890, 11111, 16);
    print(r1);

    int r2 = sha_mix(1, 2, 3, 32);
    print(r2);

    int r3 = sha_mix(255, 128, 64, 8);
    print(r3);

    /* Dead code: unused computation */
    int unused = sha_mix(0, 0, 0, 4);

    return 0;
}
