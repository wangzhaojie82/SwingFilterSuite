#include <algorithm>
#include <fstream>
#include "header/SwingFilterSpread.h"


SwingFilterSpread::SwingFilterSpread(float memory_kb, Sketch* skt): sketch(skt){
    layers = 2;
    d_hash_num = 3;
    numOfFlags = {2, 4};
    std::vector<float> memory_ratios = {0.5, 0.5};
    uint32_t memory_bits = static_cast<uint32_t>(std::round(memory_kb * 1024 * 8));
    bucketsPerLayer.resize(layers);
    filter.resize(layers);
    for (size_t i = 0; i < layers; ++i) {
        uint32_t memory_bits_layer = static_cast<uint32_t>(std::round(memory_bits * memory_ratios[i]));
        bucketsPerLayer[i] = memory_bits_layer / (numOfFlags[i] * 2);
        filter[i].resize(bucketsPerLayer[i], Bucket(numOfFlags[i]));
    }
}


int8_t SwingFilterSpread::hash_s(uint32_t key, uint32_t bkt_index) {
    uint32_t hash_value = key ^ bkt_index;
    return (hash_value & 1) ? 1 : -1;
}


void SwingFilterSpread::update(const uint32_t key, const uint32_t element) {
    uint32_t element_hash_t = 0;
    MurmurHash3_x86_32(&element, KEY_BYTE_LEN, 1378943173, &element_hash_t);
    uint32_t hash_func_idx = element_hash_t % d_hash_num;
    uint32_t key_hash_val;
    MurmurHash3_x86_32(&key, KEY_BYTE_LEN, HASH_SEED_ARR[hash_func_idx], &key_hash_val);
    for (int l = 0; l < layers; ++l) {
        uint32_t bkt_idx = key_hash_val % bucketsPerLayer[l];
        int op_ = hash_s(key, bkt_idx);
        uint32_t flag_idx = element % numOfFlags[l];
        auto& bucket = filter[l][bkt_idx];
        bucket.flags[flag_idx] = std::clamp(bucket.flags[flag_idx] + op_, -1, 1);
        int same_direction_count = 0;
        for (auto& flag : bucket.flags) {
            if (flag == op_) same_direction_count++;
        }
        if (same_direction_count * 2 <= numOfFlags[l]) {
            return;
        }
    }
    sketch->update(key, element);
}



uint32_t SwingFilterSpread::query(const uint32_t key) {
    uint32_t spread_es = 0;
    for (int l = 0; l < layers; ++l) {
        uint32_t curr_layer_esti = 0;
        uint32_t buckets_with_valid_flags = 0;
        for (int i = 0; i < d_hash_num; ++i) {
            uint32_t key_hash_val;
            MurmurHash3_x86_32(&key, KEY_BYTE_LEN, HASH_SEED_ARR[i], &key_hash_val);
            uint32_t bkt_idx = key_hash_val % bucketsPerLayer[l];
            int op_ = hash_s(key, bkt_idx);
            auto& bucket = filter[l][bkt_idx];
            uint32_t same_direction_count = 0;
            for (auto flag: bucket.flags) {
                if (flag == op_) {
                    same_direction_count++;
                }
            }
            if (same_direction_count * 2 > numOfFlags[l]) {
                ++buckets_with_valid_flags;
            }
            curr_layer_esti += same_direction_count;
        }
        spread_es += curr_layer_esti;
        if (buckets_with_valid_flags * 2 <= d_hash_num) {
            return spread_es;
        }
    }
    spread_es += sketch->query(key);
    return spread_es;
}


// Per-flow spread estimation
void SwingFilterSpread::spreadEstimation(
        const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
        const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi) {
    for (const auto& [key, element] : dataset) {
        update(key, element);
    }
    float total_are = 0.0f;
    uint32_t count = 0;
    for (const auto& [flow_label, ele_set] : true_cardi) {
        uint32_t true_value = ele_set.size();
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



void SwingFilterSpread::throughput(const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
                const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi){
    auto start_update = std::chrono::high_resolution_clock::now();
    // the process of traffic
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


void SwingFilterSpread::SSDetection(
        const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
        const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi,
        const std::vector<uint32_t> thresholds) {
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
            uint32_t esti_ = SSQues(key);
            if (esti_ > threshold){
                detected_ss[key] = esti_;
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


uint32_t SwingFilterSpread::SSQues(const uint32_t key) {
    uint32_t ans_t = sketch->query(key);
    uint32_t s_es = 0;
    for (int l = 0; l < layers; ++l) {
        uint32_t curr_layer_esti = 0;
        for (int i = 0; i < d_hash_num; ++i) {
            uint32_t key_hash_val;
            MurmurHash3_x86_32(&key, KEY_BYTE_LEN, HASH_SEED_ARR[i], &key_hash_val);
            uint32_t bkt_idx = key_hash_val % bucketsPerLayer[l];
            int op_ = hash_s(key, bkt_idx);
            auto& bucket = filter[l][bkt_idx];
            uint32_t same_direction_count = 0;
            for (auto flag: bucket.flags) {
                if (flag == op_) {
                    same_direction_count++;
                }
            }
            curr_layer_esti += same_direction_count;
        }
        s_es += curr_layer_esti;
    }
    if (ans_t != 0)
        ans_t += s_es;
    else
        ans_t = s_es;
    return ans_t;
}