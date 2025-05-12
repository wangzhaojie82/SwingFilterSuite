#!/bin/bash

# options
optimize_flag="-O3"

# compile
echo "Compiling LoglogFilter with $optimize_flag optimization flag..."
g++ ./LogLogFilter.cpp ../MurmurHash3.cpp ../CountMin.cpp ./main_log.cpp -o Log -std=c++17 -I ../C++ $optimize_flag

if [ $? -eq 0 ]; then
    echo "Compilation successful. Running LogLogFilter..."
    ./Log -total_mem $1 -mem_ratio $2
    rm -rf ./Log
else
    echo "Compilation failed. Exiting."
    exit 1
fi