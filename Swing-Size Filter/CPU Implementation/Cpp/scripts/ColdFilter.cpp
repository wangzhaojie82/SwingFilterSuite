#include "../headers/ColdFilter.h"


ColdFilter::ColdFilter(float memory_kb, Sketch* sketch1) {
    d = 3;
    bits[0] = 4;
    bits[1] = 16;
    thres[0] = 15;
    thres[1] = 985;
    sketch = sketch1;
    uint32_t memory_bits = static_cast<uint32_t>(std::round(memory_kb * 1024 * 8));
    uint32_t memory_bits_layer_0 = static_cast<uint32_t>(std::round(memory_bits * 0.5));
    uint32_t memory_bits_layer_1 = memory_bits - memory_bits_layer_0;
    num_counters[0] = static_cast<uint32_t>(std::round(memory_bits_layer_0 / bits[0]));
    num_counters[1] = static_cast<uint32_t>(std::round(memory_bits_layer_1 / bits[1]));
    counters = new uint32_t *[2];
    counters[0] = new uint32_t[num_counters[0]]{0}; // layer 1
    counters[1] = new uint32_t[num_counters[1]]{0}; // layer 2
}


void ColdFilter::update(const int packet_id, uint32_t flow_label, uint32_t weight) {
    bool flag = false;
    char hash_input_str[5] = {0};
    memcpy(hash_input_str, &flow_label, sizeof(uint32_t));
    uint32_t index_hash; // used to calculate the counter index
    std::vector<std::pair<uint32_t, uint32_t>> min_indices;
    for (int i = 0; i < 2; ++i) {
        min_indices.clear(); // Clear previous indices
        uint32_t min_value = UINT32_MAX;
        for (int j = 0; j < d; ++j) {
            uint32_t seed = i*10+j;
            index_hash = 0;
            MurmurHash3_x86_32(hash_input_str, KEY_LEN, seed, &index_hash);
            uint32_t idx = index_hash % num_counters[i];
            uint32_t val = counters[i][idx];
            if (val < min_value) {
                min_value = val;
                min_indices.clear(); // Clear previous indices
                min_indices.push_back(std::make_pair(i, idx)); // Record the new minimum index
            } else if (val == min_value) {
                min_indices.push_back(std::make_pair(i, idx)); // Record another index with the same minimum value
            }
        }

        for (const auto& index : min_indices) {
            uint32_t i_idx = index.first;
            uint32_t j_idx = index.second;
            // Update the minimum counter at position (i, j)
            // For example, increment it by 1
            uint32_t current_val = counters[i_idx][j_idx];
            if (current_val < thres[i]) {
                counters[i_idx][j_idx] += 1;
                flag = true;
            }
        }

        if (flag)
            return;
    }

    if (!flag)
        sketch->update(packet_id, flow_label, 1);
}


int ColdFilter::report(uint32_t flow_label) {
    char hash_input_str[5] = {0};
    memcpy(hash_input_str, &flow_label, sizeof(uint32_t));
    uint32_t index_hash; // used to calculate the counter index
    int estimation = 0;
    for (int i = 0; i < 2; ++i) {
        uint32_t min_value = UINT32_MAX;
        for (int j = 0; j < d; ++j) {
            MurmurHash3_x86_32(hash_input_str, KEY_LEN, i * 10 + j, &index_hash);

            uint32_t idx = index_hash % num_counters[i];
            uint32_t val = counters[i][idx];
            if (val < min_value)
                min_value = val;
        }
        estimation += int(min_value);
        if (min_value < thres[i])
            return estimation;
    }
    estimation += sketch->report(flow_label);
    return estimation;
}
