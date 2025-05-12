cmake_minimum_required(VERSION 3.26)
project(Cpp)

set(CMAKE_CXX_STANDARD 17)

add_executable(Cpp main.cpp
        Couper.cpp
        CouponFilter.cpp
        CSE.cpp
        KjSkt.cpp
        LogLogFilter_Spread.cpp
        MurmurHash3.cpp
        rSkt.cpp
        SuperKjSkt.cpp
        SwingFilterSpread.cpp
        vHLL.cpp)
