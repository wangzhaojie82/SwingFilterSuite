#include <numeric>
#include <unordered_set>
#include "../header/SwingFilter.h"

#include <algorithm>

SwingFilter::SwingFilter(float memory_kb, Sketch* sketch1): sketch(sketch1){
    d = 3;
    bits[0] = 4;
    bits[1] = 8;

    seeds = new unsigned *[2];
    for (int i = 0; i < 2; ++i) {
        seeds[i] = new unsigned[d];
    }
    std::unordered_set<uint32_t> set;
    while (set.size() != 2 * d) {
        set.insert(rand() % 50000);
    }
    int count = 0;
    for (auto iter = set.begin(); iter != set.end(); iter ++, count ++) {
        if (count < d) {
            seeds[0][count] = *iter;
        } else {
            seeds[1][count - d] = *iter;
        }
    }
    max_positive[0] = (1 << (bits[0] - 1)) - 1;
    max_positive[1] = (1 << (bits[1] - 1)) - 1;
    min_negative[0] = -(1 << (bits[0] - 1));
    min_negative[1] = -(1 << (bits[1] - 1));

    uint32_t memory_bits = static_cast<uint32_t>(std::round(memory_kb * 1024 * 8));

    // Memory allocation: SF two layers of memory each occupy 50%
    uint32_t memory_bits_layer_0 = static_cast<uint32_t>(std::round(memory_bits * 0.5));
    uint32_t memory_bits_layer_1 = memory_bits - memory_bits_layer_0;

    num_counters[0] = static_cast<uint32_t>(std::round(memory_bits_layer_0 / bits[0]));
    num_counters[1] = static_cast<uint32_t>(std::round(memory_bits_layer_1 / bits[1]));

    counters = new int *[2];
    // Allocate memory for int arrays
    counters[0] = new int[num_counters[0]]{0}; // layer 1
    counters[1] = new int[num_counters[1]]{0}; // layer 2
    std::cout << num_counters[0] << "  " << num_counters[1] << std::endl;
    p = 12412;
}


int SwingFilter::hash_s(uint32_t flow_label, uint32_t& counter_index) {
    return (flow_label ^ counter_index) & 1;
}

int SwingFilter::hash_s2(char* flow_label, uint32_t& counter_index) {
    uint32_t hash_value;
    MurmurHash3_x86_32(flow_label, KEY_LEN, counter_index, &hash_value);
    return hash_value % 2 == 0;
}

uint32_t myhash(uint32_t flow_label, uint32_t rand_value) {
    return 177 * (flow_label) + rand_value;
}

void SwingFilter::update(const int packet_id, uint32_t flow_label, uint32_t weight){
    char hash_input_str[5] = {0};
    memcpy(hash_input_str, &flow_label, sizeof(uint32_t));
    uint32_t index_hash; // used to calculate the counter index
    uint32_t rand_value = packet_id % d;
    index_hash = myhash(flow_label, rand_value);
    
    for (uint32_t i = 0; i < 2; ++i) {
        uint32_t j = index_hash % num_counters[i];
        int op_ = hash_s(flow_label, j);
        int current_value = counters[i][j];
        int next_value;
        if (op_) {
            next_value = current_value + 1;
            if (next_value > max_positive[i])
                continue;
        } else {
            next_value = current_value - 1;
            if (next_value < min_negative[i])
                continue;
        }
        counters[i][j] = next_value;
        return;

    }
    sketch->update(packet_id, flow_label);
}


int SwingFilter::report(uint32_t flow_label){
    int estimation = 0;
    char hash_input_str[5] = {0};
    memcpy(hash_input_str, &flow_label, sizeof(uint32_t));
    uint32_t hash_value = 0;
    bool large_flow_flag = true;

    for (uint32_t i = 0; i < 2; ++i) {
        int es_per_layer = 0;
        for (int c = 0; c < d; c++) {
            hash_value = myhash(flow_label, c);
            uint32_t j = hash_value % num_counters[i];
            int op_ = hash_s(flow_label, j);
            int es_;
            if (op_ == 0)
                es_ = counters[i][j] * -1;
            else
                es_ = counters[i][j];
            /*if (flow_label == 1333769258) {
                std::cout << i << " level, j is " << j << ", counter value is " << counters[i][j] << ", opt is " << op_ << std::endl;
            }*/
            es_per_layer += es_;
        }
        estimation += es_per_layer;
        /*if (flow_label == 1333769258) {
            std::cout << estimation << " before add sketch..." << std::endl;
        }*/
        // if the estimated size less than counter capacity of this layer
        if (es_per_layer < d * max_positive[i] ){
            large_flow_flag = false;
            break;
        }
    }
    if(large_flow_flag){
        estimation += sketch->report(flow_label);
    }

    return estimation;
}
