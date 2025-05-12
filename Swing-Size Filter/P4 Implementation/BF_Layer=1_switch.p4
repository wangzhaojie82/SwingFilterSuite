/* -*- P4_16 -*- */
#include<core.p4>
#if __TARGET_TOFINO__ == 2
#include<t2na.p4>
#else
#include<tna.p4>
#endif
#define M1 65536
#define W  65536
#define b1 8
#define T1 255
#define median1 127

const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t{
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<1>  cwr;
    bit<1>  ece;
    bit<1>  urg;
    bit<1>  ack;
    bit<1>  psh;
    bit<1>  rst;
    bit<1>  syn;
    bit<1>  fin;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

struct egress_headers_t {}
struct egress_metadata_t {}

struct hash_info_t{
	bit<16> counter_index1;
	bit<b1> counter_value1;
	bit<1> random_value;
	bit<1> op;
	bit<16> sketch_index;
	bit<1> bingo;
}

struct metadata{
	hash_info_t hash_info;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    tcp_t   tcp;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                out metadata meta,
                out ingress_intrinsic_metadata_t ig_intr_md) {

    state start {
        packet.extract(ig_intr_md);
		packet.advance(PORT_METADATA_SIZE);
		transition parse_ethernet;
    }
	
	state parse_ethernet {
		packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType){
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
	}
	
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol)
        {
            (bit<8>) 6 : parse_tcp;
            default : accept;
        }
    }

    state parse_tcp{
        packet.extract(hdr.tcp);
        transition accept;
    }

}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  in ingress_intrinsic_metadata_t ig_intr_md,
				  in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
				  inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
				  inout ingress_intrinsic_metadata_for_tm_t ig_tm_md
					) {
	// packet hash function
	CRCPolynomial<bit<32>>(coeff=0x04C11DB7,reversed=true, msb=false, extended=false, init=0xFFFFFFFF, xor=0xFFFFFFFF) crc0;
	
	// hash functions in L1
	CRCPolynomial<bit<32>>(coeff=0xF23D4780,reversed=true, msb=false, extended=false, init=0xFFFFFFFF, xor=0xFFFFFFFF) crc1;
	CRCPolynomial<bit<32>>(coeff=0x8164DDC2,reversed=true, msb=false, extended=false, init=0xFFFFFFFF, xor=0xFFFFFFFF) crc2;
	
	// hash function in Count-min sketch
	CRCPolynomial<bit<32>>(coeff=0x53ABD3C2,reversed=true, msb=false, extended=false, init=0xFFFFFFFF, xor=0xFFFFFFFF) crc6;
	
	Register<bit<b1>, bit<16>>(M1, median1) L1;
	Register<bit<32>, bit<32>>(W) sketch;
	
	Hash<bit<1>>(HashAlgorithm_t.CUSTOM, crc0) hash00;
	
	Hash<bit<16>>(HashAlgorithm_t.CUSTOM, crc1) hash01;
	Hash<bit<1>>(HashAlgorithm_t.CUSTOM, crc2) hash02;
	
	Hash<bit<16>>(HashAlgorithm_t.CUSTOM, crc6) hash_sketch;
	
	RegisterAction<bit<b1>, bit<16>, bit<b1>>(L1) L1_alu_write =  {
		void apply(inout bit<b1> register_data, out bit<b1> result) {
			if (meta.hash_info.op == 0) {
				register_data = register_data |-| 1;
			} else {
				register_data = register_data |+| 1;
			}
			result = register_data;
		}
	};
	
	/*
		count-min sketch
	*/
	RegisterAction<bit<32>, bit<16>, bit<32>>(sketch) sketch_update =  {
		void apply(inout bit<32> register_data, out bit<32> result) {
			register_data = register_data + 1;
			result = register_data;
		}
	};
	
	action hash_L1 () {
		meta.hash_info.random_value = hash00.get({hdr.ipv4.srcAddr, hdr.ipv4.dstAddr});
		meta.hash_info.counter_index1 = hash01.get({hdr.ipv4.srcAddr, meta.hash_info.random_value});
		meta.hash_info.op = hash02.get({hdr.ipv4.srcAddr, meta.hash_info.counter_index1});
	}
	
	@pragma stage 0
	table hash_L1_table {
		actions = {
			hash_L1;
		}
		size = 1;
		const default_action = hash_L1();
	}
	
	action L1_cal () {
		meta.hash_info.counter_value1 = L1_alu_write.execute(meta.hash_info.counter_index1);
	}
	@pragma stage 0
	table L1_cal_table {
		actions = {
			L1_cal;
		}
		size = 1;
		const default_action = L1_cal();
	}
	
	/*
		Basic forwarding
	*/
    action drop() {
        ig_dprsr_md.drop_ctl = 1;
    }
	
    action ipv4_forward(egressSpec_t port) {
	    ig_tm_md.ucast_egress_port = port;
    }
	
	@pragma stage 0
    table ipv4_lpm {
        key = {
		    hdr.ipv4.dstAddr: lpm;
        }

        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }

        size = 32;

        default_action = NoAction();
    }

    apply {
        //only if IPV4 the rule is applied. Therefore other packets will not be forwarded.
        if (hdr.ipv4.isValid()){
			hash_L1_table.apply();
			L1_cal_table.apply();
			if (meta.hash_info.counter_value1 == 0 || meta.hash_info.counter_value1 == T1) {
				meta.hash_info.sketch_index = hash_sketch.get({hdr.ipv4.srcAddr});
				sketch_update.execute(meta.hash_info.sketch_index);
			}
			ipv4_lpm.apply();
        }
    }
}

control IngressDeparser(packet_out packet,
	inout headers hdr,
	in metadata meta,
	in ingress_intrinsic_metadata_for_deparser_t ig_dprtr_md)
{
	apply{
		packet.emit(hdr);
	}
}
/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/
parser EgressParser(packet_in packet,
	out egress_headers_t hdr,
	out egress_metadata_t meta,
	out egress_intrinsic_metadata_t eg_intr_md)
{
	state start{
		packet.extract(eg_intr_md);
		transition accept;
	}
}

control Egress(inout egress_headers_t hdr,
				inout egress_metadata_t meta,
				in egress_intrinsic_metadata_t eg_intr_md,
				in egress_intrinsic_metadata_from_parser_t eg_prsr_md,
				inout egress_intrinsic_metadata_for_deparser_t eg_dprsr_md,
				inout egress_intrinsic_metadata_for_output_port_t eg_oport_md) 
{
    apply {  }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control EgressDeparser(packet_out packet, 
						inout egress_headers_t hdr, 
						in egress_metadata_t meta, 
						in egress_intrinsic_metadata_for_deparser_t eg_dprsr_md) {
    apply {
        //parsed headers have to be added again into the packet.
		packet.emit(hdr);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
Pipeline(
MyParser(),
MyIngress(),
IngressDeparser(),
EgressParser(),
Egress(),
EgressDeparser()
) pipe;

Switch(pipe) main;