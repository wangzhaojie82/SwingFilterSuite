
# An implementation of WavingSketch proposed in:
# https://doi.org/10.1145/3394486.3403208

import random
import mmh3


class Cell:
    def __init__(self):
        self.flow_label = '' # The flow_label to which a packet belongs (ID field in paper), 32 bits
        self.frequency = 0 # the estimated frequency, 32 bits
        #  the flag indicates whether the frequency has error,
        #  {True: the frequency is error-free; False: the frequency has error}
        self.flag = True # True indicates the frequency is error free, 1 bit


class Bucket:
    def __init__(self, num_cells=16):
        self.waving_counter = 0 # 32-bit signed counter
        self.heavy_part = [Cell() for _ in range(num_cells)]

    def is_full(self):
        # True: heavy part is full; False: otherwise
        return all(cell.flow_label != '' for cell in self.heavy_part)

    def find_cell(self, flow_label):
        # Find the cell that records the specified flow
        cell_index = 0
        for cell in self.heavy_part:
            if cell.flow_label == flow_label:
                return cell_index, cell
            cell_index += 1
        # if the specified flow is not recorded in heavy part, then return None
        return None, None

    def find_min_cell(self):
        # Find the cell with minimum frequency field
        min_cell_index, min_cell = min(enumerate(self.heavy_part), key=lambda x: (x[1].frequency if x[1].frequency > 0 else float('inf')))
        return min_cell_index, min_cell


class WavingSketch:
    def __init__(self, num_buckets, num_cells=16):
        self.num_buckets = num_buckets # WavingSketch contains l buckets
        self.num_cells = num_cells # the heavy part in each bucket contains d cells
        self.buckets = [Bucket(num_cells) for _ in range(num_buckets)]

    def hash_h(self, flow_label):
        hash_value = "{:08x}".format(mmh3.hash(str(flow_label)))
        return int(hash_value, 16) % self.num_buckets

    def hash_s(self, flow_label):
        hash_value = mmh3.hash(str(flow_label))
        return 1 if hash_value % 2 == 0 else -1

    def update(self, packet):
        bucket_index = self.hash_h(packet.flow_label)
        bucket = self.buckets[bucket_index]
        # check whether the flow is recorded in heavy part
        cell_index, cell = bucket.find_cell(packet.flow_label)
        if cell is not None: # flow is recorded in the heavy part
            if cell.flag:
                cell.frequency += 1
            else:
                cell.frequency += 1
                # Simulating hash_s value update
                bucket.waving_counter += self.hash_s(packet.flow_label)

        else: # flow is not recorded in the heavy part
            if not bucket.is_full(): # heavy part is not full
                for cell in bucket.heavy_part:
                    if cell.flow_label == '': # the first empty cell
                        cell.flow_label = packet.flow_label
                        cell.frequency = 1
                        cell.flag = True
                        break
            else: # heavy part is full

                # update waving counter
                bucket.waving_counter += self.hash_s(packet.flow_label)
                # calculate the estimated frequency
                estimated_frequency = bucket.waving_counter * self.hash_s(packet.flow_label)
                # find the smallest cell in heavy part
                min_cell_index, min_cell = bucket.find_min_cell()
                # check whether the updated frequency is larger than the smallest cell
                if estimated_frequency > min_cell.frequency:
                    if min_cell.flag:
                        # update waving counter
                        bucket.waving_counter += min_cell.frequency * self.hash_s(min_cell.flow_label)
                    # replace the smallest cell with new incoming flow
                    min_cell.flow_label = packet.flow_label
                    min_cell.frequency = estimated_frequency
                    min_cell.flag = False

    def report_unbiased(self, flow_label):

        bucket_index = self.hash_h(flow_label)
        bucket = self.buckets[bucket_index]

        # Check if the flow is in the heavy part
        cell_index, cell = bucket.find_cell(flow_label)
        if cell is not None and cell.flag:
            # Return frequency if flow is in the heavy part and flag is true
            return cell.frequency
        else:
            # Return estimated size if flow is not in the heavy part or flag is False
            return bucket.waving_counter * self.hash_s(flow_label)


    def report(self, flow_label):

        bucket_index = self.hash_h(flow_label)
        bucket = self.buckets[bucket_index]

        # Check if the flow is in the heavy part
        cell_index, cell = bucket.find_cell(flow_label)
        if cell is not None:
            # Return frequency if flow is in the heavy part
            return cell.frequency
        else:
            # Return estimated size if flow is not in the heavy part or flag is False
            return bucket.waving_counter * self.hash_s(flow_label)


    def memory_usage(self):
        '''
        :return: memory in kb
        '''
        # Calculate the number of buckets based on the memory size
        # Each bucket has a 32-bit waving_counter
        # and 16 cells * (32-bit flow_label + 18-bit frequency + 1-bit flag)
        bucket_size = 32 + 16 * (32 + 32 + 1)  # size in bits
        memory_kb = (self.num_buckets * bucket_size)/(1024 * 8)
        return round(memory_kb)


def init_WavingSketch(memory_kb):
    """
    Initialize a WavingSketch object based on the given memory size.
    :param memory_kb: The size of the memory in kilobytes.
    :return: A WavingSketch object.
    """
    # Calculate the number of buckets based on the memory size
    bucket_size = 20 + 12 * (32 + 32 + 1)  # size in bits
    num_buckets = int((memory_kb * 1024 * 8) / bucket_size)  # Convert KB to bits

    return WavingSketch(num_buckets)