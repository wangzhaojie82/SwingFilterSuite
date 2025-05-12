# C++ implementation

This is a C++ implementation for Swing-Spread Filter and the other related filters. 

## Project Structure

```
Cpp/
├── main.cpp
├── header/
│   ├── bitmap.h
│   ├── Couper.h
│   ├── CouponFilter.h
│   ├── CSE.h
│   ├── KjSkt.h
│   ├── LogLogFilter_Spread.h
│   ├── MurmurHash3.h
│   ├── rSkt.h
│   ├── Sketch.h
│   ├── SuperKjSkt.h
│   ├── SwingFilterSpread.h
│   ├── vHLL.h
│   └── Xorshift.h
├── MurmurHash3.cpp
├── Couper.cpp
├── CouponFilter.cpp
├── CSE.cpp
├── KjSkt.cpp
├── LogLogFilter_Spread.cpp
├── rSkt.cpp
├── SuperKjSkt.cpp
├── SwingFilterSpread.cpp
└── vHLL.cpp
```

## Usage

### Compilation

```bash
$ mkdir build
$ cd build
$ cmake ..
$ make
```

### Execution

```bash
$ ./Cpp
```

## Requirements

- CMake 3.26 or above
- Compiler with support for C++17 standard
