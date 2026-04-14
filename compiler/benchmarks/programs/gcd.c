/* Greatest Common Divisor (Euclidean algorithm).
 * Adapted from MiBench basicmath category.
 * Classic number-theory computation using modulo.
 * Exercises: loops, modulo, conditionals, comparison.
 */
int gcd(int a, int b) {
    int temp;
    while (b != 0) {
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    int x = 48;
    int y = 18;
    int result = gcd(x, y);
    print(result);
    return 0;
}
