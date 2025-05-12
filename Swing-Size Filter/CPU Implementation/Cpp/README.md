# C++ implementation

This is a C++ implementation for Swing-Size Filter and related filters. The source code for LadderFilter is provided by the authors in their repository [LadderFilterCode/LadderFilter (github.com)](https://github.com/LadderFilterCode/LadderFilter).

## Project Structure

```
Cpp/
├── main.cpp
├── header/
│   ├── MurmurHash3.h
│   ├── Sketch.h
│   ├── CountMin.h
│   ├── SwingFilter.h
│   ├── CouponFilter.h
│   ├── ColdFilter.h
│   ├── Xorshift.h
│   └── LogLogFilter.h
├── MurmurHash3.cpp
├── CountMin.cpp
├── SwingFilter.cpp
├── ColdFilter.cpp
├── CouponFilter.cpp
└── LogLogFilter.cpp
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
