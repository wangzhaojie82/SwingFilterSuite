#!/bin/bash

# options
optimize_flag="-O3"

# compile
echo "Compiling ColdFilter with $optimize_flag optimization flag..."
g++ ./ColdFilter.cpp ../MurmurHash3.cpp ../CountMin.cpp ./main_cf.cpp -o CF -std=c++17 -I ../C++ $optimize_flag

if [ $? -eq 0 ]; then
    echo "Compilation successful. Running ColdFilter..."
    ./CF -total_mem $1 -mem_ratio $2
    rm -rf ./CF
else
    echo "Compilation failed. Exiting."
    exit 1
fi