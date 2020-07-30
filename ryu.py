#ryu-manager /media/sf_shared/lab3-tele.py ryu.app.ofctl_rest
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


class ryu(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ryu, self).__init__(*args, **kwargs)
        # self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        k = 2
        h = 2
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = str(hex(datapath.id))[2:].zfill(16)
        self.logger.info("DPID is %s", dpid)

        # hotel switch	
        if int(dpid[13]) == int(1):
            self.logger.info("Core Switch, DPID: %s", dpid)
            for floorCount in range(1, int(k) + 1):
                # db = database, pt = portal, sw = switch
                # sending all inquiries to portal first
                ip = "10.0." + str(floorCount) + ".0" #knows which floor switch to direct pkts to
                mask = "255.255.255.0"
                match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip, mask))
                # ports are not zero indexed
                port = floorCount
                # sending all inquiries to portal first
                action = parser.OFPActionOutput(port, 0)
                self.logger.info("Mapped IP %s to port %d", ip, port)
                self.add_flow(datapath, 500, match, action)

            ip_db = "10.1.1.0"
            ip_pt = "10.2.1.0"
            mask = "255.255.255.0"
            match_db = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip_db, mask))
            match_pt = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip_pt, mask))
            port_db = floorCount + 1
            port_pt = floorCount + 2

            action_db = parser.OFPActionOutput(port_db, 0)
            action_pt = parser.OFPActionOutput(port_pt, 0)
            self.add_flow(datapath, 500, match_db, action_db)
            self.add_flow(datapath, 500, match_pt, action_pt)

            # default gateway/floor switches
        elif int(dpid[15]) <= int(k):
            # directing hosts to internet
            # floor switches to host
            self.logger.info("floor Switch, DPID: %s", dpid)
            for hostCount in range(2, 2 + int(h)):
                ip = "10.0" + "." + dpid[15] + "." + str(hostCount)
                mask = "255.255.255.255"
                match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip, mask))
                port = 1 + hostCount - 2
                action = parser.OFPActionOutput(port, 0)
                self.logger.info("Mapped IP %s to port %d", ip, port)
                self.add_flow(datapath, 500, match, action)

            # directing traffic to hotel switch to portal
            # for suffixCount in range(0, 2 + int(k / 2)):
            #     ip = "10." + dpid[11] + ".0." + str(suffixCount)
            #     mask = "0.0.0.255"
            #     match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(ip, mask))
            #     # port = int((k-2) / 2) + suffixCount  # (k-2)/2 + suffixCount
            #     port = int(k) + 1
            #     action = parser.OFPActionOutput(port, 0)
            #     self.logger.info("Mapped IP %s to port %d", ip, port)
            #     self.add_flow(datapath, 100, match, action)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [actions])]

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_ADD, priority=priority, match=match,
                                instructions=inst)

        datapath.send_msg(mod)
