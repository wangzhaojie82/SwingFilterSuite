
#ifndef COLDFILTER_H
#define COLDFILTER_H
#include "Sketch.h"

class ColdFilter : public Sketch {

public:
    int d; // num of hash per layer
    int bits[2]; // counter bits per layer
    uint32_t thres[2]; // threshold for layer
    uint32_t num_counters[2]; // num of counters per layer
    uint32_t** counters; // filter, array of int arrays
    Sketch* sketch;

    ColdFilter(float memory_kb, Sketch* sketch1);

    void update(const uint32_t packet_id, const uint32_t flow_label, uint32_t weight= 1);

    int report(const uint32_t flow_label);

};


#endif


