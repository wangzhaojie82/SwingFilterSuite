#include "../headers/LogLogFilter.h"

LogLogFilter::LogLogFilter(float memory_kb, Sketch* sketch1){

    m = int(memory_kb * 1024 * 8); // 4  # number of registers
    r = 3; // number of hash
    f = 0;
    delta = 10; // the threshold, 10 is recommended in that paper
    phi = 0.77351;
    R.resize(m, 0);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 2147483647);
    for (int i = 0; i < r; ++i) {
        seeds.push_back(dis(gen));
    }
    sketch = sketch1;
}

int LogLogFilter::get_leftmost(uint32_t random_val){
    int left_most = 0;
    while (random_val) {
        left_most += 1;
        random_val >>= 1;
    }
    return 32 - left_most;

}

void LogLogFilter::update(const int packet_id, uint32_t flow_label, uint32_t weight){
    uint32_t hash_value = 0;
    uint32_t gamma = 0xffffffff;
    char hash_input_str[5] = {0};
    memcpy(hash_input_str, &flow_label, sizeof(uint32_t));
    for (int i = 0; i < r; ++i) {

        MurmurHash3_x86_32(hash_input_str, KEY_LEN, seeds[i], &hash_value);
        int idx = hash_value % m;

        gamma = std::min(static_cast<uint32_t>(R[idx]), gamma);
    }
    if (gamma < delta) {
        f += 1;
        for (int i = 0; i < r; ++i) {
            MurmurHash3_x86_32(hash_input_str, KEY_LEN, seeds[i], &hash_value);
            int idx = hash_value % m;

            uint32_t random_val = std::rand();
            int leftmost = get_leftmost(random_val);
            R[idx] = std::max(std::min(leftmost, delta), static_cast<int>(R[idx]));
        }
    } else {
        sketch->update(packet_id, flow_label);
    }

}

int LogLogFilter::report(uint32_t flow_label){
    uint32_t hash_value = 0;
    double filter_est = 0.0;
    double reg_sum = 0.0;
    double sketch_est = 0.0;
    char hash_input_str[5] = {0};
    memcpy(hash_input_str, &flow_label, sizeof(uint32_t));
    uint32_t gamma = 0xffffffff;
    for (int i = 0; i < r; ++i) {
        MurmurHash3_x86_32(hash_input_str, KEY_LEN, seeds[i], &hash_value);
        int idx = hash_value % m;
        gamma = std::min(gamma, static_cast<uint32_t>(R[idx]));
        reg_sum += R[idx];
    }
    reg_sum = std::pow(2, reg_sum / r);
    filter_est = (m * r) / (m - r) * (1 / (r * phi) * reg_sum - f / m);
    if (gamma == delta) {
        sketch_est = sketch->report(flow_label);
    }
    return static_cast<int>(std::round(filter_est + sketch_est));

}