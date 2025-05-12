#ifndef _COUPONFILTER_H
#define _COUPONFILTER_H

#include <cstdint>
#include <iostream>
#include <ctime>
#include <cmath>
#include <cstring>
#include "./Xorshift.h"
#include "Sketch.h"

#define MAX_VALUE 0xFFFFFFFF
#define NUM_BITS 8 // size of each item

struct Cpf_Param {
    uint32_t m;
    uint32_t c;
    double p;
    char mea_tag;
};

// implementation of CouponFilter, derived from:  https://github.com/duyang92/coupon-filter-paper

class CouponFilter : public Sketch {
private:
    // @params: m - num of filter units
    //          c - size of each filter unit (in bits, in fact, the num of coupon should be collected)
    double p;
    uint32_t m;
    uint32_t c;
    char mea_tag;

    uint32_t seed;       // seed for murmurhash
    uint8_t *bitmap;
    Sketch* skt1;
    xorshift::xorshift32 rng;

    uint32_t get_unit_index(uint32_t flow_id);
    int get_coupon_index(uint32_t flow_id, uint32_t pkt_id);

public:

    CouponFilter(float memory_kb, Sketch* sketch1);

    ~CouponFilter() {
        if (bitmap) {
            delete[] bitmap;
            bitmap = nullptr;
        }
    }

    void update(uint32_t pkt_id, uint32_t flow_id, uint32_t weight = 1);
    int report(uint32_t flow_id);

};

#endif // _COUPONFILTER_H
