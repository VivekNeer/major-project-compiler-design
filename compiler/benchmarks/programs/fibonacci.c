/* Fibonacci sequence computation.
 * Adapted from MiBench basicmath category.
 * Computes the Nth Fibonacci number iteratively.
 * Exercises: loops, arithmetic, variable updates.
 */
int main() {
    int n = 20;
    int a = 0;
    int b = 1;
    int i = 0;
    int temp;

    while (i < n) {
        temp = a + b;
        a = b;
        b = temp;
        i = i + 1;
    }

    print(a);
    return 0;
}
