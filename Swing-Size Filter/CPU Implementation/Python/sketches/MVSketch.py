# An implementation of MV-Sketch proposed in paper:
# A Fast and Compact Invertible Sketch for Network-Wide Heavy Flow Detection

import mmh3

class MVSketch:
    def __init__(self, r, w):
        self.r = r
        self.w = w
        # each bucket is a tuple (V, Key, C)
        self.buckets = [[(0, '', 0) for _ in range(w)] for _ in range(r)]


    def update_with_weight(self, key, weight):
        '''
        update sketch with weight for given item ID or flow label
        :param key: item ID or flow label
        :param weight: weight to be inserted
        '''
        for i in range(self.r):
            j = mmh3.hash(str(key), seed=i) % self.w

            b_V, b_key, b_C = self.buckets[i][j]

            # increase V by weight
            b_V += weight

            # check if key matches
            if b_key == key:
                b_C += weight
            else:
                b_C -= weight

                if b_C < 0:
                    # replace key and set C to its absolute value
                    b_key = key
                    b_C = abs(b_C)

            # update bucket
            self.buckets[i][j] = (b_V, b_key, b_C)



    def update(self, packet):
        self.update_with_weight(packet.flow_label, 1)




    def report(self, key):
        '''
        query the sketch for estimated frequency of given item ID or flow label
        :param key: item ID or flow label
        :return: estimated frequency of the given item ID or flow label
        '''
        estimates = []
        for i in range(self.r):
            j = mmh3.hash(str(key), seed=i) % self.w
            V, bucket_key, C = self.buckets[i][j]

            if bucket_key == key:
                es = (V + C) / 2
            else:
                es = (V - C) / 2

            estimates.append(es)

        return min(estimates)


    def heavy_hitter_query(self, heavy_hitter_threshold):
        '''
        query for heavy hitters (items with frequency above heavy_hitter_threshold)
        :param heavy_hitter_threshold: threshold for heavy hitter detection
        :return: list of heavy hitters, each represented as a tuple (key, size)
        '''
        heavy_hitters = []
        heavy_hitters_set = set()

        for i in range(self.r):
            for j in range(self.w):
                V, key, _ = self.buckets[i][j]

                if key in heavy_hitters_set:
                    continue
                else:
                    if V > heavy_hitter_threshold:
                        size = self.report(key)

                        if size > heavy_hitter_threshold:
                            heavy_hitters.append((key, size))
                            heavy_hitters_set.add(key)



        return heavy_hitters



    def heavy_hitter_query_with_filter(self, filter, heavy_hitter_threshold):
        '''
        Because the filter intercept some packets, the total sum value V in a bucket may be
        less than the threshold, so remove the condition of "V > heavy_hitter_threshold",
        just check whether estimated size plus filter estimation larger than threshold.

        query for heavy hitters (items with frequency above heavy_hitter_threshold)
        :param filter: a filter combined with
        :param heavy_hitter_threshold: threshold for heavy hitter detection
        :return: list of heavy hitters, each represented as a tuple (key, size)
        '''
        heavy_hitters = []
        heavy_hitters_set = set()

        for i in range(self.r):
            for j in range(self.w):
                V, key, _ = self.buckets[i][j]

                if key in heavy_hitters_set:
                    continue
                else:

                    size = self.report(key)
                    # estimated size in filter
                    size_in_filter, _ = filter.report(key)

                    total_size = size + size_in_filter

                    if total_size > heavy_hitter_threshold:
                        heavy_hitters.append((key, total_size))
                        heavy_hitters_set.add(key)


        return heavy_hitters


    def all_heavy_flows(self):
        heavy_flows = []
        heavy_flows_set = set()

        for i in range(self.r):
            for j in range(self.w):
                V, key, _ = self.buckets[i][j]

                if key in heavy_flows_set:
                    continue
                else:
                    size = self.report(key)
                    heavy_flows.append((key, size))
                    heavy_flows_set.add(key)

        return heavy_flows


def init_MVSketch(memory_kb):

    bucket_bits = 96 # 32 bits V + 32 bits key + 32 bits C

    r = 4 # as did of the setting in the paper

    total_buckets = (memory_kb * 1024 * 8) // bucket_bits

    w = total_buckets // r

    return  MVSketch(r, w)
