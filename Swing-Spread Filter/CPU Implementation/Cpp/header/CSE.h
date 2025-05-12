

#ifndef CSE_H
#define CSE_H

#define KEY_LEN 16
#include "Sketch.h"
#include "bitmap.h"
#include "cmath"
#include "ctime"
#include "cstring"
#include <cstdlib>

class CSE : public Sketch {
private:
    uint32_t m, v;
    uint8_t* bitmap;
    uint32_t c;
    uint32_t seed;
public:
    CSE(uint32_t memory_kb);
    ~CSE() {
        delete bitmap;
    }
    void update(uint32_t, uint32_t);

    uint32_t query(const uint32_t key);

    void spreadEstimation(
            const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
            const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi);

};



#endif
