def calculate_are(real_flows, estimated_flows):
    real_data = []
    estimated_data = []
    for flow, size in real_flows.items():
        es_size = estimated_flows[flow]
        real_data.append(size)
        estimated_data.append(es_size)
    sumOfRe = 0.0
    num_flows = 0
    for i in range(len(real_data)):
        real_ = real_data[i]
        estimated_ = estimated_data[i]
        if estimated_ == 0:
            estimated_ = 1
        relativeError = (estimated_ - real_) * 1.0 / real_
        relativeError = abs(relativeError)
        num_flows += 1
        sumOfRe += relativeError

    return round(sumOfRe/num_flows, 2)

