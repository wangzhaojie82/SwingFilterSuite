
from collections import Counter

# An approximate implementation of Space Saving
# Credit to: https://codereview.stackexchange.com/users/180160/phipsgabler
# This guy's code is very helpful. Thanks!


class SpaceSaving:

    def __init__(self, memory_size_kb):
        # memory_size_kb: available memory in KB
        self.memory_usage_ = memory_size_kb
        self.elements_seen = 0
        self.counts = Counter()  # contains the accurate counts for elements
        self.bits_per_element = 96  # default: 32 bits for count, 32 bits for tstamp, 32 bits for key
        self.l = (memory_size_kb * 1024 * 8) // self.bits_per_element  # maximum number of counters, we should ensure the l >= k


    def _update_element(self, x):
        self.elements_seen += 1

        if x in self.counts:
            self.counts[x] += 1

        elif len(self.counts) < self.l:
            self.counts[x] = 1
        else:
            self._replace_least_element(x)

    def _replace_least_element(self, e):

        min_element, min_count = self.counts.most_common()[-1]

        del self.counts[min_element]

        self.counts[e] = min_count + 1



    def update(self, packet):
        """
        Encapsulate a new update function for traffic process.
        its count increments by 1
        """
        self._update_element(packet.flow_label)


    def query(self, k):
        """
        :return top k items and their frequencies. A list of tuple (item_key, frequency)
        """

        if k > self.l:
            top_k_elements = self.counts.most_common(self.l)
            top_k_elements.extend([("", 0)] * (k - self.l))
        else:
            top_k_elements = self.counts.most_common(k)

        return top_k_elements


    def query_with_filter(self, filter, k):
        """
        :return top k flows and their size. A list of tuple (flow_label, size)
        """
        all_elements = []
        for element, count in self.counts.items():
            size_in_filter, large_flow_flag = filter.report(element)
            total_size = count + size_in_filter
            all_elements.append((element, total_size))


        sorted_elements = sorted(all_elements, key=lambda x: x[1], reverse=True)
        return sorted_elements[:k]



    def memory_usage(self):
        '''
        :return: memory size in KB
        '''
        return self.memory_usage_



def init_SpaceSaving(memory_kb):

    SS = SpaceSaving(memory_kb)
    return SS