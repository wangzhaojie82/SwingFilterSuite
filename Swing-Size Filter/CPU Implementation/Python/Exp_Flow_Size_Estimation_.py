import concurrent.futures
import time
import re
import Packet
from filters import SwingFilter, ASketch, CouponFilter
from sketches import CountMin, ElasticSketch

def cal_are(real_flows, estimated_flow):
    # To calculate ARE

    total_flows = 0
    total_relative_error = 0

    for flow, size in real_flows.items():
        estimated_size = estimated_flow[flow]
        if size > 0:
            relative_error = abs(size - estimated_size) / size
            total_relative_error += relative_error
            total_flows += 1

    ARE = round(total_relative_error / total_flows, 3)
    return ARE



def exp_flow_size_es(**kwargs):
    '''
    Experiment for flow size estimation
    '''

    # path of dataset
    traffic_traces = kwargs['traffic_traces']
    memory_kb = kwargs['memory_kb']
    memory_kb_Filter = round(memory_kb * 0.33)
    memory_kb_Sketch = memory_kb - memory_kb_Filter

    # Initialize a filter and measurement sketch, e.g., CountMin, by given memories
    filter = SwingFilter.init_SwingFilter(memory_kb_Filter)
    sketch = CountMin.init_CountMin(memory_kb_Sketch)

    all_flows = {}
    total_packets = 0  # total number of all packets

    # regular expression to match valid IPv4 address
    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    for traffic_trace in traffic_traces:
        with open(traffic_trace, 'r', encoding='utf-8') as f:
            for line in f:
                tmp = line.split()
                # filter the invalid IPv4 packets
                if not re.match(pattern, tmp[0]) or not re.match(pattern, tmp[1]):
                    continue

                packet = Packet.Packet(total_packets, tmp[0], tmp[1])

                # to record all flows processed
                total_packets += 1
                if packet.flow_label in all_flows.keys():
                    all_flows[packet.flow_label] += 1
                else:
                    all_flows[packet.flow_label] = 1

                succ = filter.update(packet)
                if succ:
                    continue
                else:
                    sketch.update(packet)


    estimated_flows = {}
    for flow_label in all_flows.keys():
        size_in_filter, large_flow_flag = filter.report(flow_label)
        if large_flow_flag:
            size_in_sketch = sketch.report(flow_label)
            estimated_flows[flow_label] = size_in_filter + size_in_sketch
        else:
            estimated_flows[flow_label] = size_in_filter

    ARE = cal_are(all_flows, estimated_flows)

    print(f"Memory = {memory_kb} |  ARE = {ARE}")


def AS_improve(**kwargs):

    # path of traffic trace
    traffic_traces = kwargs['traffic_traces']

    memory_kb = kwargs['memory_kb']

    # filter size is 0.4 KB as the authors did
    AS = ASketch.init_ASketch(0.4)

    skt = CountMin.init_CountMin(memory_kb - 0.4)
    # skt = SwingFilter.init_SwingFilter(memory_kb - 0.4)


    all_flows = {}
    total_packets = 0  # total number of all packets

    # regular expression to match IPv4 address
    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    for traffic_trace in traffic_traces:
        with open(traffic_trace, 'r', encoding='utf-8') as f:
            for line in f:
                tmp = line.split()
                # filter the invalid IPv4 packets or IPv6 packets
                if not re.match(pattern, tmp[0]) or not re.match(pattern, tmp[1]):
                    continue

                packet = Packet.Packet(total_packets, tmp[0], tmp[1])

                # to count all packets processed
                total_packets += 1
                if packet.flow_label in all_flows.keys():
                    all_flows[packet.flow_label] += 1
                else:
                    all_flows[packet.flow_label] = 1

                succ = AS.update(packet)
                if succ:
                    continue
                else:
                    skt.update(packet)

                    # Check if swapping is needed

                    # Find the item in filter with the minimum new_count
                    # min_item_label: the flow label of item with the minimum new_count
                    # min_item_info: a tuple (new_count, old_count) of this item
                    min_item_label, min_item_info = min(AS.filter.items(), key=lambda x: x[1][0])

                    estimated_size = skt.report(packet.flow_label)

                    if estimated_size > min_item_info[0]:

                        # Update the sketch with packets from the minimum item
                        num_to_update = round(min_item_info[0] - min_item_info[1])
                        for _ in range(num_to_update):
                            packet_tmp = Packet.Packet(0, min_item_label, min_item_label)
                            skt.update(packet_tmp)

                        # Delete the minimum item
                        del AS.filter[min_item_label]

                        # Add the new item with the updated flow_label and size
                        AS.filter[packet.flow_label] = (estimated_size, estimated_size)

    estimated_flows = {}
    for flow_label in all_flows.keys():
        size_in_AS = AS.report(flow_label)
        if size_in_AS < 0:
            size_in_skt = skt.report(flow_label)
            estimated_flows[flow_label] = size_in_skt
        else:
            estimated_flows[flow_label] = size_in_AS

    ARE = cal_are(all_flows, estimated_flows)
    print(f"Memory = {memory_kb} |  ARE = {ARE}")


def ES_improve(**kwargs):

    traffic_traces = kwargs['traffic_traces']
    memory_kb = kwargs['memory_kb']

    Elastic = ElasticSketch.init_ElasticSketch(memory_kb)

    all_flows = {}
    total_packets = 0  # total number of all packets
    # regular expression to match IPv4 address
    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    for traffic_trace in traffic_traces:
        with open(traffic_trace, 'r', encoding='utf-8') as f:
            for line in f:
                tmp = line.split(',')
                # filter the invalid IPv4 packets or IPv6 packets
                if not re.match(pattern, tmp[0]) or not re.match(pattern, tmp[1]):
                    continue

                packet = Packet.Packet(total_packets, tmp[0], tmp[1])

                # to count all packets processed
                total_packets += 1
                if packet.flow_label in all_flows.keys():
                    all_flows[packet.flow_label] += 1
                else:
                    all_flows[packet.flow_label] = 1

                Elastic.update(packet)

    estimated_flows = {}
    for flow_label in all_flows.keys():
        size_in_Elastic = Elastic.report(flow_label)
        estimated_flows[flow_label] = size_in_Elastic

    ARE = cal_are(all_flows, estimated_flows)
    print(f"Memory = {memory_kb} |  ARE = {ARE}")




def run_method(method, **kwargs):
    method(**kwargs)



def run_parallel():

    traffic_traces = [r'your dataset file path']

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []

        # memory in KB
        for memory_kb in [100, 200]:

            futures.append(
                executor.submit(run_method, exp_flow_size_es,
                                traffic_traces=traffic_traces,
                                memory_kb=memory_kb))

        concurrent.futures.wait(futures)



if __name__ == '__main__':

    print("Program execution start.")
    start_time = time.time()

    run_parallel()

    end_time = time.time()
    execution_time = end_time - start_time
    formatted_time = time.strftime('%H:%M:%S', time.gmtime(execution_time))

    print(f"\nTotal execution time is: {formatted_time}")