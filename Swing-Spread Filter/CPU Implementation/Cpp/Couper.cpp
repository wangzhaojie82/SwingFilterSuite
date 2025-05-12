#include <fstream>
#include "header/Couper.h"


// Constructor: Calculate L1 based on memory size and initialize the filter
Couper::Couper(float memory_kb, Sketch* skt): sketch(skt) {
    b = 12;
    tau = 9;
    uint64_t total_bits = static_cast<uint64_t>(memory_kb * 1024 * 8);
    L1 = total_bits / b;
    // false is as 0, true is as 1
    filter.resize(L1, std::vector<bool>(b, false));
}


void Couper::update(const uint32_t key, const uint32_t element) {
    uint32_t key_hash_val;
    // Hash the key with the chosen hash function
    MurmurHash3_x86_32(&key, KEY_BYTE_LEN, HASH_SEED, &key_hash_val);
    uint32_t bitmap_idx = key_hash_val % L1;

    // Count the number of 1s in the bitmap
    uint32_t cf = 0;

    for (uint32_t i = 0; i < b; i++) {
        if (filter[bitmap_idx][i]) {
            cf++;
        }
    }

    // Case 1: cf < Tau
    if (cf < tau) {
        uint32_t element_hash_val;
        MurmurHash3_x86_32(&element, KEY_BYTE_LEN, HASH_SEED, &element_hash_val);
        uint32_t bit_pos = element_hash_val % b;
        filter[bitmap_idx][bit_pos] = true;
    }
    else { // Case 2: cf >= Tau
        // std::cout << "check: before update sketch" << std::endl;
        sketch->update(key, element);
        // std::cout << "check: after update sketch" << std::endl;
    }
}


uint32_t Couper::query(const uint32_t key){

    uint32_t key_hash_val;
    // Hash the key with the chosen hash function
    MurmurHash3_x86_32(&key, KEY_BYTE_LEN, HASH_SEED, &key_hash_val);
    uint32_t bitmap_idx = key_hash_val % L1;

    // Count the number of 1s in the bitmap, i.e., check the collected coupons
    uint32_t cf = 0;
    for (uint32_t i = 0; i < b; i++) {
        if (filter[bitmap_idx][i]) {
            cf++;
        }
    }

    // Case 1: cf < Tau
    if (cf < tau) {
        // cf < tau < b
        return static_cast<uint32_t>(b * log(static_cast<double>(b) / (b - cf)));
    }
    else {
        return sketch->query(key) + static_cast<uint32_t>(b * log(static_cast<double>(b) / (b - cf)));
    }

}



void Couper::spreadEstimation(
        const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
        const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi){

    for (const auto& [key, element] : dataset) {
        update(key, element);
    }

    float total_are = 0.0f;
    uint32_t count = 0;

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




void Couper::throughput(const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
                                 const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi){

    auto start_update = std::chrono::high_resolution_clock::now();
    for (const auto& [key, element] : dataset) {
        update(key, element);
    }
    auto end_update = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> update_duration = end_update - start_update;
    double update_throughput_Mpps = (dataset.size() / 1e6) / update_duration.count();


    auto start_query = std::chrono::high_resolution_clock::now();
    for (const auto& [flow_label, ele_set] : true_cardi) {
        query(flow_label);
    }
    auto end_query = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> query_duration = end_query - start_query;
    double query_throughput_Mfps = (true_cardi.size() / 1e6) / query_duration.count();

    std::cout << "update Throughput: " << update_throughput_Mpps << " Mpps" << std::endl;
    std::cout << "Query Throughput: " << query_throughput_Mfps << " Mfps" << std::endl;
}



void Couper::SSDetection(
        const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
        const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi,
        const std::vector<uint32_t> thresholds) {

    // the process of traffic
    for (const auto& [key, element] : dataset) {
        update(key, element);
    }

    std::cout << "\nSuper Spreader Detection:\n";
    for (uint32_t threshold : thresholds) {

        std::unordered_map<uint32_t, uint32_t> ground_truth;
        std::unordered_map<uint32_t, uint32_t> detected_ss;
        for (const auto& [key, elements] : true_cardi) {
            if (elements.size() > threshold) {
                ground_truth[key] = elements.size();
            }

            uint32_t est = query(key);
            if (est > threshold){
                detected_ss[key] = est;
            }
        }

        int TP = 0;
        for (const auto& [key, estimated] : detected_ss) {
            if (ground_truth.find(key) != ground_truth.end()) {
                TP++;
            }
        }

        double precision = (detected_ss.size() > 0) ? (double)TP / detected_ss.size() : 0.0;
        double recall = (ground_truth.size() > 0) ? (double)TP / ground_truth.size() : 0.0;
        double f1_score = (precision + recall > 0) ? 2 * precision * recall / (precision + recall) : 0.0;
        std::cout << "Th: " << threshold << ", | PR: " << precision << ", CR: " << recall << ", F1: " << f1_score
                  << std::endl;
    }
}