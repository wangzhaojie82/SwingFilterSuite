#ifndef SWINGFILTERPLUS_H
#define SWINGFILTERPLUS_H

#include "Sketch.h"

struct Bucket {
    std::vector<int> flags; // a flag array, each flag has 3 state: {-1, 0, 1}
    Bucket(size_t numFlags) : flags(numFlags, 0) {}
};


class SwingFilterSpread : public Sketch{
private:
    std::vector<std::vector<Bucket>> filter;
    size_t layers;

    size_t d_hash_num;
    // array of params for each layer
    std::vector<size_t> bucketsPerLayer;
    std::vector<size_t> numOfFlags;
    Sketch* sketch;

public:


    SwingFilterSpread(float memory_kb, Sketch* skt);

    ~SwingFilterSpread() {

    }

    int8_t hash_s(const uint32_t key, uint32_t bkt_index);

    void update(const uint32_t key, const uint32_t element);
    uint32_t query(const uint32_t key);

    void spreadEstimation(
            const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
            const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi);

    uint32_t SSQues(const uint32_t key);

    void SSDetection(
            const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
            const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi,
            const std::vector<uint32_t> thresholds);

    void throughput(const std::vector<std::pair<uint32_t, uint32_t>>& dataset,
                    const std::unordered_map<uint32_t, std::unordered_set<uint32_t>>& true_cardi);

};

#endif
