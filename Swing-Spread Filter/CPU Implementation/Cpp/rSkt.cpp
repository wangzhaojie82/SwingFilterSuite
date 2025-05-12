#include "header/rSkt.h"
#include <iostream>
#include <fstream>

rSkt::rSkt(uint32_t memory_kb) {
    uint32_t memory_bits = memory_kb * 1024 * 8;
    this->w = memory_bits / (5 * 32);
    this->m = 32;
    this->C = new uint32_t *[w];
    this->C1 = new uint32_t *[w];
    for (int i = 0; i < w; ++i) {
        C[i] = new uint32_t[m] {0};
        C1[i] = new uint32_t[m] {0};
    }
    keyseed = 41213;
    eleseed = 12412;
    num_leading_zeros = floor(log10(double(m)) / log10(2.0)); // used to locate
    if (m == 16) {
        alpha = 0.673;
    } else if (m == 32) {
        alpha = 0.697;
    } else if (m == 64) {
        alpha = 0.709;
    } else {
        alpha = (0.7213 / (1 + (1.079 / m)));
    }
}


void rSkt::update(uint32_t flo, uint32_t elo) {
    uint64_t key = flo;
    uint64_t ele = elo;
    uint32_t hashValue, hashIndex, hashValue2;
    uint32_t g_f_i;
    MurmurHash3_x86_32(&key, 8, keyseed, &hashValue);
    hashIndex = hashValue % w;
    MurmurHash3_x86_32(&ele, 8, eleseed, &hashValue2);
    uint32_t p_part = hashValue2 >> (sizeof(uint32_t) * 8 - num_leading_zeros);
    uint32_t q_part = hashValue2 - (p_part << (sizeof(uint32_t) * 8 - num_leading_zeros));
    uint32_t left_most = 0;
    while(q_part) {
        left_most += 1;
        q_part = q_part >> 1;
    }
    left_most = sizeof(uint32_t) * 8 - num_leading_zeros - left_most + 1;
    MurmurHash3_x86_32(&key, 8, p_part, &hashValue);
    g_f_i = hashValue % 2;
    if (g_f_i == 0) {
        C[hashIndex][p_part] = MAX(left_most, C[hashIndex][p_part]);
    } else {
        C1[hashIndex][p_part] = MAX(left_most, C1[hashIndex][p_part]);
    }
}



int rSkt::queryReg(uint32_t * Lf, uint32_t * Lf1) {
    double sum_register_Lf = 0;
    double sum_register_Lf1 = 0;
    double zero_ratio_Lf = 0, zero_ratio_Lf1 = 0;
    for (int i = 0; i < m; ++i) {
        sum_register_Lf += pow(2.0, -double(Lf[i]));
        if(Lf[i] == 0)
            zero_ratio_Lf += 1;
        sum_register_Lf1 += pow(2.0, -double(Lf1[i]));
        if (Lf1[i] == 0)
            zero_ratio_Lf1 += 1;
    }
    zero_ratio_Lf = zero_ratio_Lf1 / m;
    zero_ratio_Lf1 = zero_ratio_Lf1 / m;
    double n = alpha * pow(double(m), 2) / sum_register_Lf;
    double n_ = alpha * pow(double(m), 2) / sum_register_Lf1;
    if(n <= 2.5 * m) {
        if(zero_ratio_Lf != 0) {
            n = - double(m) * log(zero_ratio_Lf);
        }
    }
    else if(n > pow(2.0, 32) / 30) {
        n = - pow(2.0, 32) * log(1 - n / pow(2.0, 32));
    }

    if(n_ <= 2.5 * m) {
        if(zero_ratio_Lf1 != 0) {
            n_ = - double(m) * log(zero_ratio_Lf1);
        }
    }
    else if(n_ > pow(2.0, 32) / 30) {
        n_ = - pow(2.0, 32) * log(1 - n_ / pow(2.0, 32));
    }
    return MAX(abs(n - n_), 1);
}



uint32_t rSkt::query(uint32_t flo) {
    uint64_t key = flo;
    uint32_t hashValue, hashIndex, g_f_i, g_f_i_hashValue;
    uint32_t * Lf, *Lf1;
    Lf = new uint32_t[m]{0};
    Lf1 = new uint32_t[m]{0};
    MurmurHash3_x86_32(&key, 8, keyseed, &hashValue);
    hashIndex = hashValue % w;
    for (int i = 0; i < m; ++i) {
        MurmurHash3_x86_32(&key, 8, i, &g_f_i_hashValue);
        g_f_i = g_f_i_hashValue % 2;
        if (g_f_i == 0) {
            Lf[i] = C[hashIndex][i];
            Lf1[i] = C1[hashIndex][i];
        } else {
            Lf[i] = C1[hashIndex][i];
            Lf1[i] = C[hashIndex][i];
        }
    }

    int val_e = this->queryReg(Lf, Lf1);
    if (val_e > 0)
        return static_cast<uint32_t>(val_e);
    return 1;
}


void rSkt::SSDetection(
        const std::vector<std::pair<uint32_t, uint32_t>> &dataset,
        const std::unordered_map<uint32_t, std::unordered_set<uint32_t>> &true_cardi,
        const std::vector<uint32_t> thresholds) {

    // the process of traffic
    for (const auto &[key, element]: dataset) {
        update(key, element);
    }

    std::cout << "\nSuper Spreader Detection:\n";
    for (auto th_: thresholds) {

        std::unordered_map<uint32_t, uint32_t> ground_truth;
        std::unordered_map<uint32_t, uint32_t> detected_ss;
        for (const auto &[key, elements]: true_cardi) {
            if (elements.size() > th_) {
                ground_truth[key] = elements.size();
            }

            int esti_ = query(key);
            if (esti_ > th_) {
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
        std::cout << "Th: " << th_ << ", | PR: " << precision << ", CR: " << recall << ", F1: " << f1_score
                  << std::endl;
    }

}