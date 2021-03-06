###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2007
# Chair of Communication Networks (ComNets)
# Kopernikusstr. 16, D-52074 Aachen, Germany
# phone: ++49-241-80-27910,
# fax: ++49-241-80-22242
# email: info@openwns.org
# www: http://www.openwns.org
# _____________________________________________________________________________
#
# openWNS is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 2 as published by the
# Free Software Foundation;
#
# openWNS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

"""Read campaign from database.
"""
import os.path
import Database as db
import Probe
import Representations

class ProbeReader:
    """Reads a probe from the database.

    To be used as 'source' for 'Representations.Probe'.
    """
    def __init__(self, simId, probeName, probeClass, dbClass):
        self.simId = simId
        self.probeName = probeName
        self.probeClass = probeClass
        self.dbClass = dbClass

    def getData(self):
        return list(self.dbClass.select(db.sqlobject.AND(self.dbClass.q.scenarioID == db.Scenario.Scenario.q.id,
                                                         db.Scenario.Scenario.q.id == self.simId,
                                                         self.dbClass.q.altName == self.probeName)))[0]

    def getName(self):
        return self.probeName

class ScenarioReader:
    """Reads a scenario from the database.

    To be used as 'source' for 'Representations.Scenario'.
    """
    def __init__(self, simId):
        self.simId = simId

    def getProbes(self):
        probes = {}
        for (probeTable, probeClass) in [(db.ProbeDB.PDF, Probe.PDFProbe), (db.ProbeDB.LogEval, Probe.LogEvalProbe), (db.ProbeDB.Moments, Probe.MomentsProbe)]:
             selectObj = db.sqlbuilder.Select([probeTable.q.altName], probeTable.q.scenarioID == self.simId)
             sqlRepr = db.getConnection().sqlrepr(selectObj)
             try:
                 probeNames = db.getConnection().queryAll(sqlRepr)
             except:
                 probeNames = []
             for probeName in probeNames:
                 probeInstance = Representations.Probe(ProbeReader(self.simId, probeName[0], probeClass, probeTable))
                 probes[probeName[0]] = probeInstance
        return probes

class CampaignReader:
    """Reads a campaign from a database.

    CampaignReader will call back to 'paramSelectUI.do()' to permit interactive
    selection of the simulation parameters from all columns in the database.
    All non-simulation-parameter columns are passed as deselectedColumns, as the
    simulation parameter names are stored in the database.
    """
    def __init__(self, location, paramSelectUI, progressNotify = None, prefetchProbeNames = False):
        # "location" was previously "path",
        # so this is for backward compatibility:
        if ":/" not in location:
            location = "sqlite://" + location
        db.connectUri(location)
        scenarioColumns = db.Scenario.Scenario.sqlmeta.columns.keys()
        excludeParameters = ['hostname', 'id', 'probes', 'resultsMerged',
                             'sgeJobId', 'startDate', 'state', 'stderr', 'stdout', 'stopDate']
        self.parameters = paramSelectUI.do(scenarioColumns, excludeParameters)
        self.progressNotify = progressNotify
        self.prefetchProbeNames = prefetchProbeNames

    def read(self):
        if self.parameters == []:
            return [], []
        scenarios = []
        dbScenarios = list(db.Scenario.Scenario.select())
        maxIndex = len(dbScenarios)
        for index, scenario in enumerate(dbScenarios):
            parameters = {}
            for parameter in self.parameters:
                parameters[parameter] = getattr(scenario, parameter)
            scenarioData = Representations.Scenario(ScenarioReader(scenario.id), parameters, self.prefetchProbeNames)
            scenarios.append(scenarioData)
            if callable(self.progressNotify):
                self.progressNotify(index + 1, maxIndex, "reading id " + str(scenario.id))
        return scenarios, self.parameters

