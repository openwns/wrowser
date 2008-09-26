import random
random.seed(42)
import wns.WNS
import wns.Node
import rise.Mobility
import rise.scenario.ScenarioBuilder
import rise.scenario.Nodes
import ofdmaphy.Transmitter
import ofdmaphy.Receiver
import ofdmaphy.Station
import ofdmaphy.OFDMAPhy
from openwns.evaluation import *

class BS(wns.Node.Node):
    mobility = None
    sender = None

    def __init__(self, name, mobility, powerPerSubBand):
        super(BS, self).__init__(name)
        self.name = self.name + str(self.id)

        self.mobility = rise.Mobility.Component(self,
                                                "Mobility Component",
                                                mobility)
        self.mobility.mobility.logger.enabled=False
        self.sender = ofdmaphy.Station.Sender(self, name, [ofdmaphy.Transmitter.TransmitterDropIn()])
        self.sender.txPower = powerPerSubBand

class MS(wns.Node.Node):
    mobility = None
    scanner = None

    def __init__(self, name, mobility):
        super(MS, self).__init__(name)
        self.name = self.name + str(self.id)
        self.mobility = rise.Mobility.Component(self,
                                                "Mobility Component",
                                                mobility)
        self.mobility.mobility.logger.enabled=False
        self.scanner = ofdmaphy.Station.Scanner(self, name, [ofdmaphy.Receiver.ReceiverDropIn()])
        self.scanner.rxpProbeName = "Scanner_RxPwr"
        self.scanner.sinrProbeName = "Scanner_SINR"

class ScannerScenarioBuilder(rise.scenario.ScenarioBuilder.IScenarioBuilder):

    def __init__(self, maxSimTime, scenarioSize, tileWidth, powerPerSubBand):
        self.maxSimTime = maxSimTime
        self.scenarioSize = scenarioSize
        print self.scenarioSize
        self.powerPerSubBand = powerPerSubBand
        self.rxpProbeName = "Scanner_RxPwr"
        self.sinrProbeName = "Scanner_SINR"
        self.numBS = 0
        self.tileWidth = tileWidth

        self.simulator = wns.WNS.WNS()
        self.simulator.maxSimTime = maxSimTime
        self.simulator.outputStrategy = wns.WNS.OutputStrategy.DELETE

        riseConfig = self.simulator.modules.rise

        ofdmaPhyConfig = self.simulator.modules.ofdmaPhy
        ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('OFDMA')
        ofdmaPhySystem.Scenario = rise.Scenario.Scenario(0.0, 0.0)
        ofdmaPhyConfig.systems.append(ofdmaPhySystem)
        
    def getSimulator(self):
        return self.simulator

    def createBaseStation(self, rap):
        noMobility = rise.Mobility.No(rap.position)
        self.simulator.nodes.append( BS("BS", noMobility, self.powerPerSubBand) )
        self.numBS += 1

    def createRelayEnhancedCell(self, rec):
        pass

    def createUserTerminal(self):
        #aMobility = rise.Mobility.BrownianRect([self.scenarioSize[0], self.scenarioSize[1], self.scenarioSize[2], self.scenarioSize[3]])
        aMobility = self.createPointByPointMobility(self.scenarioSize[0], self.scenarioSize[2], self.scenarioSize[1], self.scenarioSize[3], 100.0, None, 1)
        self.simulator.nodes.append( MS("MS", aMobility) )

    def finalizeScenario(self):
        self.createUserTerminal()
        self.installDefaultProbes()

    def createPointByPointMobility(self, xMin, xMax, yMin, yMax, maxSimTime, mobilityObstructions=None, scale=1):
        t = 0.0
        inObstacle = False
        timestep = float(maxSimTime)/((xMax-xMin)*(yMax-yMin)* scale * scale)
        mobility = rise.Mobility.EventList(wns.Position(0,0,0))
        for ii in xrange(int(xMax-xMin)*scale):
            for jj in xrange(int(yMax-yMin)*scale):
                waypoint = [float(ii)/scale + xMin, float(jj)/scale + yMin, 0]
                # check if position is within an obstacle
                #if mobilityObstructions is not None:
                #    for obstacle in mobilityObstructions:
                #        if obstacle.containsPoint(waypoint):
                #            inObstacle = True
                #            break
                
                #    if (mobilityObstructions is None or not inObstacle):
                print "Adding waypoint at t=%s" % str(t)
                mobility.addWaypoint(t, wns.Position(float(ii)/scale + xMin, float(jj)/scale + yMin, 1.5))

                #inObstacle = False
                t += timestep
        return mobility

    def installDefaultProbes(self):
        # Create a table generator for the evaluation
        width = self.scenarioSize[2] - self.scenarioSize[0]
        height = self.scenarioSize[3] - self.scenarioSize[1]
        table = Table(axis1 = 'rise.scenario.mobility.x', minValue1 = self.scenarioSize[0], maxValue1 = self.scenarioSize[2], resolution1 = width,
                      axis2 = 'rise.scenario.mobility.y', minValue2 = self.scenarioSize[1], maxValue2 = self.scenarioSize[3], resolution2 = height,
                      values = ['mean', 'max', 'trials'],
                      formats = ['MatlabReadable']
                      )

        node = openwns.evaluation.createSourceNode(self.simulator, self.rxpProbeName)
        node.appendChildren(table)
        sep = node.appendChildren(Separate(by = 'BSID', forAll = range(0, self.numBS), format = "BSID%d"))
        sep.appendChildren(PDF(name = self.rxpProbeName,
                               description = 'Received Power [dBm]',
                               minXValue = -170,
                               maxXValue = -40,
                               resolution = 130))
        sep.appendChildren(table)

        node = openwns.evaluation.createSourceNode(self.simulator, self.sinrProbeName)
        node.appendChildren(table)
        sep = node.appendChildren(Separate(by = 'BSID', forAll = range(0, self.numBS), format = "BSID%d"))
        sep.appendChildren(PDF(name = self.sinrProbeName,
                               description = 'SINR [dB]',
                               minXValue = -30,
                               maxXValue = 30,
                               resolution = 60))
        sep.appendChildren(table)

