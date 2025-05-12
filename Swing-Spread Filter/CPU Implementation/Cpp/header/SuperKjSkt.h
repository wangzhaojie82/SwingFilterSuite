#ifndef SKJSKT_H
#define SKJSKT_H

#include "Sketch.h"
#define MAX(a,b) ((a)<(b))?(b):(a)
#define MIN(a,b) ((a)<(b))?(a):(b)


//
// Created by Hanwen
// An implementation for paper: From CountMin to Super kJoin Sketches for Flow Spread Estimation
// available at https://doi.org/10.1109/TNSE.2023.3279665
// Super kJoin version
//


class SuperKjSkt : public Sketch{
private:
    uint32_t k, m, l;
    uint32_t z;

    uint32_t s_l, s_m;

    uint8_t ** C;
    uint32_t eleseed;
    uint32_t **keyseeds;
    uint32_t num_of_leading_bits;
    double alpha;

public:
    SuperKjSkt(uint32_t);

    ~SuperKjSkt() {
        for (int i = 0; i < k; ++i) {
            delete[] C[i];
            delete[] keyseeds[i];
        }
    }

    void update(uint32_t, uint32_t);
    uint32_t query(uint32_t);
    void spreadEstimation(
            const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
            const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi);

};
#endif