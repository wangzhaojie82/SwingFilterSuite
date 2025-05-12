
#ifndef SKETCH_H
#define SKETCH_H
#include <iostream>
#include <cstdlib>
#include <cstdint>
#include <ctime>
#include <cstring>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <cmath>
#include "MurmurHash3.h"
#include <random>
#define KEY_LEN 4 // byte length of key

class Sketch {
public:
    virtual void update(const uint32_t packet_id, const uint32_t flow_label, uint32_t weight= 1) = 0;
    virtual int report(const uint32_t flow_label) = 0;
};

#endif
