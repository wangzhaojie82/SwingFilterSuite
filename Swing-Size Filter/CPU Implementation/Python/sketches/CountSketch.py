import math

import numpy as np
import mmh3

class CountSketch:
    def __init__(self, width, depth, counter_bits=32):
        self.depth = depth
        self.width = width
        self.counter_bits = counter_bits  # bits for each counter
        self.num_counters = width * depth  # total number of counters
        self.counters = np.zeros((depth, width), dtype=np.int32)


    def hash_s(self, flow_label, counter_index):
        '''
        :param flow_label: flow label
        :param counter_index: index with format (i, j)
        :return: corresponding operation
        '''
        hash_value = mmh3.hash(str(flow_label) + str(counter_index))
        return 1 if hash_value % 2 == 0 else -1


    def find_k_counters(self, flow_label):
        '''
        :return: a list of selected counters indexd by (i, j)
        '''
        selected_counters = []
        for i in range(self.depth):
            j = mmh3.hash(flow_label, i) % self.width
            selected_counters.append((i, j))
        return selected_counters


    def update(self, packet):
        flow_label = packet.flow_label

        selected_counters = self.find_k_counters(flow_label)
        for i, j in selected_counters:
            op_ = self.hash_s(flow_label, (i, j))

            if op_ == 1:
                self.counters[i, j] = min(self.counters[i, j] + 1, (1 << (self.counter_bits - 1)) - 1)
            else:
                self.counters[i, j] = max(self.counters[i, j] - 1, -(1 << (self.counter_bits - 1)))


    def report(self, flow_label):
        '''
        frequency estimation
        :param flow_label:
        :return:
        '''
        values = []
        selected_counters = self.find_k_counters(flow_label)

        for i, j in selected_counters:
            counter_value = self.counters[i, j]
            op_ = self.hash_s(flow_label, (i, j))
            values.append(counter_value * op_)

        median_value = np.median(values)
        return median_value


    def memory_usage(self):
        """
        :return: memory in kb
        """
        memory_kb = (self.depth * self.width * self.counter_bits) / (8 * 1024)
        return round(memory_kb)



def init_CountSketch(memory_kb):
    # Set the counter size to 32 bits
    counter_bits = 32  # bits

    # Calculate total number of counters based on memory size and counter size
    total_counters = (memory_kb * 1024 * 8) // counter_bits
    # depth = int(math.log2(total_counters))
    depth = 4
    width = int(total_counters / depth)

    # Create and return a CountSketch instance
    CS = CountSketch(width, depth, counter_bits)
    return CS