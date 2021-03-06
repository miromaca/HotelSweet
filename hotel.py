"""
Start with sudo mn --custom lab2.py --topo fattree,4 --controller remote,ip='127.0.0.1',port='6633'

dpctl dump-flows <-- to check flows
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange,dumpNodeConnections
from mininet.node import OVSController, RemoteController, CPULimitedHost
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import Switch, Ryu
import os, logging

logging.basicConfig(filename='./hotelSweet.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Hotel(Topo):
    # Fat tree topology of order k
    
    
    
    def __init__(self, **opts):
        """Init.
            k: Number of floors at the hotel
        """
        k=2
        self.FloorSwList = []
        self.HostList = []
        self.floors = k
        self.hosts = k*2
        self.density = self.hosts/self.floors
        
        super(Hotel, self).__init__(**opts)
        
    def build(self):
        # Build the topology and add links
        self.createHotelSw()
        self.createFloors(self.floors)
        self._addHosts(self.density, self.floors)
        self.createLink()
        
    def _addHosts(self, dens, floorNum):
        logger.debug("Create Hosts")
        
        num = 0
        for x in xrange(1, floorNum+1):
            for y in xrange(2, dens+2):
                num = num + 1
                self.HostList.append(self.addHost(name="h"+str(num), ip="10.0."+str(x)+"."+str(y)))
        
    def createHotelSw(self):
        logger.debug("Create Hotel Switch")
        self.hotelSwitch = self.addSwitch(name="hotelSwitch", dpid="00:00:00:00:00:00:01:00")
        
    def createFloors(self, floorNum):
        logger.debug("Create Floor Switches")
        for x in xrange(1, floorNum+1):
            if x < 10:
                self.FloorSwList.append(self.addSwitch(name="Floor_"+str(x), dpid="00:00:00:00:00:00:00:0"+str(x)))
            elif x >= 10:
                self.FloorSwList.append(self.addSwitch(name="Floor_"+str(x), dpid="00:00:00:00:00:00:00:"+str(x)))
        
    """
    Create links
    """
    
    def createLink(self):
        logger.debug("Create Links")
        logger.debug("Link Hotel to Floors")
        
        logger.debug("Link Floor switches to Hosts")
        for x in xrange(0, self.floors):
            for y in xrange(0, self.density):
                self.addLink(self.FloorSwList[x], self.HostList[self.density * x + y], port1=y+1, port2=1)
    
def simpleTest():

    #"Create and test a simple network"
    topo = Hotel()
    net = Mininet(topo,controller=None, autoSetMacs=True, autoStaticArp=True, host=CPULimitedHost, link=TCLink)
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
    
topos = { 'hotel': ( lambda: simpleTest()) }

