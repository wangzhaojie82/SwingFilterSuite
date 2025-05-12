#include <fstream>
#include "header/CSE.h"

CSE::CSE(uint32_t memory_kb ) {
    uint32_t m = memory_kb * 8 * 1024;
    uint32_t v = 8192;
    this->m = m;
    this->v = v;
    this->c = m;
    bitmap = allocbitmap(m);
    fillzero(bitmap, this->m);
    srand(time(NULL));
    seed = uint32_t(rand());
}

void CSE::update(uint32_t key, uint32_t ele) {
    uint32_t hashValue, hashIndex;
    char hash_input_key[5] = {0};
    char hash_input_ele[5] = {0};
    memcpy(hash_input_key, &key, sizeof(uint32_t));
    memcpy(hash_input_ele, &ele, sizeof(uint32_t));
    MurmurHash3_x86_32(hash_input_ele, 4, seed, &hashValue);
    hashIndex = hashValue % v;
    MurmurHash3_x86_32(hash_input_key, 4, hashIndex, &hashValue);
    hashIndex = hashValue % m;
    if (!getbit(hashIndex, bitmap)) {
        setbit(hashIndex, bitmap);
        this->c -= 1;
    }
}


uint32_t CSE::query(uint32_t key) {
    uint32_t z_ = 0;
    uint32_t hashIndex, hashValue;
    char hash_input_key[5] = {0};
    memcpy(hash_input_key, &key, sizeof(uint32_t));
    double est = 0.0;
    for (int i = 0; i < v; ++i) {
        MurmurHash3_x86_32(hash_input_key, 4, i, &hashValue);
        hashIndex = hashValue % m;
        if (!getbit(hashIndex, bitmap))
            z_ ++;
    }
    if (z_ == 0 && c == 0) {
        est = - v * log(1.0 * m) + v * log(1.0 * v);
    } else if (c == 0 && z_ != 0) {
        est = - (v * log(1.0 * z_ / v) + v * log(1.0 * m));
    } else if (c != 0 && z_ == 0) {
        est = v * log((1.0 * c * v) / m);
    } else {
        est = v * log(1.0 * c / m) - v * log(1.0 * z_ / v);
    }
    if (est < 0) est = 0;
    return static_cast<uint32_t>(est);
}


void CSE::spreadEstimation(
        const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
        const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi) {

    for (const auto& [key, element] : dataset) {
        update(key, element);
    }

    float total_are = 0.0f;
    int count = 0;

    for (const auto& entry : true_cardi) {
        uint32_t flow_label = entry.first;
        uint32_t true_value = entry.second.size();
        uint32_t estimated_value = query(flow_label);
        if (true_value > 0) {
            float are = std::abs(static_cast<float>(estimated_value) - static_cast<float>(true_value)) / static_cast<float>(true_value);
            total_are += are;
            ++count;
        }
    }

    if (count > 0) {
        float avg_are = total_are / count;
        std::cout << "ARE: " << avg_are << std::endl;

    } else {
        std::cout << "No data to calculate ARE." << std::endl;
    }

}
