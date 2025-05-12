

import mmh3
from Packet import Packet

class ASketch:
    def __init__(self, memory_bits):
        self.memory_bits = memory_bits # memory size (in bit)
        self.item_size = 96  # each item has 96 bits as recommended (flow label 32 bits, new_count 32 bits, old_count 32 bits)
        self.num_items = self.memory_bits // self.item_size  # The largest number of items

        # Initialize the filter: a dictionary where keys are flow labels and values are tuples (new_count, old_count)
        self.filter = {} # we use a dict to replace the item list for accelerating


    def update(self, packet):
        """
        Update the filter with a new packet
        return: True if the update was successful, False otherwise.
        """
        flow_label = packet.flow_label

        # If the flow label exists in the filter, update its count
        if flow_label in self.filter.keys():
            new_count, old_count = self.filter[flow_label]
            self.filter[flow_label] = (new_count + 1, old_count)
            return True

        # If the flow label is not in the filter and there's space, insert it
        if len(self.filter) < self.num_items:
            self.filter[flow_label] = (1, 0)
            return True

        return False


    def report(self, flow_label):

        """
        Report the new_count for the given flow_label.
        If the flow_label is not found in the filter, return -1.
        """
        if flow_label in self.filter.keys():
            return self.filter[flow_label][0]
        return -1

    def top_k_query(self, k):
        """
        Return a list of tuple (flow_label, new_count) for the top k flows based on new_count.
        """

        if k > len(self.filter):
            print("Warning: k exceeds the maximum number of counters in ASketch, results may be inaccurate.")
            top_k_elements = list(self.filter.items())
        else:
            sorted_items = sorted(self.filter.items(), key=lambda x: x[1][0], reverse=True)

            top_k_elements = sorted_items[:k]

        return [(flow_label, count[0]) for flow_label, count in top_k_elements]



    def memory_usage(self):
        """
        Calculate the total memory usage of the ASketch
        :return: memory in KB
        """
        memory_kb = self.memory_bits / (1024 * 8)
        return round(memory_kb)




def init_ASketch(memory_kb):
    '''
    :param memory_kb: KB
    :return:
    '''
    memory_bits = int(memory_kb * 1024 * 8)
    AS = ASketch(memory_bits)
    return AS

