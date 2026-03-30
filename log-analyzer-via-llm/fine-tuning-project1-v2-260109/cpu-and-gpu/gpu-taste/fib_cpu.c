// fib_cpu.c
#include <stdio.h>
#include <time.h>

long long fib_cpu(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1, c;
    for (int i = 2; i <= n; ++i) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}

int main() {
    const int N = 45;
    clock_t start = clock();
    long long result = fib_cpu(N);
    clock_t end = clock();
    double time_sec = ((double)(end - start)) / CLOCKS_PER_SEC;

    printf("CPU: fib(%d) = %lld, time = %.4f s\n", N, result, time_sec);
    return 0;
}