import concurrent.futures
import time
import re
import Packet

from filters import SwingFilter
from sketches import MVSketch


def calculate_metrics(heavy_hitter_threshold, heavy_hitters, all_flows):

    true_heavy_hitters = set()
    for flow_label, true_size in all_flows.items():
        if true_size > heavy_hitter_threshold:
            true_heavy_hitters.add(flow_label)
    true_positives = 0
    total_relative_error = 0
    num_are = 0
    for flowlabel, estimated_size in heavy_hitters:
        # the reported flow exists
        if flowlabel in all_flows.keys():
            true_size = all_flows[flowlabel]

            if true_size > 0:
                relative_error = abs(estimated_size - true_size) / true_size
                total_relative_error += relative_error
                num_are += 1

        if flowlabel in true_heavy_hitters:
            true_positives += 1

    average_relative_error, precision, recall, f1 = 0, 0, 0, 0

    # Calculate average relative error
    average_relative_error = round(total_relative_error / num_are, 3)

    if len(heavy_hitters) > 0:
        precision = round(true_positives / len(heavy_hitters), 3)
    if len(true_heavy_hitters) > 0:
        recall = round(true_positives / len(true_heavy_hitters), 3)

    # Calculate F1 score
    if precision + recall > 0:
        f1 = round(2 * (precision * recall) / (precision + recall), 3)

    return average_relative_error, f1


def heavy_hitter_d(**kwargs):

    traffic_traces = kwargs['traffic_traces']
    memory_kb = kwargs['memory']
    filter_ = SwingFilter.init_SwingFilter(memory_kb * 0.2)
    sketch_ = MVSketch.init_MVSketch(memory_kb * 0.8)
    all_flows = {}
    total_packets = 0
    # regular expression to match IPv4 address
    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    for traffic_trace in traffic_traces:
        with open(traffic_trace, 'r', encoding='utf-8') as f:
            for line in f:
                tmp = line.split()
                # filter the invalid IPv4 packets
                if not re.match(pattern, tmp[0]) or not re.match(pattern, tmp[1]):
                    continue

                packet = Packet.Packet(total_packets, tmp[0], tmp[1])

                # to count all packets processed
                total_packets += 1
                if packet.flow_label in all_flows.keys():
                    all_flows[packet.flow_label] += 1
                else:
                    all_flows[packet.flow_label] = 1

                succ = filter_.update(packet)
                if succ:
                    continue
                else:
                    sketch_.update(packet)


    heavy_hitter_threshold = kwargs['heavy_hitter_threshold']

    filename = f'HHD_Memory={memory_kb}_heavy_hitter_detection.txt'

    with open(filename, 'w') as file:
        for threshold in heavy_hitter_threshold:

            heavy_hitters = sketch_.heavy_hitter_query_with_filter(filter_, threshold)

            ARE, F1 = calculate_metrics(threshold, heavy_hitters, all_flows)
            file.write(f"HH threshold = {threshold}  |  ARE = {ARE}  |  F1 = {F1} \n")
            file.write(f"\n")


def run_method(method, **kwargs):
    method(**kwargs)


def run_parallel():

    traffic_traces = ['./data/your_dataset.txt']

    heavy_hitter_threshold = [1000, 2000, 4000, 6000, 8000, 10000]

    with concurrent.futures.ProcessPoolExecutor() as executor:

        futures = []
        for memory in [80]:

            futures.append(
                executor.submit(run_method, heavy_hitter_d, traffic_traces=traffic_traces,
                                heavy_hitter_threshold=heavy_hitter_threshold,
                                memory=memory))

        concurrent.futures.wait(futures)



if __name__ == '__main__':

    print("Program execution started.")
    start_time = time.time()

    run_parallel()

    end_time = time.time()
    execution_time = end_time - start_time
    formatted_time = time.strftime('%H:%M:%S', time.gmtime(execution_time))

    print(f"\nTotal execution time is: {formatted_time}")