from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import *
from crc import Crc
import socket, struct, pickle, os

crc32_polinomials = [0x04C11DB7, 0xEDB88320, 0xDB710641, 0x82608EDB, 0x741B8CD7, 0xEB31D82E,
                     0xD663B05, 0xBA0DC66B, 0x32583499, 0x992C1A4C, 0x32583499, 0x992C1A4C, 0x3FC1A2B3, 0x115A6B5C, 0x76BCFF11]


class BFController(object):
    # Swing filter

    def __init__(self, sw_name):

        self.topo = Topology(db="topology.db")
        self.sw_name = sw_name
        self.thrift_port = self.topo.get_thrift_port(sw_name)
        self.controller = SimpleSwitchAPI(self.thrift_port)
        self.custom_calcs = self.controller.get_custom_crc_calcs()
        print self.custom_calcs.items()
        self.d = 1
        self.d1 = 3
        self.d2 = 3
        self.bits1 = 4
        self.bits2 = 8
        self.layer_num = 2
        self.layer_opt = 2
        self.hash_nums = self.d + self.d1 + self.d2 + 6
        #self.register_num = self.d + self.d1 + self.d2 + 6 # The number of layers in Bounce filter and d of cm-sketch
        self.init()
        self.registers = []
        self.layers = []
        # The length of first layer
        self.M1 = 500000
        # The len
        self.M2 = 100000
        self.w = 50000

    def init(self):
        self.set_crc_custom_hashes()
        self.create_hashes()
        

    def set_forwarding(self):
        self.controller.table_add("forwarding", "set_egress_port", ['1'], ['2'])
        self.controller.table_add("forwarding", "set_egress_port", ['2'], ['1'])

    def reset_registers(self):
        # initialize each layer of Bounce filter
        self.controller.register_reset("L1")
        self.controller.register_reset("L2")
				# initialize each row of cm-sketch
        for i in range(self.d):
            self.controller.register_reset("sketch{}".format(i))

    def flow_to_bytestream(self, flow):
        # In this paper, we define the flow label as source address
        return socket.inet_aton(flow)

    def set_crc_custom_hashes(self):
        i = 0
        #for custom_crc32, width in self.custom_calcs.items():
        for custom_crc32, width in [(u'calc', 32), (u'calc_0', 32), (u'calc_1', 32), (u'calc_2', 32), (u'calc_3', 32), (u'calc_4', 32), (u'calc_5', 32), (u'calc_6', 32), (u'calc_7', 32), (u'calc_8', 32), (u'calc_9', 32), (u'calc_10', 32), (u'calc_11', 32)]:
            self.controller.set_crc32_parameters(custom_crc32, crc32_polinomials[i], 0xffffffff, 0xffffffff, True, True)
            i+=1

    def create_hashes(self):
        self.hashes = []
        for i in range(self.hash_nums):
            self.hashes.append(Crc(32, crc32_polinomials[i], True, 0xffffffff, True, 0xffffffff))

    def read_registers(self):
        self.layers = []
        self.registers = []
        self.layers.append(self.controller.register_read("L1"))
        self.layers.append(self.controller.register_read("L2"))
        for i in range(self.d):
            self.registers.append(self.controller.register_read("sketch{}".format(i)))

    def get_per_flow_size(self, flow):
        values = []
        value1 = 0
        value2 = 0
        for i in range(0, 6, 2):
            index = self.hashes[i].bit_by_bit_fast((self.flow_to_bytestream(flow))) % self.M1
            status = self.hashes[i + 1].bit_by_bit_fast((self.flow_to_bytestream(flow))) % 2
            #print i, index, status, self.layers[0][index]
            x = 0
            if self.layers[0][index] & 0x8 != 0:
                x = -1 * (self.layers[0][index] & 0x7)
            else:
                x = self.layers[0][index]
            value1 += status * x if status == 1 else -1 * x
        if value1 < self.d1 * ((1 << (self.bits1 - 1)) - 1):
            return value1
        else:
            for i in range(6, 12, 2):
                x = 0
                index = self.hashes[i].bit_by_bit_fast((self.flow_to_bytestream(flow))) % self.M2
                status = self.hashes[i + 1].bit_by_bit_fast((self.flow_to_bytestream(flow))) % 2
                print i, index, status, self.layers[1][index]
                if self.layers[1][index] & 0x80 != 0:
                    x = -1 * (self.layers[1][index] & 0x7F)
                else:
                    x = self.layers[1][index]
                value2 += status * x if status == 1 else -1 * x
            if value2 < self.d2 * ((1 << (self.bits2 - 1)) - 1):
                return value1 + value2
            else:
                '''
                for i in range(12, self.d + 12):
                    index = self.hashes[i].bit_by_bit_fast((self.flow_to_bytestream(flow))) % self.w
                    values.append(self.registers[i][index])
                print value1, value2, min(values)
                '''
                index = self.hashes[12].bit_by_bit_fast((self.flow_to_bytestream(flow))) % self.w
                return value1 + value2 + self.registers[0][index]

    def decode_registers(self, ground_truth_file="caida_2016_00.pickle"):

        """In the decoding function you were free to compute whatever you wanted.
           This solution includes a very basic statistic, with the number of flows inside the confidence bound.
        """
        f = open("BF.txt", "w")
        self.read_registers()
        flows = pickle.load(open(ground_truth_file, "r"))
        for flow, n_packets in flows.items():
            pred_size = self.get_per_flow_size(flow)
            f.write(str(n_packets) + " " + str(pred_size) + "\n")
        f.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--option', help="controller option can be either update or estimate", type=str, required=False, default="update")
    sw_name = "s1"
    args = parser.parse_args()
    moption = args.option
    controller = BFController(sw_name)
    if args.option == "estimate":
        controller.decode_registers()
    else:
        controller.reset_registers()
