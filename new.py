# sudo mn --custom /media/sf_shared/mininet.py --topo mytopo
# dpctl dump-flows #CHECKS IF FLOWS ARE ADDED
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController, RemoteController, CPULimitedHost, Ryu
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.link import Intf
from mininet.nodelib import NAT
import sys
import getopt



# k = 4

class FatTree(Topo):
    "Simple topology example."

    # net = Mininet(topo=None, controller=None, autoSetMacs=True, autoStaticArp=True, host=CPULimitedHost, link=TCLink)
    def __init__(self):
        # global k
        "Create custom topo."
        self.coreList = []
        #self.natList = []
        self.edgeList = []
        self.hostList = []

        # Initialize topology
        Topo.__init__(self)

        k = 2
        hosts = 2  # no of hosts per floor
        # creating core switches and appending them to core list
        # for i in range(0, int((k/2)**2)):
        # core = self.addSwitch("crSw%s" % i, dpid="00:00:00:00:00:%.2d:%.2d:01" % (int(k),i))
        core = self.addSwitch("hotelsw", dpid="00:00:00:00:00:00:01:00")
        self.coreList.append(core)

        natIP = '10.0.0.254'
        nat = self.addNode('nat0', cls=NAT, ip=natIP, inNamespace=False, inetIntf="eth2", subnet='10.0.0.0/8')  # default gateway
        internet = self.addHost("internet", ip="10.1.0.2")
        self.addLink(internet, nat, port1=1, port2=2)
        #s1 = self.addSwitch('s1', dpid="00:00:00:00:00:01:00:00")
        self.addLink(core, nat, port1=int(k+1), port2=1) #port 1 of s1 to access internet
        #self.addLink(core, s1, port1=int(hosts+1), port2=2)

        # creating edge switches and appending them to the edge list
        for floor in range(1, int(k) + 1):
            # agg = self.addSwitch("agSw%s%s" % (j, i), dpid="00:00:00:00:00:%.2d:%.2d:01" % (j, int(k/2)+i))
            edge = self.addSwitch("edSw%s" % floor, dpid="00:00:00:00:00:00:00:%.2d" % floor)
            # print(type(edge))
            # self.aggList.append(agg)
            self.edgeList.append(edge)
            #self.addLink(self.edgeList[floor - 1], core, port1=int(hosts + 2), port2=int(floor))
            #############
            # def build(self, n=2, **_kwargs):
            #     # set up inet switch
            #     inetSwitch = self.addSwitch('s0')
            #     # add inet host
            #     inetHost = self.addHost('h0')
            #     self.addLink(inetSwitch, inetHost)
            #  #add local nets
            # for i in irange(1, n):
            #     inetIntf = 'nat%d-eth0' % i
            #     localIntf = 'nat%d-eth1' % i
            #     localIP = '192.168.%d.1' % i
            #     localSubnet = '192.168.%d.0/24' % i
            #     natParams = {'ip': '%s/24' % localIP}
            #     # add NAT to topology
            #     nat = self.addNode('nat%d' % i, cls=NAT, subnet=localSubnet,
            #                        inetIntf=inetIntf, localIntf=localIntf)
            #     switch = self.addSwitch('s%d' % i)
            #     # connect NAT to inet and local switches
            #     self.addLink(nat, inetSwitch, intfName1=inetIntf)
            #     self.addLink(nat, switch, intfName1=localIntf, params1=natParams)
            #     # add host and connect to local switch
            #     host = self.addHost('h%d' % i,
            #                         ip='192.168.%d.100/24' % i,
            #                         defaultRoute='via %s' % localIP)
            #     self.addLink(host, switch)

        # create hosts
        for floor in range(1, int(k) + 1):
            for hostCount in range(2, 2 + int(hosts)):
                host = self.addHost("h%s%s" % (floor, hostCount),
                                    ip="10.0.%s.%s" % (floor, hostCount))  # """, defaultRoute='via ' + natIP""")
                self.hostList.append(host)

        # add links from hosts to edge switches
        # loop through edge switches
        for i in range(0, int(k)):
            # loop through hosts
            for j in range(0, int(hosts)):
                self.addLink(self.hostList[int(k) * (i) + j], self.edgeList[i], port1=1, port2=j + 1)

        # #add links from edge switches to aggregation switches
        # #loop through pods
        # for podCount in range(0, int(k)):
        #     p1 = int(k / 2)
        #     #loop through agg switches
        #     for aggCount in range(podCount*int(k/2), podCount*int(k/2) + (int(k/2))):
        #         p1 = p1 + 1
        #         p2 = 1
        #         for edgeCount in range(podCount*int(k/2), podCount*int(k/2) + (int(k/2))):
        #             self.addLink(self.edgeList[edgeCount], self.aggList[aggCount], port1=p1, port2=p2)
        #             p2 = p2 + 1

        # add links from floor switches to core switches
        for floorCount in range(1, (int(k) + 1)):
            p1 = int(hosts) + 1
            p2 = floorCount
            self.addLink(self.edgeList[floorCount - 1], self.coreList[0], port1=p1, port2=p2)


def simpleTest():
    # "Create and test a simple network"
    topo = FatTree()
    natSubnet = '10.0.0.0/8'  # restrict ip range of Mininet
    #natSubnet = '10.0/8'
    net = Mininet(topo, controller=None, autoSetMacs=True, autoStaticArp=True, host=CPULimitedHost, link=TCLink,
                  ipBase=natSubnet)
    #net.addController('controller', controller=RemoteController, ip='127.0.0.1', port=6633, protocols='OpenFlow13')
    net.addController('controller', controller=Ryu, ryuArgs='/media/sf_shared/tele_lab3_controller.py ryu.app.ofctl_rest', protocols='OpenFlow13')
    # net.addNAT().configDefault()
    # for ed in range(0, 2):
    #     Intf("edSw%s-eth4" % (ed + 1), node=net.topo.edgeList[ed])
    net.start()

    # Dumping Network Statistics
    print("Dumping Host Connections")
    dumpNodeConnections(net.hosts)
    print("Dumping Switches Connections")
    dumpNodeConnections(net.switches)
    print("Testing Network Connectivity")

    # Showing Mininet CLI
    CLI(net)

    # Stopping Network Topology
    print("Stopping Network Topology")
    net.stop()


topos = {'mytopo': (lambda: simpleTest())}
