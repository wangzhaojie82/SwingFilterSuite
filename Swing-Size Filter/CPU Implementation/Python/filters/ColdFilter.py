import mmh3


class ColdCounter:
    def __init__(self, num_counters, bits, num_hash, threshold):
        self.num_counters = num_counters  # num of counters
        self.bits = bits  # bits of each counter
        # Parameter d in paper, num of hash functions for 1 flow
        # each flow will be hased to num_hash counters
        self.num_hash = num_hash
        # Setting default threshold to the maximum value for counter bits

        self.threshold = ((1 << bits) - 1) if threshold is None else threshold
        self.counters = [0] * self.num_counters  # a list of counters initialized by 0

    def find_d_counters(self, flow_label):
        '''
        :return: a list of indices of counters to be hashed to
        '''
        counter_indices = []
        for i in range(self.num_hash):
            hash_val = mmh3.hash(flow_label, i) % self.num_counters
            counter_indices.append(hash_val)
        return counter_indices


    def update(self, packet):
        counter_indices = self.find_d_counters(packet.flow_label)

        # Check if all d counters have reached the threshold
        if all(self.counters[index] >= self.threshold for index in counter_indices):
            return False  # Update unsuccessful, all counters have reached threshold

        # Find the minimum value among the hashed counters
        min_val = min(self.counters[i] for i in counter_indices)

        # Increment all counters with the minimum value
        for index in counter_indices:
            if self.counters[index] == min_val:
                self.counters[index] += 1
        return True  # Update successful, at least one counter below threshold and updated



    def update_by_label(self, flow_label):
        counter_indices = self.find_d_counters(flow_label)

        # Check if all d counters have reached the threshold
        if all(self.counters[index] >= self.threshold for index in counter_indices):
            return False  # Update unsuccessful, all counters have reached threshold

        # Find the minimum value among the hashed counters
        min_val = min(self.counters[i] for i in counter_indices)

        # Increment all counters with the minimum value
        for index in counter_indices:
            if self.counters[index] == min_val:
                self.counters[index] += 1
        return True  # Update successful, at least one counter below threshold and updated





class ColdFilter:
    def __init__(self, layers, layers_config):
        """
        :param layers: the layers of ColdCounters
        :param layers_config: List of tuples, each tuple contains the configuration (num_counters, bits, num_hash, threshold) for a layer
        """
        self.layers = layers
        self.filter = [ColdCounter(num_counters, bits, num_hash, threshold) for num_counters, bits, num_hash, threshold in layers_config]


    def update(self, packet):
        for cold_counter in self.filter:
            updated_successfully = cold_counter.update(packet)
            if updated_successfully:
                return True

        # Returns False if all layers overflow
        return False


    def update_with_weight(self, flow_label, weight):
        for w in range(weight):
            for cold_counter in self.filter:
                updated_successfully = cold_counter.update_by_label(flow_label)
                if updated_successfully:
                    break



    def report(self, flow_label):
        total_value = 0
        large_flow_flag = True  # report whether this flow is a large flow. True: is a large Flow

        for cold_counter in self.filter:
            counter_indices = cold_counter.find_d_counters(flow_label)
            # Find the minimum value among the hashed counters
            min_val = min(cold_counter.counters[i] for i in counter_indices)

            if min_val < cold_counter.threshold:
                total_value += min_val
                large_flow_flag = False
                break  # Stop iterating if below threshold
            else:
                total_value += cold_counter.threshold

        return total_value, large_flow_flag
        # return total_value # 用于 ES 和 AS 替换 CM 实验


    def memory_usage(self):
        memory_usage = 0
        for cold_counter in self.filter:
            # Storage for each layer = num_counters * bits
            memory_usage += cold_counter.num_counters * cold_counter.bits

        memory_kb = memory_usage / (1024 * 8)
        return round(memory_kb)



def init_ColdFilter(memory_kb):
    k = 3
    bits = [4, 8]  # counter bits for each layer
    thresholds = [15, 255]

    memory_bits = memory_kb * 1024 * 8
    memory_bits_layer_1 = int(memory_bits * 0.5)
    memory_bits_layer_2 = int(memory_bits - memory_bits_layer_1)
    # Calculate counter numbers for each layer based on the allocated memory
    num_counters_layer_1 = int(memory_bits_layer_1 // bits[0])
    num_counters_layer_2 = int(memory_bits_layer_2 // bits[1])

    # Configuration for each layer is a tuple (num_counters, bits, num_hash, threshold)
    conf_layer1 = (num_counters_layer_1, bits[0], k, thresholds[0])
    conf_layer2 = (num_counters_layer_2, bits[1], k, thresholds[1])
    layers_config = [conf_layer1, conf_layer2]
    cold_filter = ColdFilter(2, layers_config)
    return cold_filter
