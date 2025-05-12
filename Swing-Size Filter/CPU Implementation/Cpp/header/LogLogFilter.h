

#ifndef LOGLOGFILTER_H
#define LOGLOGFILTER_H


#include "MurmurHash3.h"
#include "Sketch.h"

class LogLogFilter : public Sketch{
private:
    int m;
    int r;
    uint32_t f;
    int delta;
    double phi;
    Sketch* sketch;
    std::vector<int8_t> R;
    std::vector<int> seeds;

public:
    LogLogFilter(float memory_kb, Sketch* sketch1);

    int get_leftmost(uint32_t random_val);

    void update(const uint32_t packet_id, const uint32_t flow_label, uint32_t weight= 1);

    int report(const uint32_t flow_label);

};


#endif
