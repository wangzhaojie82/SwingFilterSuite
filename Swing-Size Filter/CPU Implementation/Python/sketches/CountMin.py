import mmh3
import numpy as np
import re
import os
import Packet

class CountMin:
    def __init__(self, width, depth, counter_bits=32):
        self.width = width
        self.depth = depth
        self.counter_bits = counter_bits # num bits for each counter
        self.num_counters = width * depth # total number of counters
        self.counters = np.zeros((depth, width), dtype=np.int32)

    def update(self, packet):
        flow_label = packet.flow_label
        for i in range(self.depth):
            index = mmh3.hash(flow_label, i) % self.width

            counter_limit = (1 << self.counter_bits) - 1
            if self.counters[i][index] < counter_limit:
                self.counters[i][index] += 1


    def update_with_weight(self, flow_label, weight):

        for i in range(self.depth):
            index = mmh3.hash(flow_label, i) % self.width

            counter_limit = (1 << self.counter_bits) - 1
            if self.counters[i][index] + weight <= counter_limit:
                self.counters[i][index] += weight



    def report(self, flow_label):
        '''
        Report the estimated flow size of given flow label
        '''
        # min_index = (0, 0) # initialize the index for min value
        min_value = float('inf') # init the min value with infinity

        for i in range(self.depth):
            j = mmh3.hash(flow_label, i) % self.width
            val = self.counters[i][j]
            if val < min_value:
                min_value = val
                # min_index = (i, j)
        return min_value


    def memory_usage(self):
        '''
        :return: memory in KB
        '''
        memory_kb = (self.depth * self.width * self.counter_bits) / (1024 * 8)
        return round(memory_kb)


def init_CountMin(memory_kb):
    # set the counter size to 32 bits
    counter_bits = 32 # bits

    total_counters = (memory_kb * 1024 * 8) // counter_bits
    # depth = int(np.log2(total_counters))
    depth = 4
    width = int(total_counters / depth)

    CM = CountMin(width, depth, counter_bits)
    return CM
