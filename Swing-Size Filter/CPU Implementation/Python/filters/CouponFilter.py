import mmh3
import random
import math
import concurrent.futures
import re
import Packet
import utils

from sketches import CountSketch, CountMin, CUSketch, CounterSumEstimation, ElasticSketch, MVSketch, WavingSketch, PyramidSketch



class CouponFilter:
    def __init__(self, m, l, p):
        self.m = m
        self.l = l
        self.p = p
        self.R = [[0] * l for _ in range(m)]
        self.tau = 8

    def update(self, packet):
        idx = mmh3.hash(packet.flow_label) % self.m
        B = self.R[idx]
        r = random.random()
        c = max(0, math.ceil(self.l - r / self.p))
        if c == 0:
            return True

        if c - 1 < self.l:
            B[c - 1] = 1

        if all(B):
            return False
        else:
            return True


    def update_with_weight(self, flow_label, weight):
        for i in range(weight):
            idx = mmh3.hash(flow_label) % self.m
            B = self.R[idx]
            r = random.random()
            c = max(0, math.ceil(self.l - r / self.p))
            if c == 0:
                return True

            if c - 1 < self.l:
                B[c - 1] = 1


    def report(self, flow_label):
        idx = mmh3.hash(flow_label) % self.m
        B = self.R[idx]
        num_ones = sum(B)
        return num_ones / self.p, True


def init_CouponFilter(memory_kb):
    l = 8
    memory_bits = memory_kb * 1024 * 8
    m = round(memory_bits / l)
    p = 0.1
    filter = CouponFilter(m,l,p)
    return filter




def size_estimation(**kwargs):

    # path of traffic trace
    traffic_traces = kwargs['traffic_traces']
    memory_kb_Filter = kwargs['memory_kb_Filter']
    memory_kb_Sketch = kwargs['memory_kb_Sketch']

    filter = init_CouponFilter(memory_kb_Filter)

    # sketch = CountMin.init_CountMin(memory_kb_Sketch)
    sketch = PyramidSketch.init_PyramidSketch(memory_kb_Sketch)

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

                succ = filter.update(packet)
                if succ:
                    continue
                else:
                    sketch.update(packet)

    estimated_flows = {}
    for flow_label in all_flows.keys():
        # derived from the authors' source code at https://github.com/duyang92/coupon-filter-paper/blob/master
        ans_t  = sketch.report(flow_label)
        if ans_t != 0:
            ans_t += filter.tau
        else:
            ans_t = 1

        estimated_flows[flow_label] = ans_t

    are = utils.calculate_are(all_flows, estimated_flows)

    print(f'Size estimate with Coupon! Memory = {memory_kb_Filter + memory_kb_Sketch}, ARE = {are}')



def run_method(method, **kwargs):
    method(**kwargs)


def run_parallel():
    traffic_traces = [r'data set file path']
    print(f'Traffic Traces: {traffic_traces}\n')

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        # memory in KB
        for memory_kb in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:

            memory_kb_Filter = round(memory_kb * 0.33)
            memory_kb_Sketch = memory_kb - memory_kb_Filter

            futures.append(
                    executor.submit(run_method, size_estimation, traffic_traces=traffic_traces,
                                 memory_kb_Filter=memory_kb_Filter, memory_kb_Sketch=memory_kb_Sketch))

        concurrent.futures.wait(futures)


if __name__ == '__main__':

    run_parallel()