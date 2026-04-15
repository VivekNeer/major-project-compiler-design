/* Bit counting (population count).
 * Directly adapted from MiBench automotive/bitcount.
 * Counts the number of set bits in an integer using
 * the classic shift-and-mask approach.
 * Exercises: loops, bitwise-like arithmetic, conditionals.
 *
 * Note: Since our language lacks bitwise operators, we simulate
 * bit counting using division by 2 (equivalent to right-shift)
 * and modulo 2 (equivalent to AND 1).
 */
int bitcount(int n) {
    int count = 0;
    while (n > 0) {
        int bit = n % 2;
        if (bit == 1) {
            count = count + 1;
        }
        n = n / 2;
    }
    return count;
}

int main() {
    int num = 255;
    int result = bitcount(num);
    print(result);

    int num2 = 1023;
    int result2 = bitcount(num2);
    print(result2);

    return 0;
}
