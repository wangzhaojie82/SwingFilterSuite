#include <algorithm>
#include <fstream>
#include "header/CouponFilter.h"

CouponFilter::CouponFilter(float memory_kb, Sketch* sketch1): skt1(sketch1){
    this->c = 6;
    this->p = 0.1;
    uint32_t memory_bits = memory_kb * 1024 * 8;
    this->m = memory_bits / this->c;

    srand(time(NULL));
    seed = uint32_t(rand());
    rng.seed(uint32_t(rand()));

    bitmap = new uint8_t[m];
    memset(bitmap, 0, sizeof(uint8_t) * m);
}


uint32_t CouponFilter::get_unit_index(uint32_t flow_id) {
    uint64_t hash_val[2];
    char hash_input_str[9] = {0};
    memcpy(hash_input_str, &flow_id, sizeof(uint32_t));
    MurmurHash3_x86_128(hash_input_str, sizeof(hash_input_str), seed, hash_val);
    return hash_val[0] % m;
}

int CouponFilter::get_coupon_index(uint32_t flow_id, uint32_t pkt_id) {
    uint32_t hash_val = 0;
    char hash_input_str[13] = {0};

    if (mea_tag == 'f') {
        uint32_t rand_val = rng();
        memcpy(hash_input_str, &flow_id, sizeof(uint32_t));
        memcpy(hash_input_str + 4, &rand_val, sizeof(uint32_t));
        MurmurHash3_x86_32(hash_input_str, 8, seed, &hash_val);
    }
    else if (mea_tag == 'c') {
        memcpy(hash_input_str, &flow_id, sizeof(uint32_t));
        memcpy(hash_input_str + 4, &pkt_id, sizeof(uint32_t));
        MurmurHash3_x86_32(hash_input_str, 8, seed, &hash_val);
    }
    else if (mea_tag == 'p') {
        memcpy(hash_input_str, &flow_id, sizeof(uint32_t));
        memcpy(hash_input_str + 8, &pkt_id, sizeof(uint32_t));
        MurmurHash3_x86_32(hash_input_str, 12, seed, &hash_val);
    }

    for (int i = 0; i < c; i++) {
        if (double(hash_val) < p * (i + 1) * uint32_t(MAX_VALUE)) {
            return i;
        }
    }
    return -1;
}

void CouponFilter::update(uint32_t pkt_id, uint32_t flow_id, uint32_t weight ) {
    int coupon_index = get_coupon_index(flow_id, pkt_id);
    uint32_t unit_index = get_unit_index(flow_id);

    if (coupon_index >= 0) {
        bitmap[unit_index] |= (1 << coupon_index);
    }

    if (bitmap[unit_index] == (uint8_t(1 << c) - 1)) {
        skt1->update(pkt_id, flow_id);
    }
}

int CouponFilter::report(uint32_t flow_id) {
    int ans_t = skt1->report(flow_id);
    uint32_t unit_index = get_unit_index(flow_id);
    uint8_t val = bitmap[unit_index];
    int count = 0;
    for (int i = 0; i < c; ++i) {
        if (val & (1 << i)) {
            ++count;
        }
    }
    if (ans_t != 0)
        ans_t += count/p;
    else
        ans_t = count/p;
    return ans_t;
}
