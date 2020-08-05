import parser
# ryu-manager /media/sf_shared/tele_lab3_controller.py ryu.app.ofctl_rest

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, arp, ipv4
from ryu.lib.packet import ether_types
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from ryu.ofproto import ether
import ryu.app.ofctl.api
import csv


# csv database file needs to be in same folder as topo and controller
class ryu(app_manager.RyuApp):
    with open('/media/sf_shared/Passwords.csv') as f:
        csv_f = csv.reader(f)
        content = []
        authentication = []
        for row in csv_f:
            content.append(row)

        for x in range(0, len(content)):
            authentication.append(content[x][2])
        #f.close()

    h = 2
    k = 2
    hotel_check = [0] * len(authentication)
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ryu, self).__init__(*args, **kwargs)
        # self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        k = 2  # no of floors
        h = 2  # no of hosts per floor
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = str(hex(datapath.id))[2:].zfill(16)
        self.logger.info("DPID is %s", dpid)




        # if you're the hotel switch
        if int(dpid[13]) == int(1):
            self.logger.info("hotel Switch, DPID: %s", dpid)

            for floorCount in range(1, int(k) + 1):
                # if(authentication[floorCount] == 'no'):
                ip = "10.0." + str(floorCount) + ".0"  # knows which floor switch to direct pkts to
                mask = "255.255.255.0"
                match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip, mask))
                # ports are not zero indexed
                port = floorCount
                # sending all inquiries to portal first
                action = parser.OFPActionOutput(port, 0)
                self.logger.info("Mapped IP %s to port %d", ip, port)
                self.add_flow(datapath, 500, match, action)

                for hostCount in range(2, 2 + int(h)):
                    ip = "10.0." + str(floorCount) + "." + str(hostCount)
                    mask = "255.255.255.255"
                    if self.authentication[h * (floorCount - 1) + hostCount - 2] == 'yes':
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(ip, mask))
                        port = 3  # make dynamic later
                        action = parser.OFPActionOutput(port, 0)
                        self.logger.info("Mapped IP %s to port %d", ip, port)
                        self.add_flow(datapath, 500, match, action)

                    else:
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(ip, mask))
                        action = parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, 0)
                        self.add_flow(datapath, 600, match, action)

        # if you're a floor switch
        elif int(dpid[15]) <= int(k):
            self.logger.info("floor switch")
            for hostCount in range(2, 2 + int(h)):
                ip = "10.0" + "." + dpid[15] + "." + str(hostCount)
                mask = "255.255.255.255"
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(ip, mask))
                port = int(h)+ 1
                action = parser.OFPActionOutput(port, 0)
                self.logger.info("Mapped IP %s to port %d", ip, port)
                self.add_flow(datapath, 500, match, action)

                match = parser.OFPMatch(in_port=1)
                action = parser.OFPActionOutput(port, 0)
                self.add_flow(datapath, 100, match, action)

            # allowing for hosts to ping each other
            for suffixCount in range(2, 2 + int(h)):
                ip = "0.0.0." + str(suffixCount)
                mask = "0.0.0.255"
                match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip, mask))
                port = suffixCount - 1
                action = parser.OFPActionOutput(port, 0)
                self.logger.info("Mapped IP %s to port %d", ip, port)
                self.add_flow(datapath, 700, match, action)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = ev.msg.datapath
        k = 2  # no of floors
        h = 2  # no of hosts per floor
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = str(hex(datapath.id))[2:].zfill(16)
        pkt = packet.Packet(msg.data)
        pkt_ip = pkt.get_protocol(ipv4)
        source = pkt_ip.src
        #if authorised
        if self.authentication[h * (int(source[3]) - 1) + int(source[4]) - 2] == "yes":
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(source, "255.255.255.255"))
            port = 3  # make dynamic later
            action = parser.OFPActionOutput(port, 0)
            self.logger.info("Mapped IP %s to port %d", source, port)
            self.add_flow(datapath, 700, match, action)


    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [actions])]

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_ADD, priority=priority, match=match,
                                instructions=inst)

        datapath.send_msg(mod)