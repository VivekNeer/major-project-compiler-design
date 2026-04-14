/* Collatz conjecture (3n+1 problem).
 * Adapted from MiBench automotive computation patterns.
 * Counts how many steps it takes for a number to reach 1
 * under the Collatz iteration.
 * Exercises: loops, conditionals, mixed arithmetic, modulo.
 */
int collatz_steps(int n) {
    int steps = 0;
    while (n != 1) {
        int remainder = n % 2;
        if (remainder == 0) {
            n = n / 2;
        } else {
            n = 3 * n + 1;
        }
        steps = steps + 1;
    }
    return steps;
}

int main() {
    /* Test with several starting values */
    int s1 = collatz_steps(27);
    print(s1);

    int s2 = collatz_steps(97);
    print(s2);

    int s3 = collatz_steps(256);
    print(s3);

    return 0;
}
