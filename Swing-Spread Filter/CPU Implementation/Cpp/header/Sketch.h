
#ifndef SKETCH_H
#define SKETCH_H
#include <iostream>
#include <cstdlib>
#include <cstdint>
#include <ctime>
#include <unordered_map>
#include <unordered_set>
#include <cmath>
#include "MurmurHash3.h"
#include <random>
#include <vector>
#include <cassert>
#include <chrono>

#define KEY_BYTE_LEN 4
#define HASH_SEED 1201

class Sketch {
public:
    const std::vector<uint32_t> HASH_SEED_ARR = {1999, 5701, 7723, 9973, 10211, 21211};

    virtual ~Sketch() = default;
    virtual void update(const uint32_t key, const uint32_t element) = 0;
    virtual uint32_t query(const uint32_t key) = 0;
};

#endif
