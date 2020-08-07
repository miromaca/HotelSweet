# sudo mn --custom /media/sf_shared/mininet2.py --topo mytopo
# dpctl dump-flows #CHECKS IF FLOWS ARE ADDED
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController, RemoteController, CPULimitedHost
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
        nat = self.addNode('nat0', cls=NAT, ip=natIP, inNamespace=False)  # default gateway
        self.addLink(core, nat, port1=int(hosts+1)) #port 1 of s1 to access internet
        server = self.addHost("server", ip="10.0.0.253")
        self.addLink(core, server, port1=int(hosts+2), port2=1)

        # creating edge switches and appending them to the edge list
        for floor in range(1, int(k) + 1):
            # agg = self.addSwitch("agSw%s%s" % (j, i), dpid="00:00:00:00:00:%.2d:%.2d:01" % (j, int(k/2)+i))
            edge = self.addSwitch("edSw%s" % floor, dpid="00:00:00:00:00:00:00:%.2d" % floor)
            # print(type(edge))
            # self.aggList.append(agg)
            self.edgeList.append(edge)
            #self.addLink(self.edgeList[floor - 1], core, port1=int(hosts + 2), port2=int(floor))

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

        # add links from floor switches to core switches
        for floorCount in range(1, (int(k) + 1)):
            p1 = int(hosts) + 1
            p2 = floorCount
            self.addLink(self.edgeList[floorCount - 1], self.coreList[0], port1=p1, port2=p2)


def simpleTest():
    # "Create and test a simple network"
    topo = FatTree()
    natSubnet = '10.0.0.0/23'  # restrict ip range of Mininet
    net = Mininet(topo, controller=None, autoSetMacs=True, autoStaticArp=True, host=CPULimitedHost, link=TCLink,
                  ipBase=natSubnet)
    net.addController('controller', controller=RemoteController, ip='127.0.0.1', port=6633, protocols='OpenFlow13')
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
