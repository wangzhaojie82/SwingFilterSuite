#!/bin/bash

# options
optimize_flag="-O3"

# compile
echo "Compiling SwingFilter with $optimize_flag optimization flag..."
g++ ./SwingFilter.cpp ../MurmurHash3.cpp ../CountMin.cpp ./main_bf.cpp -o BF -std=c++17 -I ../C++ $optimize_flag

if [ $? -eq 0 ]; then
    echo "Compilation successful. Running SwingFilter..."
    ./BF -total_mem $1 -mem_ratio $2
    rm -rf ./BF
else
    echo "Compilation failed. Exiting."
    exit 1
fi