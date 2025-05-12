#include <iostream>
#include <chrono>
#include <sstream>
#include <fstream>
#include <string>
#include <vector>
#include <set>
#include "../headers/CountMin.h"
#include "../headers/ColdFilter.h"
#define PACKET_SIZE 16
using namespace std;
uint32_t convertIPv4ToUint32(char* ipAddress) {
    uint32_t result = 0;
    int octet = 0;
    char ipCopy[PACKET_SIZE];
    strncpy(ipCopy, ipAddress, sizeof(ipCopy) - 1);
    ipCopy[sizeof(ipCopy) - 1] = '\0';
    char* token = strtok(ipCopy, ".");
    while (token != nullptr) {
        octet = std::stoi(token);
        result = (result << 8) + octet;
        token = std::strtok(nullptr, ".");
    }
    return result;
}

vector<pair<int, uint32_t>> readDataSet(const string& file_path) {
    // load ip trace
    vector<pair<int, uint32_t>> data;
    uint32_t src;
    ifstream file(file_path);
    if (!file.is_open()) {
        cerr << "Failed to open file: " << file_path << endl;
    }

    int total_packets = 0;
    string line;
    while (getline(file, line)) {
        istringstream iss(line.c_str());
        string source_ip, dest_ip;
        iss >> source_ip >> dest_ip;

        /*char* source_ip_fixed = new char[PACKET_SIZE]; // 1 less for null terminator
        strncpy(source_ip_fixed, source_ip.c_str(), PACKET_SIZE - 1); // -1 to reserve space for null terminator
        memset(source_ip_fixed + std::min(static_cast<int>(source_ip.length()), KEY_LEN - 1), '0', KEY_LEN - std::min(static_cast<int>(source_ip.length()), KEY_LEN - 1));
        source_ip_fixed[KEY_LEN - 1] = '\0'; // null terminator*/
        src = convertIPv4ToUint32((char*) source_ip.c_str());

        // Fill data pair and add to vector
        data.push_back(make_pair(total_packets, src));
        total_packets++;
    }

    return data;
}


void process(Sketch* sketch, const string& ip_trace){
    vector<pair<int, uint32_t>> dataset = readDataSet(ip_trace);
    clock_t start = clock();
    for (const auto& data : dataset) {
        sketch->update(data.first, data.second,1);
    }
    clock_t current = clock();
    cout << dataset.size() << " lines: have used " << ((double)current - start) / CLOCKS_PER_SEC << " seconds" << endl;
    double throughput_mpps = (dataset.size() / 1000000.0) / (((double)current - start) / CLOCKS_PER_SEC);
    cout << "Update Throughput: " << throughput_mpps << " Mpps" << endl;

    start = clock();
    for (const auto& data : dataset) {
        sketch->report(data.second);
    }
    current = clock();
    cout << dataset.size() << " lines: have used " << ((double)current - start) / CLOCKS_PER_SEC << " seconds" << endl;
    double throughput_mpps_query = (dataset.size() / 1000000.0) / (((double)current - start) / CLOCKS_PER_SEC);
    cout << "Query Throughput: " << throughput_mpps_query << " Mpps" << endl;
}

int main(int argc, char** argv) {
    string ip_trace = "data_path";
    float total_memory_kb;
    float filter_ratio;
    for (int i = 1; i < argc; i ++) {
        if(strcmp(argv[i], "-total_mem") == 0) {
           string str_temp = string(argv[i + 1]);
           total_memory_kb = atof(str_temp.c_str()); 
        } else if (strcmp(argv[i], "-mem_ratio") == 0) {
           string str_temp = string(argv[i + 1]);
           filter_ratio = atof(str_temp.c_str());
        }
    }
    cout << "Hello! Program starts executing......" << endl;
    cout << "-------------------------------\n" << endl;
    cout << "Process: memory_kb="<< total_memory_kb << "KB | " << endl;
    float filter_memory_kb = total_memory_kb * filter_ratio;
    CountMin CM = CountMin(total_memory_kb - filter_memory_kb);
    ColdFilter cf = ColdFilter(filter_memory_kb, &CM);
    process(&cf,ip_trace);
    cout << "-------------------------------\n" << endl;

    return 0;
}
