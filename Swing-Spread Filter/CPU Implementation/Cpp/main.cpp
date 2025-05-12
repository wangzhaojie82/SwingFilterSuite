#include "header/Sketch.h"
#include "header/SwingFilterSpread.h"
#include "header/vHLL.h"
#include "header/rSkt.h"
#include "header/CouponFilter.h"
#include "header/Couper.h"
#include "header/CSE.h"
#include "header/KjSkt.h"
#include "header/SuperKjSkt.h"
#include "header/LogLogFilter_Spread.h"
#include <iostream>
#include <vector>
#include <cstdint>
#include <fstream>
#include <sstream>
#include <chrono>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <utility>
#include <iomanip>
#include <map>
#include <set>


// load dataset and get true per-flow spread,
// auto [dataset, true_cardinality] = loadDataSet();
// first is dataset, second is related spread/cardinality statistics
std::pair<std::vector<std::pair<uint32_t, uint32_t>>,
        std::unordered_map<uint32_t, std::unordered_set<uint32_t>>> loadDataSet() {
    std::vector<std::string> file_paths = {
            "your dataset file path"
    };

    std::vector<std::pair<uint32_t, uint32_t>> data;
    std::unordered_map<uint32_t, std::unordered_set<uint32_t>> true_cardinality;
    uint64_t total_data_num = 0;

    for (const auto &file_path: file_paths) {
        std::ifstream file(file_path);
        if (!file.is_open()) {
            std::cerr << "Failed to open file: " << file_path << std::endl;
            continue;
        }

        std::string line;
        while (getline(file, line)) {
            std::istringstream iss(line);
            std::string source_ip, dest_ip;
            iss >> source_ip >> dest_ip;

            if (source_ip.empty() || dest_ip.empty()) {
                continue;
            }

            std::stringstream ss1(source_ip), ss2(dest_ip);
            uint32_t src_ip_int = 0, dst_ip_int = 0;
            int part;

            for (int i = 0; i < 4; i++) {
                ss1 >> part;
                src_ip_int = (src_ip_int << 8) | part;
                if (ss1.peek() == '.') ss1.ignore();

                ss2 >> part;
                dst_ip_int = (dst_ip_int << 8) | part;
                if (ss2.peek() == '.') ss2.ignore();
            }

            data.emplace_back(src_ip_int, dst_ip_int);
            true_cardinality[src_ip_int].insert(dst_ip_int);
            total_data_num++;
        }

        std::cout << file_path << " is loaded." << std::endl;
    }

    std::cout << "\n" << file_paths.size() << " minutes data loaded.\n"
              << "Totaling packets: " << total_data_num
              << ", Totaling unique flows: " << true_cardinality.size() << std::endl;
    return {data, true_cardinality};
}


void flowSizeDistribution(const std::vector<std::pair<uint32_t, uint32_t>> &dataset) {
    std::vector<std::pair<int, int>> intervals = {
            {1,     100},
            {100,   500},
            {500,   1000},
            {1000,  5000},
            {5000,  10000},
            {10000, 0x7fffffff}
    };
    std::vector<int> distribution(intervals.size(), 0);
    std::map<uint32_t, uint32_t> flow_size;
    for (const auto &[key, _]: dataset) {
        flow_size[key]++;
    }
    for (const auto &[key, size]: flow_size) {
        for (size_t i = 0; i < intervals.size(); ++i) {
            if (size >= intervals[i].first && size < intervals[i].second) {
                distribution[i]++;
                break;
            }
        }
    }
    int total_flows = flow_size.size();

    std::cout << "Flow Size Distribution:\n";
    std::cout << std::setw(15) << "Interval" << std::setw(15) << "Count" << std::setw(15) << "Percentage\n";
    for (size_t i = 0; i < intervals.size(); ++i) {
        double percentage = static_cast<double>(distribution[i]) / total_flows * 100.0;
        std::cout << std::setw(5) << "[" << intervals[i].first
                  << "," << (intervals[i].second == INT_MAX ? "+" : std::to_string(intervals[i].second)) << ")"
                  << std::setw(15) << distribution[i]
                  << std::setw(15) << std::fixed << std::setprecision(3) << percentage << "%\n";
    }
    std::cout << "\n";
}


void cardinalityDistribution(const std::vector<std::pair<uint32_t, uint32_t>> &dataset) {
    std::vector<std::pair<int, int>> intervals = {
            {1,   10},
            {10,  50},
            {50,  100},
            {100, 500},
            {500, 1000},
            {1000, INT_MAX}
    };
    std::vector<int> distribution(intervals.size(), 0);
    std::map<uint32_t, std::set<uint32_t>> flow_map;
    for (const auto &[key, element]: dataset) {
        flow_map[key].insert(element);
    }

    size_t unique_pairs_count = 0;
    uint32_t max_flow = 0;
    uint32_t max_spread = 0;

    for (const auto &[key, elements]: flow_map) {
        int cardinality = elements.size();
        unique_pairs_count += cardinality;
        if (cardinality > max_spread) {
            max_flow = key;
            max_spread = cardinality;
        }
        for (size_t i = 0; i < intervals.size(); ++i) {
            if (cardinality >= intervals[i].first && cardinality < intervals[i].second) {
                distribution[i]++;
                break;
            }
        }
    }
    std::cout << "Cardinality Distribution for dataset:\n";
    std::cout << std::setw(15) << "Interval" << std::setw(15) << "Count" << std::setw(15) << "Percentage\n";
    int total_flows = flow_map.size();
    for (size_t i = 0; i < intervals.size(); ++i) {
        double percentage = static_cast<double>(distribution[i]) / total_flows * 100.0;
        std::cout << std::setw(5) << "[" << intervals[i].first
                  << "," << (intervals[i].second == INT_MAX ? "+" : std::to_string(intervals[i].second)) << ")"
                  << std::setw(15) << distribution[i]
                  << std::setw(15) << std::fixed << std::setprecision(3) << percentage << "%\n";
    }
    std::cout << "\nTotal unique <key, element> pairs: " << unique_pairs_count << "\n";
    std::cout << max_flow << "  has the max spread: " << max_spread << "\n";
}


int main() {

    std::cout << "Hello! Experiment starts ..." << std::endl;
    auto start_time = std::chrono::steady_clock::now();
    auto [dataset, true_cardinality] = loadDataSet();
    double fil_me_frac = 0.33;
    std::vector<uint32_t> thresholds = {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000};

    std::vector<uint32_t> memo_kb_values = {100, 200, 300, 400};
    for (uint32_t memo_kb: memo_kb_values) {

        std::cout << "\n-------------------------------\n"
                     "Memory: " << memo_kb << std::endl;

        uint32_t filter_memo = static_cast<uint32_t>(memo_kb * fil_me_frac);
        uint32_t sketch_memo = memo_kb - filter_memo;


        std::cout << "\n" << "Only vHLL: " << std::endl;
        vHLL *sketch_only = new vHLL(memo_kb);
        sketch_only->spreadEstimation(dataset, true_cardinality);
        delete sketch_only;


        std::cout << "\n" << "Swing-Spread Filter + vHLL: " << std::endl;
        vHLL *skt_swing = new vHLL(sketch_memo);
        SwingFilterSpread *swingFilter = new SwingFilterSpread(filter_memo, skt_swing);
        swingFilter->spreadEstimation(dataset, true_cardinality);
        delete swingFilter;
        delete skt_swing;

    }

    auto end_time = std::chrono::steady_clock::now();
    auto elapsed_time = std::chrono::duration_cast<std::chrono::seconds>(end_time - start_time).count();
    std::cout << "\nExperiment ends. Elapsed time: "
              << elapsed_time / 3600 << "h " << (elapsed_time % 3600) / 60 << "m " << elapsed_time % 60 << "s"
              << std::endl;

    return 0;
}

