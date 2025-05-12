#ifndef BOUNCEFILTER_H
#define BOUNCEFILTER_H


#include "MurmurHash3.h"
#include "Sketch.h"

class SwingFilter : public Sketch{
private:
    int d;
    int bits[2];
    int max_positive[2];
    int min_negative[2];
    uint32_t num_counters[2];
    int** counters;
    Sketch* skt1;


public:
    SwingFilter(float memory_kb, Sketch* sketch1);

    int hash_s(const uint32_t flow_label, uint32_t& counter_index);

    void update(const uint32_t packet_id, const uint32_t flow_label, uint32_t weight= 1);

    int report(const uint32_t flow_label);

    ~SwingFilter() {
        delete[] counters[0];
        delete[] counters[1];
    }

};

#endif
