/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#include "headers.p4"
#include "parsers.p4"

/* CONSTANTS */
#define SKETCH_BUCKET_LENGTH 50000
#define SKETCH_CELL_BIT_WIDTH 32
#define D1 3
#define D2 3
#define bits1 4
#define bits2 8
#define threshold1 8
#define threshold2 128
#define M1 500000
#define M2 100000

#define SKETCH_REGISTER(num) register<bit<SKETCH_CELL_BIT_WIDTH>>(SKETCH_BUCKET_LENGTH) sketch##num

#define SKETCH_COUNT(num, algorithm) hash(meta.index_sketch##num, HashAlgorithm.algorithm, (bit<16>)0, {hdr.ipv4.srcAddr}, (bit<32>)SKETCH_BUCKET_LENGTH);\
 sketch##num.read(meta.value_sketch##num, meta.index_sketch##num); \
 meta.value_sketch##num = meta.value_sketch##num +1; \
 sketch##num.write(meta.index_sketch##num, meta.value_sketch##num)

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

		register<bit<bits1>>(M1) L1;
		register<bit<bits2>>(M2) L2;
    register<bit<SKETCH_CELL_BIT_WIDTH>>(SKETCH_BUCKET_LENGTH) sketch0;

    action drop() {
        mark_to_drop(standard_metadata);
    }

		// Here we set the row of cm-sketch to 1
    /*
    action sketch_count(){
        SKETCH_COUNT(0, crc32_custom);
    }*/

   action set_egress_port(bit<9> egress_port){
        standard_metadata.egress_spec = egress_port;
    }

    table forwarding {
        key = {
            standard_metadata.ingress_port: exact;
        }
        actions = {
            set_egress_port;
            drop;
            NoAction;
        }
        size = 64;
        default_action = drop;
    }

    apply {
        //apply sketch
        if (hdr.ipv4.isValid()){
           	random(meta.random_value, 0, D1 - 1);
						// choose the mapped physical register from BF
            if (meta.random_value == 0) {
                hash(meta.counter_index1, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>)M1);
                hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>) 2);
            } else {
                if (meta.random_value == 1) {
                    hash(meta.counter_index1, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>)M1);
                    hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>) 2);
                } else {
                    hash(meta.counter_index1, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>)M1);
                    hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>) 2);
                }
            }
						//hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr, meta.counter_index1}, (bit<32>) 2);
						L1.read(meta.counter_value1, meta.counter_index1);
						meta.bingo = 1;
            if (meta.op == 1) { // positive direction
            		if (meta.counter_value1 & 0x8 == 0) { // positive counter
										if (meta.counter_value1 < threshold1 - 1) {
												meta.counter_value1 = meta.counter_value1 + 1; // add counter without overflow
                    		L1.write(meta.counter_index1, meta.counter_value1);
                    		meta.bingo = 0;
										}
                } else { // negative counter
										if (meta.counter_value1 != 0xF) { // sub counter without overflow
												if (meta.counter_value1 != 0x9) { // sub counter not equals zero (0x1000)
														meta.counter_value1 = meta.counter_value1 - 1;
                        		L1.write(meta.counter_index1, meta.counter_value1);
                        		meta.bingo = 0;
												} else { // set counter to zero when 0x1001
														meta.counter_value1 = 0;
                            L1.write(meta.counter_index1, meta.counter_value1);
                            meta.bingo = 0;
                        }
										}
								}
            } else { // negative direction
								if (meta.counter_value1 & 0x8 == 0) { // postive counter
										if (meta.counter_value1 < threshold1 - 1) { // sub counter without overflow
												if (meta.counter_value1 != 0) {
														meta.counter_value1 = meta.counter_value1 - 1;
                        		L1.write(meta.counter_index1, meta.counter_value1);  // sub counter not equals zero
                        		meta.bingo = 0;
												} else {
														meta.counter_value1 = 0x9;  // set counter to 0x1001 (-1)
														L1.write(meta.counter_index1, meta.counter_value1);
                            meta.bingo = 0;
												}
										}
								} else { // negative counter
										if (meta.counter_value1 != 0xF) { // add counter without overflow
												meta.counter_value1 = meta.counter_value1 + 1;
												L1.write(meta.counter_index1, meta.counter_value1);
                        meta.bingo = 0;
										}
								}
            }
						if (meta.bingo == 1) {
								// Enter to the second layer of Bounce filter
								random(meta.random_value, 0, D2 - 1);
                if (meta.random_value == 0) {
                    hash(meta.counter_index2, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>)M2);
                    hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>) 2);
                } else {
                    if (meta.random_value == 1) {
                        hash(meta.counter_index2, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>)M2);
                        hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>) 2);
                    } else {
                        hash(meta.counter_index2, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>)M2);
                        hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr}, (bit<32>) 2);
                    }
                }
								//hash(meta.op, HashAlgorithm.crc32_custom, (bit<16>) 0, {hdr.ipv4.srcAddr, meta.counter_index2}, (bit<32>) 2);
								L2.read(meta.counter_value2, meta.counter_index2);
								if (meta.op == 1) {
										if (meta.counter_value2 & 0x80 == 0) {
												if (meta.counter_value2 < threshold2 - 1) {
                        		meta.counter_value2 = meta.counter_value2 + 1;
                        		L2.write(meta.counter_index2, meta.counter_value2);
                        		meta.bingo = 0;
                    		}
										} else {
												if (meta.counter_value2 != 0xFF) {
                        		if (meta.counter_value2 != 0x81) {
                            		meta.counter_value2 = meta.counter_value2 - 1;
                            		L2.write(meta.counter_index2, meta.counter_value2);
                            		meta.bingo = 0;
                        		} else {
                            		meta.counter_value2 = 0;
                            		L2.write(meta.counter_index2, meta.counter_value2);
                            		meta.bingo = 0;
                        		}
                    		}
										}
								} else {
										if (meta.counter_value2 & 0x80 == 0) {
                    		if (meta.counter_value2 < threshold2 - 1) {
                        		if (meta.counter_value2 != 0) {
                            		meta.counter_value2 = meta.counter_value2 - 1;
                            		L2.write(meta.counter_index2, meta.counter_value2);
                            		meta.bingo = 0;
                        		} else {
                            		meta.counter_value2 = 0x81;
                            		L2.write(meta.counter_index2, meta.counter_value2);
                            		meta.bingo = 0;
                        		}
                        }
                    } else {
												if (meta.counter_value2 != 0xFF) {
														meta.counter_value2 = meta.counter_value2 + 1;
														L2.write(meta.counter_index2, meta.counter_value2);
                            meta.bingo = 0;
												}
										}
								}								

								// Enter to the cm-sketch
								if (meta.bingo == 1) {
										//sketch_count();
                    hash(meta.index_sketch0, HashAlgorithm.crc32_custom, (bit<16>)0, {hdr.ipv4.srcAddr}, (bit<32>)SKETCH_BUCKET_LENGTH);
               			sketch0.read(meta.value_sketch0, meta.index_sketch0);
										meta.value_sketch0 = meta.value_sketch0 + 1;
										sketch0.write(meta.index_sketch0, meta.value_sketch0);
								}
						}
        }
        forwarding.apply();
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
