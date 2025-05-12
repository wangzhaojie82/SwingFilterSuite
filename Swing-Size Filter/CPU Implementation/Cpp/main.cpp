#include <iostream>
#include <chrono>
#include <sstream>
#include <fstream>
#include <cmath>
#include <string>
#include <vector>
#include <map>
#include "./header/LogLogFilter.h"
#include "./header/ColdFilter.h"
#include "header/CouponFilter.h"
#include "./header/CountMin.h"
#include "./header/SwingFilter.h"


using namespace std;

vector<pair<uint32_t, uint32_t>> readDataSet(const std::vector<std::string> file_paths) {
    // load ip trace
    vector<pair<uint32_t, uint32_t>> data;
    for (const auto& file_path : file_paths) {
        ifstream file(file_path);
        if (!file.is_open()) {
            cerr << "Failed to open file: " << file_path << endl;
        }

        uint32_t total_packets = 0;
        std::string line;
        while (getline(file, line)) {
            std::istringstream iss(line);
            std::string source_ip, dest_ip;
            iss >> source_ip >> dest_ip;

            if (source_ip.empty()) {
                continue;
            }
            std::stringstream ss1(source_ip);
            uint32_t src_ip_int = 0;
            int part;
            for (int i = 0; i < 4; i++) {
                ss1 >> part;
                src_ip_int = (src_ip_int << 8) | part;
                if (ss1.peek() == '.') ss1.ignore();
            }
            // Fill data pair and add to vector
            data.push_back(make_pair(total_packets, src_ip_int));
            total_packets++;
        }
    }
    std::cout<< "Data is loaded. Total num: " << data.size() << std::endl;
    return data;
}


void flow_size_estimation(Sketch* sketch, vector<pair<uint32_t, uint32_t>>& dataset){

    std::map<uint32_t, uint32_t> real_flows;
    for (const auto& data : dataset) {
        real_flows[data.second]++;
    }

    float total_are = 0.0f;
    uint32_t count = 0;

    for (const auto& [key, size] : real_flows) {
        int estimated_size = sketch->report(key);

        float are = std::abs(static_cast<float>(estimated_size) - static_cast<float>(size)) / static_cast<float>(size);
        total_are += are;
        ++count;
    }

    float avg_are = total_are / count;
    std::cout << "ARE: " << avg_are << std::endl;
}



void process(Sketch* sketch, const std::vector<std::string> file_paths){
    /*
     * process the dataset on path: ip_trace
     */

    vector<pair<uint32_t, uint32_t>> dataset = readDataSet(file_paths);

    auto start_time = chrono::steady_clock::now();
    for (const auto& data : dataset) {
        sketch->update(data.first, data.second,1);
    }
    auto end_time = chrono::steady_clock::now();

    auto elapsed_time = chrono::duration_cast<chrono::seconds>(end_time - start_time).count();
    double throughput_mpps = static_cast<double>(dataset.size()) / elapsed_time / 1000000.0;
    cout << "Update Throughput: " << throughput_mpps << " Mpps" << endl;

    auto start_time_query = chrono::steady_clock::now();
    for (const auto& data : dataset) {
        sketch->report(data.second);
    }
    auto end_time_query = chrono::steady_clock::now();

    auto elapsed_time_query = chrono::duration_cast<chrono::seconds>(end_time_query - start_time_query).count();
    double throughput_mpps_query = static_cast<double>(dataset.size()) / elapsed_time_query / 1000000.0;
    cout << "Query Throughput: " << throughput_mpps_query << " Mpps" << endl;

    flow_size_estimation(sketch, dataset);
}


int main() {

    std::vector<std::string> file_paths = {
            "your dataset file path"
    };


    cout << "Hello! Program starts executing......" << endl;
    cout << "-------------------------------\n" << endl;

    float total_memory_kb = 500;
    cout << "Process: memory_kb="<< total_memory_kb << "KB | " << endl;
    float filter_memory_kb = total_memory_kb * 0.33;

    CountMin CM = CountMin(total_memory_kb - filter_memory_kb);
    SwingFilter SSF = SwingFilter(filter_memory_kb, &CM);

    // LogLogFilter LLF = LogLogFilter(filter_memory_kb, &CM);
    // ColdFilter CF = ColdFilter(filter_memory_kb, &CM);
    // CouponFilter coupon = CouponFilter(filter_memory_kb, &CM);

    process(&SSF,file_paths);

    return 0;

}
