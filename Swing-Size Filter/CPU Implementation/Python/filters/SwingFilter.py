import mmh3
import statistics


# Swing Filter
class SwingCounter:

    def __init__(self, num_counters, bits=10, d=3):
        '''
        :param num_counters: number of counters == len(self.counters)
        :param d: each flow will be distributed over d counters
        :param bits: bits of each counter, default is 10 bits
        '''
        self.d = d
        self.bits = bits
        self.num_counters = num_counters
        self.counters = [0] * self.num_counters  # a list of counters initialized by 0

    def is_overflow(self, counter_index, op_):
        '''
        check whether the next update operation will cause counter overflows
        :param counter_index:
        :param op_:
        :return: True indicates the update operation will cause overflow, otherwise False
        '''

        current_value = self.counters[counter_index]
        next_value = current_value + op_

        return next_value > (1 << (self.bits - 1)) - 1 or next_value < -(1 << (self.bits - 1))


    def find_d_counters(self, flow_label):
        '''
        :param flow_label: flow label
        :return: a list of counter_indices for the d hashed counters of flow
        '''

        d = self.d
        d_counters = []
        for i in range(d):
            hash_value = mmh3.hash(flow_label, i)
            counter_index = hash_value % self.num_counters
            d_counters.append(counter_index)
        return d_counters

    def find_1_counter(self, packet):
        '''
        select 1 counter from counters for packet
        :param packet: a packet
        :return: counter_index for the found counter
        '''

        # We use a hash operation to approximate 0 to d-1 random number generation
        # to speed up execution and, in fact, have almost no impact on the results
        i = mmh3.hash(str(packet.ID)) % self.d
        hash_value = mmh3.hash(packet.flow_label, i)
        counter_index = hash_value % self.num_counters
        return counter_index


    def hash_s(self, flow_label, counter_index):
        '''
        :param flow_label: flow label
        :param counter_index: index of the found counter for packet
        :return: corresponding operation
        '''

        hash_value = mmh3.hash(str(flow_label) + str(counter_index))
        return 1 if hash_value % 2 == 0 else -1


    def update(self, packet):
        '''
        Update the Swing Counter with a packet
        :param packet: new packet
        :return: Flag in {True: Successfully update; False: Fail to update}
        '''

        # update the Swing counter
        counter_index = self.find_1_counter(packet)
        op_ = self.hash_s(packet.flow_label, counter_index)

        # check whether the next update operation will cause counter overflows
        if self.is_overflow(counter_index, op_):
            # the counter will overflows, do not update it
            return False

        else:
            # the counter will not overflow, then update it
            self.counters[counter_index] += op_
            # Successfully update counter with the packet
            return True


class SwingFilter:
    def __init__(self, layers, layers_config):
        """
        :param layers: the layers of SwingCounters
        :param layers_config: List of tuples, each tuple contains the configuration (num_counters, bits, k) for a layer
        """
        self.layers = layers
        self.filter = [SwingCounter(num_counters, bits, k) for num_counters, bits, k in layers_config]
        self.layers_config = layers_config # 各层的参数

    def update(self, packet):
        """
        Update the filter with a new packet
        :return: True if the update was successful within the filter, False if it overflows out of the filter
        """
        for Swing_counter in self.filter:
            updated_successfully = Swing_counter.update(packet)
            if updated_successfully:
                return True

        # Returns False if all layers overflow
        return False


    def report(self, flow_label):
        """
        Report the size of a specific flow across all layers of the filter
        :param flow_label: The label of the flow to report
        :return: The total size of the flow
        """
        estimation = 0
        large_flow_flag = True # report whether this flow is a large flow. True: is a large Flow

        for Swing_counter in self.filter:

            k_es_values = []
            counter_indices = Swing_counter.find_d_counters(flow_label)
            for index in counter_indices:
                op_ = Swing_counter.hash_s(flow_label, index)
                es_ = Swing_counter.counters[index] * op_
                k_es_values.append(es_)

            s_value = sum(k_es_values)

            num_hash = Swing_counter.d
            # if the estimated size less than counter capacity of this layer
            if s_value < num_hash * ((1 << (Swing_counter.bits - 1)) - 1) :
                estimation += s_value
                large_flow_flag = False 
                break
            else:
                estimation += s_value

        return estimation, large_flow_flag
        # return estimation


    def memory_usage(self):
        """
        Calculate the total memory usage of the SwingFilter
        :return: memory in kb
        """
        memory_usage = 0
        for Swing_counter in self.filter:
            # Storage for each layer = num_counters * bits
            memory_usage += Swing_counter.num_counters * Swing_counter.bits

        memory_kb = memory_usage / (1024 * 8)
        return round(memory_kb)


def init_SwingFilter(memory_kb):
    '''
    :param memory_kb: KB
    :return:
    '''
    d = 3
    bits = [4, 8]

    memory_bits = memory_kb * 1024 * 8

    memory_bits_layer_0 = round(memory_bits * 0.50)
    memory_bits_layer_1 = memory_bits - memory_bits_layer_0
    num_counters_layer_0 = int(memory_bits_layer_0 / bits[0])
    num_counters_layer_1 = int(memory_bits_layer_1 / bits[1])


    conf_layer0 = (num_counters_layer_0, bits[0], d)
    conf_layer1 = (num_counters_layer_1, bits[1], d)
    layers_config = [conf_layer0, conf_layer1]
    BF = SwingFilter(2, layers_config)
    return BF

