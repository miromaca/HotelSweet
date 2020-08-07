import parser
# ryu-manager /media/sf_shared/tele_lab3_controller.py ryu.app.ofctl_rest

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, arp, ipv4
from ryu.lib.packet import ether_types
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from ryu.ofproto import ether
import ryu.app.ofctl.api
import csv
from operator import attrgetter
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub



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
        # f.close()

    h = 2 #number of hosts per floor
    k = 2 #number
    hotel_check = [0] * len(authentication)
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ryu, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.txList = []

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
                        port = int(k + 1)
                        action = parser.OFPActionOutput(port, 0)
                        self.logger.info("Mapped IP %s to port %d", ip, port)
                        self.add_flow(datapath, 500, match, action)

                    else:
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(ip, mask))
                        serverport = int(h + 2)
                        action = parser.OFPActionOutput(serverport, 0)
                        self.add_flow(datapath, 400, match, action)

            # #surpassing download threshold per host
            # if self.txbytes_edSw1_h12 > 7500:
            #     self.logger.info("Exceeded download Threshold")
            #     match = parser.OFPMatch(eth_type=0x0800, ipv4_src=("10.0.1.2", "255.255.255.255"))
            #     port = int(h + 2)
            #     action = parser.OFPActionOutput(port, 0)
            #     self.add_flow(datapath, 800, match, action)

        # if you're a floor switch
        elif int(dpid[15]) <= int(k):
            self.logger.info("floor switch")
            for hostCount in range(2, 2 + int(h)):
                ip = "10.0" + "." + dpid[15] + "." + str(hostCount)
                mask = "255.255.255.255"
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(ip, mask))
                port = int(h) + 1
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

    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    # def _packet_in_handler(self, ev):
    #     msg = ev.msg
    #     datapath = ev.msg.datapath
    #     k = 2  # no of floors
    #     h = 2  # no of hosts per floor
    #     ofproto = datapath.ofproto
    #     parser = datapath.ofproto_parser
    #     dpid = str(hex(datapath.id))[2:].zfill(16)
    #     pkt = packet.Packet(msg.data)
    #     pkt_ip = pkt.get_protocol(ipv4)
    #     source = pkt_ip.src
    #     # if authorised
    #     if self.authentication[h * (int(source[3]) - 1) + int(source[4]) - 2] == "yes":
    #         match = parser.OFPMatch(eth_type=0x0800, ipv4_src=(source, "255.255.255.255"))
    #         port = int(k + 1)
    #         action = parser.OFPActionOutput(port, 0)
    #         self.logger.info("Mapped IP %s to port %d", source, port)
    #         self.add_flow(datapath, 700, match, action)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        # datapath = "0000000000000001"
        # ofproto = datapath.ofproto
        # parser = datapath.ofproto_parser
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(5)
            for i in self.txList:
                if i > 7500:
                    self.logger.info("Host Exceeded download Threshold")
                # match = parser.OFPMatch(eth_type=0x0800, ipv4_src=("10.0.1.2", "255.255.255.255"))
                # port = int(4)
                # action = parser.OFPActionOutput(port, 0)
                # self.add_flow(datapath, 800, match, action)

    def _request_stats(self, datapath):
        self.logger.info("\n")
        # self.logger.debug('send stats request: %016x\n', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    # def _flow_stats_reply_handler(self, ev):
    #     body = ev.msg.body
    #
    #     self.logger.info('datapath         '
    #                      'in-port  eth-dst           '
    #                      'out-port packets  bytes')
    #     self.logger.info('---------------- '
    #                      '-------- ----------------- '
    #                      '-------- -------- --------')
    #     for stat in sorted([flow for flow in body if flow.priority == 1],
    #                        key=lambda flow: (flow.match['in_port'],
    #                                          flow.match['eth_dst'])):
    #         self.logger.info('%016x %8x %17s %8x %8d %8d',
    #                          ev.msg.datapath.id,
    #                          stat.match['in_port'], stat.match['eth_dst'],
    #                          stat.instructions[0].actions[0].port,
    #                          stat.packet_count, stat.byte_count)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        # self.logger.info('datapath         port     '
        #                  'rx-pkts  rx-bytes rx-error '
        #                  'tx-pkts  tx-bytes tx-error')
        # self.logger.info('---------------- -------- '
        #                  '-------- -------- -------- '
        #                  '-------- -------- --------')
        self.logger.info('datapath           port     '
                         'tx-bytes')
        self.logger.info('---------------- -------- '
                          '--------')
        for stat in sorted(body, key=attrgetter('port_no')):
            #self.logger.info(type(ev.msg.datapath.id))
            if ev.msg.datapath.id != int(256):
                if stat.port_no != 3:
                # self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                #                  ev.msg.datapath.id, stat.port_no,
                #                  stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                #                  stat.tx_packets, stat.tx_bytes, stat.tx_errors)
                    self.logger.info('%016x %8x %8d', ev.msg.datapath.id, stat.port_no, stat.tx_bytes)
                    if stat.port_no == 1:
                        if ev.msg.datapath.id == 1:
                            if stat.tx_bytes > 7500:
                                #add flows for each switch for matching port, action drop if surpassed threshold
                                #self.txbytes_edSw1_h12 = stat.tx_bytes
                                self.txList.append(stat.tx_bytes)
                        elif ev.msg.datapath.id == 2:
                            #self.txbytes_edSw1_h13 = stat.tx_bytes
                            self.txList.append(stat.tx_bytes)
                    elif stat.port_no == 2:
                        if ev.msg.datapath.id == 1:
                            #self.txbytes_edSw2_h22 = stat.tx_bytes
                            self.txList.append(stat.tx_bytes)
                        elif ev.msg.datapath.id == 2:
                            #self.txbytes_edSw2_h23 = stat.tx_bytes
                            self.txList.append(stat.tx_bytes)
    # @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    # def switch_features_handler(self, ev):
    #     msg = ev.msg
    #
    #     self.logger.debug('OFPSwitchFeatures received: '
    #                       'datapath_id=0x%016x n_buffers=%d '
    #                       'n_tables=%d auxiliary_id=%d '
    #                       'capabilities=0x%08x',
    #                       msg.datapath_id, msg.n_buffers, msg.n_tables,
    #                       msg.auxiliary_id, msg.capabilities)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [actions])]

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_ADD, priority=priority, match=match,
                                instructions=inst)

        datapath.send_msg(mod)
