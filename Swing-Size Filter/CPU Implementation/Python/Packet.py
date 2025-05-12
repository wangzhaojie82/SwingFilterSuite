

class Packet:
    def __init__(self, id, source_IP, destination_IP):
        self.ID = id # unique id of each packet
        self.SIP = source_IP
        self.DIP = destination_IP
        self.flow_label = self.SIP # source IP as the flow label