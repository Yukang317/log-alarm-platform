// fib_gpu.cu
#include <cuda_runtime.h>
#include <stdio.h>
#include <time.h>

__global__ void fib_gpu_kernel(int n, long long* result) {
    // 注意：这里只启动一个线程！完全串行！
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        if (n <= 1) {
            *result = n;
            return;
        }
        long long a = 0, b = 1, c;
        for (int i = 2; i <= n; ++i) {
            c = a + b;
            a = b;
            b = c;
        }
        *result = b;
    }
}

int main() {
    const int N = 45;
    long long h_result;
    long long* d_result;
    cudaMalloc(&d_result, sizeof(long long));

    // 记录时间（包括 kernel 启动 + 数据拷贝）
    clock_t start = clock();

    // 启动仅 1 个线程的 kernel
    fib_gpu_kernel<<<1, 1>>>(N, d_result);

    // 同步并拷回结果
    cudaMemcpy(&h_result, d_result, sizeof(long long), cudaMemcpyDeviceToHost);
    cudaDeviceSynchronize();

    clock_t end = clock();
    double time_sec = ((double)(end - start)) / CLOCKS_PER_SEC;

    printf("GPU: fib(%d) = %lld, time = %.4f s\n", N, h_result, time_sec);

    cudaFree(d_result);
    return 0;
}