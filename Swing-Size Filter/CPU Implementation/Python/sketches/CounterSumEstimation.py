
# The software implementation of counter sum estimation (CSM) in paper:
# Per-Flow Traffic Measurement Through Randomized Counter Sharing

import random
import mmh3

class CounterSumEstimation:
    def __init__(self, m, l=50, bits=32):
        '''
        :param m: length of the array (parameter m in paper)
        :param l: each flow is mapped to l counters randomly, default l=50 as recommended in paper
        :param bits: bits for each counter, default 32 bits for large flow
        '''
        self.num_counters = m
        self.l = l
        self.bits = bits
        self.counters = [0] * m
        self.total_packets = 0 # count the total packets inserted for estimation proposed in paper

    def update(self, packet):

        flow_label = packet.flow_label
        # to simulate the random chosen
        i = mmh3.hash(str(packet.ID)) % self.l
        hash_value = mmh3.hash(flow_label, i)
        counter_index = hash_value % self.num_counters
        self.counters[counter_index] += 1
        self.total_packets += 1


    def storage_vector(self, flow_label):
        '''
        :param flow_label: label of flow f
        :return: the storage vector (contains l counters indices) of flow f
        '''
        l = self.l
        vector = []
        for i in range(l):
            hash_value = mmh3.hash(flow_label, i)
            counter_index = hash_value % self.num_counters
            vector.append(counter_index)
        return vector


    def report(self, flow_label):
        '''
        :param flow_label: label of flow f
        :return: the estimated size of flow f according to CSM estimation in paper
        '''

        vector = self.storage_vector(flow_label)

        size = 0
        for index in vector:
            size += self.counters[index]

        estimation = size - self.l * (self.total_packets / self.num_counters)

        return estimation


    def memory_usage(self):
        '''
        :return: memory in KB
        '''
        memory_kb = (self.num_counters * self.bits) / (1024 * 8)
        return round(memory_kb)



def init_CounterSumEstimation(memory_kb):
    '''
    init a CounterSumEstimation based on given memory (KB)
    :param memory_kb: memory in KB
    :return:
    '''

    # set the counter size to 32 bits by default
    counter_bits = 32 # bits
    l = 50 # recommended in paper

    num_counters = (memory_kb * 1024 * 8) // counter_bits

    CSM = CounterSumEstimation(num_counters, l, counter_bits)
    return CSM