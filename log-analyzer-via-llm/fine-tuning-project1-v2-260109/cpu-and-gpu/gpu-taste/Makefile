# 编译器设置
CC      = gcc
NVCC    = nvcc

# 编译选项
CFLAGS  = -O2 -Wall
NVCCFLAGS = -O2

# 目标文件
TARGET_CPU = fib_cpu
TARGET_GPU = fib_gpu

# 默认目标
.PHONY: all cpu gpu clean

all: cpu gpu

cpu: $(TARGET_CPU)

gpu: $(TARGET_GPU)

$(TARGET_CPU): fib_cpu.c
	$(CC) $(CFLAGS) $< -o $@

$(TARGET_GPU): fib_gpu.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

clean:
	rm -f $(TARGET_CPU) $(TARGET_GPU)