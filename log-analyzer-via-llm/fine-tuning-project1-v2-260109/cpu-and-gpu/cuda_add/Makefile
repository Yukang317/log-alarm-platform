# apt install nsight-systems-2025.5.2

CXX   = g++
NVCC  = nvcc

CXXFLAGS = -O0 -std=c++11
NVCCFLAGS = -O0 -gencode arch=compute_89,code=sm_89

TARGETS = cpu gpu1 gpu2 gpu3 gpu4

.PHONY: all clean prof nsys

all: $(TARGETS)

cpu: cpu.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

gpu1: gpu1.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

gpu2: gpu2.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

gpu3: gpu3.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

gpu4: gpu4.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

clean:
	-rm -rfv $(TARGETS)
	-rm -rfv *.nsys-rep
	-rm -rfv *.sqlite

prof: $(TARGETS)
	nvprof ./cpu
	nvprof ./gpu1
	nvprof ./gpu2
	nvprof ./gpu3
	nvprof ./gpu4

# nsys stats --report cuda_api_sum xxx.nsys-rep
# nsys stats --report cuda_gpu_mem_time_sum xxx.nsys-rep
# nsys stats --report cuda_gpu_kern_sum xxx.nsys-rep
nsys: $(TARGETS)
	nsys profile --trace=cuda,nvtx,osrt ./cpu
	nsys profile --trace=cuda,nvtx,osrt ./gpu1
	nsys profile --trace=cuda,nvtx,osrt ./gpu2
	nsys profile --trace=cuda,nvtx,osrt ./gpu3
	nsys profile --trace=cuda,nvtx,osrt ./gpu4