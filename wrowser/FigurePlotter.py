import optparse
import sys
import os

import wrowser.Configuration as simDbConf
import wrowser.simdb.Database as simDb
from wrowser.simdb.Campaigns import setCampaign as simDbSetCampaign

from wrowser.probeselector import PostgresReader
from wrowser.probeselector import Interface
from wrowser.probeselector import Representations
from wrowser.probeselector import Errors

from matplotlib import rc
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import FigureCanvasPdf as FigureCanvas
from matplotlib.font_manager import FontProperties
from pylab import *

from scipy.special import erf

def plotGraphs(PlotParameters):
    def lineStyle():
        
        for style in PlotParameters.color_sytles :
            yield style

    def lineStyleSW():

        for style in PlotParameters.bw_styles :
            yield style

    def hatches():

        for hatch in ['/','\\','|','-','+','x','.','//','\\' ]:
            yield hatch

    def prettyPrint(labels):
        '''
        Give a pretty string of parameter names.
        '''
        def pPString(string):
           if string in PlotParameters.parameterNames:
                return PlotParameters.parameterNames[string]
           else:
                return string

        out = ''
        for k,v in labels.iteritems():
           out += pPString(k) + ': ' + str(v) + ' '
        return out

    ## Get the campaign
    dbConfig = simDbConf.Configuration()
    dbConfig.read()
    simDb.Database.connectConf(dbConfig)
    simDbSetCampaign([int(PlotParameters.campaignId)])
    campaignReader = PostgresReader.CampaignReader(int(PlotParameters.campaignId), Interface.DoNotSelectProbeSelectUI())
    print 'Accessing charts from database server with campaignId: ' + str(PlotParameters.campaignId) + '\n\n'


    print "Reading Campaign"
    campaign = Representations.Campaign(*campaignReader.read())
    print "read"
    print "Creating Facade"
    ch = Interface.Facade(campaign)
    print "done"

    print ch.getParameterNames()
    print ch.getProbeNames()

    outputdir = 'FIGURES'
    if not os.path.exists(outputdir) :
        os.makedirs(outputdir)

    font = FontProperties()
    font.set_size('x-large')

    filteredFacade = ch.filteredByExpression(PlotParameters.filterExpression)
    print "Found " + str(len(filteredFacade.getScenarios())) + " scenarios"

    figure(figsize=(9, 8))
    grid()
    xlabel(PlotParameters.xLabel,fontproperties = font)
    ylabel(PlotParameters.yLabel,fontproperties = font)

    labels=[]

    if PlotParameters.color:
        ls = lineStyle()
    else:
        ls = lineStyleSW()

    probeNr = 0
    try:
     if PlotParameters.type == 'Param': 
        if PlotParameters.useXProbe:
            print "probe wird fuer x benutzt"
            graphList = filteredFacade.getGraphs(PlotParameters.parameterName, PlotParameters.probeName, PlotParameters.probeEntry, PlotParameters.aggrParam, PlotParameters.confidence, PlotParameters.confidenceLevel, plotNotAggregatedGraphs=PlotParameters.originalPlots, useXProbe = PlotParameters.useXProbe, xProbeName = PlotParameters.xProbeName, xProbeEntry = PlotParameters.xProbeEntry)
        else:
            graphList = filteredFacade.getGraphs(PlotParameters.parameterName, PlotParameters.probeName, PlotParameters.probeEntry, PlotParameters.aggrParam, PlotParameters.confidence, PlotParameters.confidenceLevel, plotNotAggregatedGraphs=PlotParameters.originalPlots)
     else:
        graphList = filteredFacade.getHistograms( PlotParameters.probeName, PlotParameters.type, PlotParameters.aggrParam, plotNotAggregatedGraphs=PlotParameters.originalPlots) #, PlotParameters.aggrParam, PlotParameters.confidence)   
    except Errors.MultipleErrors, e:
     graphList = e.graphs

    i=0
    if len(graphList)==0:
        print "no graphs to plot"
    for graph in graphList:
        labels.append(str(graph.sortkey))
        try:
            style=ls.next()
        except StopIteration:
            print "You need to define more linestyles or reduce the number of plotted graphs"    
            os._exit(1)
        X=[x  for x,y in graph.points]
        Y=[y*PlotParameters.scaleFactorY+PlotParameters.moveY  for x,y in graph.points]
        plot([x*PlotParameters.scaleFactorX+PlotParameters.moveX  for x in X ], Y , style , label=prettyPrint(graph.sortkey)+PlotParameters.probeLegendSuffix[probeNr])
        try:
          if PlotParameters.type == 'Param': 
            if PlotParameters.confidence :
                print "plotting confidence intervals"
                for i in range(len(X)):
                    e = graph.confidenceIntervalDict[X[i]]
                    errorbar(X[i]*PlotParameters.scaleFactorX+PlotParameters.moveX, Y[i], yerr=e , fmt=style)
        except: None
    if PlotParameters.doClip:
        axis([PlotParameters.minX,PlotParameters.maxX,PlotParameters.minY,PlotParameters.maxY])     
    if PlotParameters.showTitle :
        title(PlotParameters.figureTitle)
    if PlotParameters.legend:
        legend(prop = font, loc=PlotParameters.legendPosition) # (0.9, 0.01))
    print 'Plotting: ',PlotParameters.fileName
    savefig(os.path.join(outputdir, PlotParameters.fileName+'.pdf'))
    savefig(os.path.join(outputdir, PlotParameters.fileName+'.png'))    
