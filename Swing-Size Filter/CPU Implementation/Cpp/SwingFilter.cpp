
#include "header/SwingFilter.h"

SwingFilter::SwingFilter(float memory_kb, Sketch* sketch1): skt1(sketch1){
    d = 3;
    bits[0] = 4;
    bits[1] = 8;

    max_positive[0] = 7;
    max_positive[1] = 127;
    min_negative[0] = -8;
    min_negative[1] = -128;

    uint32_t memory_bits = static_cast<uint32_t>(std::round(memory_kb * 1024 * 8));

    // Memory allocation: BF two layers of memory each occupy 50%
    uint32_t memory_bits_layer_0 = static_cast<uint32_t>(std::round(memory_bits * 0.50));
    uint32_t memory_bits_layer_1 = memory_bits - memory_bits_layer_0;

    num_counters[0] = static_cast<uint32_t>(std::round(memory_bits_layer_0 / bits[0]));
    num_counters[1] = static_cast<uint32_t>(std::round(memory_bits_layer_1 / bits[1]));

    counters = new int *[2];
    // Allocate memory for int arrays
    counters[0] = new int[num_counters[0]]{0};
    counters[1] = new int[num_counters[1]]{0};

    // Initialize counters to 0
    for (int i = 0; i < 2; ++i) {
        for(int j = 0; j < num_counters[i]; j++)
            counters[i][j] = 0;
    }

}


int SwingFilter::hash_s(const uint32_t flow_label, uint32_t& counter_index) {
    uint32_t hash_value = 0;
    MurmurHash3_x86_32(&flow_label, 4, counter_index, &hash_value);
    return hash_value % 2 == 0;
}


void SwingFilter::update(const uint32_t packet_id, const uint32_t flow_label, uint32_t weight){

    uint32_t index_hash; // used to calculate the counter index
    uint32_t rand_value = packet_id % d;
    MurmurHash3_x86_32(&flow_label, 4, rand_value + 1999, &index_hash);

    for (int i = 0; i < 2; ++i) {
        uint32_t j = index_hash % num_counters[i];
        int op_ = hash_s(flow_label, j);
        int current_value = counters[i][j];
        int next_value;
        if (op_ == 1){
            next_value = current_value + 1;
            if (next_value <= max_positive[i]){
                counters[i][j] = next_value;
                return;
            }
        } else{
            next_value = current_value - 1;
            if (next_value >= min_negative[i]){
                counters[i][j] = next_value;
                return;
            }
        }
    }
    skt1->update(packet_id, flow_label);
}


int SwingFilter::report(const uint32_t flow_label){

    int estimation = 0;
    bool large_flow_flag = true;

    for (int i = 0; i < 2; ++i) {
        int es_per_layer = 0;
        for (int c = 0; c < d; c++) {
            uint32_t hash_value = 0;
            MurmurHash3_x86_32(&flow_label, 4, c + 1999, &hash_value);
            uint32_t j = hash_value % num_counters[i];
            int op_ = hash_s(flow_label, j);
            int es_ = counters[i][j] * op_;
            es_per_layer += es_;
        }
        estimation += es_per_layer;
        // if the estimated size less than counter capacity of this layer
        if (es_per_layer < d * max_positive[i] ){
            large_flow_flag = false;
            break;
        }
    }
    if(large_flow_flag){
        estimation += skt1->report(flow_label);
    }
    return estimation;
}
