
# An implementation of PyramidSketch proposed in
# Pyramid Sketch: a Sketch Framework for Frequency Estimation of Data Streams


import mmh3

class PyramidSketch:
    def __init__(self, num_layers, bucket_bits, bucket_num_per_layer):
        self.num_layers = num_layers
        self.bucket_bits = bucket_bits
        self.bucket_num_per_layer = bucket_num_per_layer

        self.num_hash_functions = 3 # hash functions on L1
        self.layers = []

        # Initialize each layer
        for i in range(num_layers):
            layer = []
            for j in range(bucket_num_per_layer[i]):
                if i == 0:
                    # For the first layer, use a pure counter
                    bucket = (0,)  # Counter only
                else:
                    # For other layers, use a mixed structure
                    bucket = (False, 0, False)  # (left flag, Counter, right flag)
                layer.append(bucket)
            self.layers.append(layer)



    def hash_f(self, flow_label, layer_index):
        bucket_indices = []
        for i in range(self.num_hash_functions):
            j = mmh3.hash(flow_label, i) % self.bucket_num_per_layer[layer_index]
            bucket_indices.append((layer_index, j))
        return bucket_indices



    def update(self, packet):
        flow_label = packet.flow_label

        # Compute bucket indices for the first layer
        bucket_indices = self.hash_f(flow_label, 0)

        for layer_index, bucket_index in bucket_indices:

            val = self.layers[layer_index][bucket_index][0]

            # Check for overflow in the layer
            if  val < ((1 << self.bucket_bits[layer_index]) - 1):
                # Increment counter
                self.layers[layer_index][bucket_index] = (val + 1,)
            else:
                self.carryin(layer_index, bucket_index)




    def carryin(self, layer_index, bucket_index):

        if layer_index >= self.num_layers - 1:
            return

        parent_layer_index = layer_index + 1
        parent_bucket_index = min(bucket_index // 2, len(self.layers[parent_layer_index]) - 1)

        # Determine if the overflowed bucket is a left child or a right child
        is_left_child = bucket_index % 2 == 0

        # Check if the parent bucket's counter is full
        parent_bucket_tuple = self.layers[parent_layer_index][parent_bucket_index]

        if parent_bucket_tuple[1] < ((1 << self.bucket_bits[parent_layer_index] - 2) - 1):

            if is_left_child:
                # Increment the parent bucket's counter
                self.layers[parent_layer_index][parent_bucket_index] = \
                    (True, parent_bucket_tuple[1] + 1,  parent_bucket_tuple[2])
            else:
                # Increment the parent bucket's counter
                self.layers[parent_layer_index][parent_bucket_index] = \
                    (parent_bucket_tuple[0], parent_bucket_tuple[1] + 1, True)

        else:
            # Carry in to the parent bucket recursively
            self.carryin(parent_layer_index, parent_bucket_index)




    def report(self, flow_label):
        '''
        estimated size based on given flow_label
        :param flow_label:
        :return: estimated size
        '''

        # Compute bucket indices for the first layer
        bucket_indices = self.hash_f(flow_label, 0)

        estimated_sizes = [] # Store estimated size on each branch/path

        for layer_index, bucket_index in bucket_indices:

            bucket = self.layers[layer_index][bucket_index]

            # Initialize estimated size with the counter value of the 1st layer
            estimated_size = bucket[0]

            # Iterate through each layer starting from the 2nd layer
            for current_layer_index in range(1, self.num_layers):
                # Get the bucket index
                current_bucket_index = min(bucket_index // 2, len(self.layers[current_layer_index]) - 1)

                # Determine if the overflowed bucket is a left child or a right child
                is_left_child = bucket_index % 2 == 0

                current_bucket = self.layers[current_layer_index][current_bucket_index]

                if is_left_child:
                    if current_bucket[0] == False:
                        break
                else:
                    if current_bucket[2] == False:
                        break

                estimated_size += current_bucket[1]  # Add the counter value of the parent bucket

                if current_bucket[0] == True and current_bucket[2] == True:
                    estimated_size -= 1

                # Update bucket index and continue to the next layer
                bucket_index = current_bucket_index

            estimated_sizes.append(estimated_size)

        # Find the minimum estimated size among all branches
        min_estimated_size = min(estimated_sizes)
        return min_estimated_size





def init_PyramidSketch(memory_kb):
    # number of layers
    num_layers = 4

    bucket_bits = [4, 8, 16, 32]

    memory_bit = memory_kb * 1024 * 8


    num_l1 = memory_bit // 12

    bucket_num_per_layer = [num_l1, num_l1//2, num_l1//4, num_l1//8]

    PS = PyramidSketch(num_layers, bucket_bits, bucket_num_per_layer)
    return PS




