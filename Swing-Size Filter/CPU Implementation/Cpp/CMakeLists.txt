cmake_minimum_required(VERSION 3.26)
project(Cpp)
set(CMAKE_CXX_STANDARD 17)
add_executable(Cpp main.cpp
        ColdFilter.cpp
        CountMin.cpp
        CouponFilter.cpp
        LogLogFilter.cpp
        MurmurHash3.cpp
        SwingFilter.cpp)
