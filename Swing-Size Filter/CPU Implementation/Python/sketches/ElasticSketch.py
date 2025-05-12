
# An implementation of measurement scheme:
# Elastic Sketch: Adaptive and Fast Network-wide Measurements

from sketches import CountMin
import mmh3

class ElasticSketch:
    def __init__(self, len_heavy, count_min):
        self.len_heavy = len_heavy # number of buckets in heavy part
        self.heavy_part = [("", 0, False, 0) for _ in range(len_heavy)]  # Initialize heavy_part with empty tuples
        self.count_min = count_min  # light_part is implemented by a CountMin
        self.lambda_ = 8


    def update(self, packet):

        flow_label = packet.flow_label
        bucket_index = mmh3.hash(flow_label) % self.len_heavy

        # tuple: (label, vote+, flag, vote−)
        hashed_tuple = self.heavy_part[bucket_index]

        # Case 1: The bucket is empty
        if hashed_tuple[0] == "":
            self.heavy_part[bucket_index] = (flow_label, 1, False, 0)

        # Case 2: flow_label matches
        elif hashed_tuple[0] == flow_label:
            self.heavy_part[bucket_index] = (flow_label, hashed_tuple[1] + 1, hashed_tuple[2], hashed_tuple[3])

        # flow_label does not match
        else:

            self.heavy_part[bucket_index] = (hashed_tuple[0], hashed_tuple[1], hashed_tuple[2], hashed_tuple[3] + 1)

            # Case 3: vote-/vote+ < lambda
            if self.heavy_part[bucket_index][3] / self.heavy_part[bucket_index][1] < self.lambda_:
                # Insert (f, 1) into the CountMin sketch
                self.count_min.update_with_weight(flow_label, 1)

            else: # Case 4: vote-/vote+ >= lambda

                # re-obtain the value, since vote- was updated
                replaced_flow = self.heavy_part[bucket_index]

                self.heavy_part[bucket_index] = (flow_label, 1, True, 1)

                # evict repleaced element to light part (count-min)
                self.count_min.update_with_weight(replaced_flow[0], replaced_flow[1])


    def report(self, flow_label):
        '''
        estimate the size of given flow for flow size estimation task
        :param flow_label:
        :return: estimated size
        '''

        bucket_index = mmh3.hash(flow_label) % self.len_heavy

        # tuple: (label, vote+, flag, vote−)
        hashed_tuple = self.heavy_part[bucket_index]

        if hashed_tuple[0] == flow_label:
            if hashed_tuple[2] == True:
                size_in_light = self.count_min.report(flow_label)
                return hashed_tuple[1] + size_in_light

            else:
                return hashed_tuple[1]

        else: # flow not in heavy part
            return self.count_min.report(flow_label)


def init_ElasticSketch(memory_size_kb):

    memory_4_light = memory_size_kb // 2

    # calculate number of buckets in heavy part
    # each bucket is 97 bits: 32 label + 32 positive vote + 1 flag + 32 negative vote
    len_heavy = ((memory_size_kb - memory_4_light) * 1024 * 8) // 97

    light_part = CountMin.init_CountMin(memory_4_light)
    # light_part = SwingFilter.init_SwingFilter(memory_4_light)


    Elastic = ElasticSketch(len_heavy, light_part)

    return Elastic
