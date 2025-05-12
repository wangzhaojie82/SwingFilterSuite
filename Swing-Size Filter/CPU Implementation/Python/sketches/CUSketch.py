

import numpy as np
import mmh3


'''
Implementation of Conservative Update, a.k.a, CM-CU, CU Sketch
'''

class CUSketch:
    def __init__(self, width, depth, counter_bits=32):
        self.width = width
        self.depth = depth
        self.counter_bits = counter_bits  # num bits for each counter
        self.num_counters = width * depth  # total number of counters
        self.counters = np.zeros((depth, width), dtype=np.int32)


    def select_counters(self, flow_label):
        '''
        :return: a list of selected counters indexed by (i, j)
        '''
        selected_counters = []
        for i in range(self.depth):
            j = mmh3.hash(flow_label, i) % self.width
            selected_counters.append((i, j))
        return selected_counters


    def update(self, packet):
        flow_label = packet.flow_label

        selected_counters = self.select_counters(flow_label)

        # Find the minimum value among the hashed counters
        min_val = min(self.counters[i][j] for i, j in selected_counters)

        counter_limit = (1 << self.counter_bits) - 1
        # Update the minimum counters
        for i, j in selected_counters:
            if self.counters[i][j] == min_val and self.counters[i][j] < counter_limit:
                self.counters[i][j] += 1


    def report(self, flow_label):
        '''
        Report the estimated flow size of the given flow label
        '''
        # min_index = (0, 0)  # initialize the index for min value
        min_value = float('inf')  # init the min value with infinity

        for i in range(self.depth):
            j = mmh3.hash(flow_label, i) % self.width
            val = self.counters[i][j]
            if val < min_value:
                min_value = val
                # min_index = (i, j)
        return min_value

    def memory_usage(self):
        '''
        :return: memory in kb
        '''
        memory_kb = (self.depth * self.width * self.counter_bits) / (1024 * 8)
        return round(memory_kb)



def init_CUSketch(memory_kb):
    # set the counter size to 32 bits
    counter_bits = 32 # bits

    total_counters = (memory_kb * 1024 * 8) // counter_bits
    # depth = int(np.log2(total_counters))
    depth = 4
    width = int(total_counters / depth)

    CU = CUSketch(width, depth, counter_bits)
    return CU