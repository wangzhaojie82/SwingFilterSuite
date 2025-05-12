
'''
A python implementation for optimized version of Ladder Filter.
We follow the settings in C++ code provided by authors.
'''

import mmh3

class LadderFilter:
    def __init__(self, que1_len, que2_len, cell_num=8, que1_thres=2, high_thres=12):
        self.que1_len = que1_len # number of buckets in queue1
        self.que2_len = que2_len  # number of buckets in queue2
        self.cell_num = cell_num # number of cells in each bucket

        self.times = 0

        self.que1_thres = que1_thres # low threshold for queue1
        self.high_thres = high_thres # common high threshold

        self.queue1 = [[('', 0, 0) for _ in range(self.cell_num)] for _ in range(que1_len)]
        self.queue2 = [[('', 0, 0) for _ in range(self.cell_num)] for _ in range(que2_len)]


    def update(self, packet):
        flow_label = packet.flow_label
        timestamp = packet.ID

        # search the flow in queue 1
        bucket_idx1 = mmh3.hash(flow_label, 1) % self.que1_len

        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[0] == flow_label:
                freq = min(cell[1] + 1, 255)
                self.queue1[bucket_idx1][i] = (flow_label, freq, timestamp)
                if freq < self.high_thres:
                    return True, 0
                elif freq == self.high_thres:
                    return False, freq # this indicate the sketch should also update the packet
                else:
                    return False, 1

        # search the flow in queue 2
        bucket_idx2 = mmh3.hash(flow_label, 2) % self.que2_len

        for i, cell in enumerate(self.queue2[bucket_idx2]):
            if cell[0] == flow_label:
                freq = min(cell[1] + 1, 255)
                self.queue2[bucket_idx2][i] = (flow_label, freq, timestamp)
                if freq < self.high_thres:
                    return True, 0
                elif freq == self.high_thres:
                    return False, freq  # this indicate the sketch should also update the packet
                else:
                    return False, 1

        # insert the flow to queue 1, if bucket is not full
        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[0] == '':
                # Insert the flow into an empty cell
                self.queue1[bucket_idx1][i] = (flow_label, 1, timestamp)
                return True, 0

        # If no empty cell found, replace the oldest cell with the new flow
        min_timestamp, min_cell_idx = timestamp, 0
        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[2] < min_timestamp:
                min_timestamp = cell[2]
                min_cell_idx = i

        # Replace the oldest cell with the new flow
        min_cell = self.queue1[bucket_idx1][min_cell_idx]
        self.queue1[bucket_idx1][min_cell_idx] = (flow_label, 1, timestamp)

        # if least recent flow is larger than threshold, insert the promising flow to queue 2
        if min_cell[1] > self.que1_thres:

            promising_bucket_idx2 = mmh3.hash(min_cell[0], 2) % self.que2_len

            # if bucket is not full in queue 2
            for i, cell in enumerate(self.queue2[promising_bucket_idx2]):
                if cell[0] == '':
                    # Insert the flow into an empty cell
                    self.queue2[promising_bucket_idx2][i] = (min_cell[0], min_cell[1], timestamp)
                    return True, 0

            # If no empty cell found, replace the oldest cell with the promising flow
            min_timestamp_, min_cell_idx_ = timestamp, 0
            for i, cell in enumerate(self.queue2[promising_bucket_idx2]):
                if cell[2] < min_timestamp_:
                    min_timestamp_ = cell[2]
                    min_cell_idx_ = i

            self.queue2[promising_bucket_idx2][min_cell_idx_] = (min_cell[0], min_cell[1], timestamp)
            return True, 0

        return True, 0


    def update_with_weight(self, flow_label, weight):
        self.times += 1
        timestamp = self.times

        # search the flow in queue 1
        bucket_idx1 = mmh3.hash(flow_label, 1) % self.que1_len

        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[0] == flow_label:
                freq = min(cell[1] + weight, 255)
                self.queue1[bucket_idx1][i] = (flow_label, freq, timestamp)
                return True

        # search the flow in queue 2
        bucket_idx2 = mmh3.hash(flow_label, 2) % self.que2_len

        for i, cell in enumerate(self.queue2[bucket_idx2]):
            if cell[0] == flow_label:
                freq = min(cell[1] + weight, 255)
                self.queue2[bucket_idx2][i] = (flow_label, freq, timestamp)
                return True

        # insert the flow to queue 1, if bucket is not full
        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[0] == '':
                # Insert the flow into an empty cell
                self.queue1[bucket_idx1][i] = (flow_label, weight, timestamp)
                return True

        # If no empty cell found, replace the oldest cell with the new flow
        min_timestamp, min_cell_idx = timestamp, 0
        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[2] < min_timestamp:
                min_timestamp = cell[2]
                min_cell_idx = i

        # Replace the oldest cell with the new flow
        min_cell = self.queue1[bucket_idx1][min_cell_idx]
        self.queue1[bucket_idx1][min_cell_idx] = (flow_label, weight, timestamp)

        # if least recent flow is larger than threshold, insert the promising flow to queue 2
        if min_cell[1] > self.que1_thres:

            promising_bucket_idx2 = mmh3.hash(min_cell[0], 2) % self.que2_len

            # if bucket is not full in queue 2
            for i, cell in enumerate(self.queue2[promising_bucket_idx2]):
                if cell[0] == '':
                    # Insert the flow into an empty cell
                    self.queue2[promising_bucket_idx2][i] = (min_cell[0], min_cell[1], timestamp)
                    return True

            # If no empty cell found, replace the oldest cell with the promising flow
            min_timestamp_, min_cell_idx_ = timestamp, 0
            for i, cell in enumerate(self.queue2[promising_bucket_idx2]):
                if cell[2] < min_timestamp_:
                    min_timestamp_ = cell[2]
                    min_cell_idx_ = i

            self.queue2[promising_bucket_idx2][min_cell_idx_] = (min_cell[0], min_cell[1], timestamp)
            return True


    def report(self, flow_label):
        # search the flow in queue 1
        bucket_idx1 = mmh3.hash(flow_label, 1) % self.que1_len
        for i, cell in enumerate(self.queue1[bucket_idx1]):
            if cell[0] == flow_label:
                return cell[1]

        # search the flow in queue 2
        bucket_idx2 = mmh3.hash(flow_label, 2) % self.que2_len
        for i, cell in enumerate(self.queue2[bucket_idx2]):
            if cell[0] == flow_label:
                return cell[1]

        # if not found, the flow may be discarded, return -1
        return -1



def init_LadderFilter(memory_kb):

    memory_que1 = memory_kb * 0.5
    memory_que2 = memory_kb - memory_que1

    que1_len = (memory_que1 * 1024 * 8) // ((32 + 8 + 32) * 8) # each bucket has 8 cells, each cell is (32bits label, 8bits counter, 32 bits timestamp)
    que2_len = (memory_que2 * 1024 * 8) // ((32 + 8 + 32) * 8) # each bucket has 8 cells, each cell is (32bits label, 8bits counter, 32 bits timestamp)

    return LadderFilter(int(que1_len), int(que2_len))

