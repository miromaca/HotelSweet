# sudo mn --custom /media/sf_shared/mininet.py --topo mytopo
# dpctl dump-flows #CHECKS IF FLOWS ARE ADDED
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController, RemoteController, CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
import sys
import getopt


# k = 4

class FatTree(Topo):
    "Simple topology example."

    def __init__(self):
        # global k
        "Create custom topo."
        self.coreList = []
        # self.aggList = []
        self.edgeList = []
        self.hostList = []

        # Initialize topology
        Topo.__init__(self)

        k = 2
        # creating core switches and appending them to core list
        # for i in range(0, int((k/2)**2)):
        # core = self.addSwitch("crSw%s" % i, dpid="00:00:00:00:00:%.2d:%.2d:01" % (int(k),i))
        core = self.addSwitch("hotelsw", dpid="00:00:00:00:00:00:01:00")
        self.coreList.append(core)

        # creating edge &  switches and appending them to the agg & edge list
        for floor in range(1, int(k) + 1):
            # agg = self.addSwitch("agSw%s%s" % (j, i), dpid="00:00:00:00:00:%.2d:%.2d:01" % (j, int(k/2)+i))
            edge = self.addSwitch("edSw%s" % floor, dpid="00:00:00:00:00:00:00:%.2d" % floor)
            # self.aggList.append(agg)
            self.edgeList.append(edge)

        # create hosts
        hosts = 2  # no of hosts per floor
        for floor in range(1, int(k)+1):
            for hostCount in range(2, 2 + int(hosts)):
                host = self.addHost("h%s%s" % (floor, hostCount), ip="10.0.%.2d.%.2d" % (floor, hostCount))
                self.hostList.append(host)

        # add links from hosts to edge switches
        #loop through edge switches
        for i in range(0, int(k)):
            #loop through hosts
            for j in range(0, int(hosts)):
                self.addLink(self.hostList[int(k)*(i)+j], self.edgeList[i], port1=1, port2=j+1)

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


        #add links from floor switches to core switches
        for floorCount in range(1, (int(k)+1)):
            p1 = int(hosts) + 1
            p2 = floorCount
            self.addLink(self.edgeList[floorCount - 1], self.coreList[0], port1=p1, port2=p2)


def simpleTest():
    # "Create and test a simple network"
    topo = FatTree()
    net = Mininet(topo, controller=None, autoSetMacs=True, autoStaticArp=True, host=CPULimitedHost, link=TCLink)
    net.addController('controller', controller=RemoteController, ip='127.0.0.1', port=6633, protocols='OpenFlow13')
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
