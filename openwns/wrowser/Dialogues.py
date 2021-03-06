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

import os
import datetime

from PyQt4 import QtCore, QtGui

from Tools import URI, Observing

import Models
import Debug
import time

from ui.Dialogues_Preferences_ui import Ui_Dialogues_Preferences
class Preferences(QtGui.QDialog, Ui_Dialogues_Preferences):

    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
        self.setupUi(self)

    def readFromConfig(self, filename, owner):
        import Configuration
        try:
            c = Configuration.Configuration()
            c.read(filename)
        except Configuration.MissingConfigurationFile, e:
            setattr(c, 'dbHost', "")
            setattr(c, 'dbName', "")
            setattr(c, 'userName', "")
            setattr(c, 'userPassword', "")
            c.writeDbAccessConf(filename, owner)
        except (Configuration.BadConfigurationFile,
                Configuration.MissingConfigurationSection,
                Configuration.MissingConfigurationEntry), e:
            QtGui.QMessageBox.warning(self, "Parse Error", "Cannot read %s. Creating a new one.\n Error is : %s" % (unicode(e.filename), str(e)))
            setattr(c, 'dbHost', "")
            setattr(c, 'dbName', "")
            setattr(c, 'userName', "")
            setattr(c, 'userPassword', "")
            c.writeDbAccessConf(filename, owner)

        self.hostname.setText(c.dbHost)
        self.databasename.setText(c.dbName)
        self.username.setText(c.userName)
        self.password.setText(c.userPassword)
        
        try:
            cSandbox = Configuration.SandboxConfiguration()
            cSandbox.read()
        except Configuration.MissingConfigurationFile, e:
            setattr(cSandbox, 'sandboxPath', "")
            setattr(cSandbox, 'sandboxFlavour', "dbg")
            c.writeDbAccessConf(filename, owner)
        except (Configuration.BadConfigurationFile,
                Configuration.MissingConfigurationSection,
                Configuration.MissingConfigurationEntry), e:
            setattr(cSandbox, 'sandboxPath', "")
            setattr(cSandbox, 'sandboxFlavour', "dbg")
            cSandbox.writeSandboxConf(owner)

        self.sandboxpath.setText(cSandbox.sandboxPath)
        self.sandboxflavour.setCurrentIndex(self.sandboxflavour.findText(QtCore.QString(cSandbox.sandboxFlavour)))

    def writeToConfig(self, filename, owner):
        import Configuration
        c = Configuration.Configuration()
        c.read(filename)

        setattr(c, 'dbHost', str(self.hostname.text()))
        setattr(c, 'dbName', str(self.databasename.text()))
        setattr(c, 'userName', str(self.username.text()))
        setattr(c, 'userPassword', str(self.password.text()))
        c.writeDbAccessConf(filename, owner)

        cSandbox = Configuration.SandboxConfiguration()
        cSandbox.read()
        setattr(cSandbox, 'sandboxPath', str(self.sandboxpath.text()))
        setattr(cSandbox, 'sandboxFlavour', str(self.sandboxflavour.currentText()))
        cSandbox.writeSandboxConf(owner)

from ui.Dialogues_OpenCouchDatabase_ui import Ui_CouchDBDialog
class OpenCouchDatabase(QtGui.QDialog, Ui_CouchDBDialog):
    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)

        self.setupUi(self)

        self._readDatabases()

        self.connect(self.importButton, QtCore.SIGNAL("clicked()"), self.onImportClicked)

    def _readDatabases(self):
        import desktopcouch.records.server
        import couchdb.client
        port = desktopcouch.find_port()
        s = desktopcouch.records.server.OAuthCapableServer('http://localhost:%s/' % port)
        self.listWidget.clear()
        for dbname in s:
            self.listWidget.addItem(dbname)

    def onImportClicked(self):
        import tracing.model
        fileDialogue = QtGui.QFileDialog(self, "Select a Probe to import", os.getcwd(), "Probe files (*.dat)")
        fileDialogue.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        fileDialogue.setFileMode(QtGui.QFileDialog.ExistingFile)
        fileDialogue.setViewMode(QtGui.QFileDialog.Detail)
        if fileDialogue.exec_() == QtGui.QDialog.Accepted:
            fileName = fileDialogue.selectedFiles()[0]
        else:
            return

        dbName = "unnamed"
        r = QtGui.QInputDialog.getText(self, "Give a name for the new database", "Datbase name:", QtGui.QLineEdit.Normal, dbName)
        if (r[1] and r[0] != ""):
            dbName = r[0]

        tracing.model.importFile(str(fileName), str(dbName))

        self._readDatabases()

    def getDatabase(self):
        i = self.listWidget.selectedItems()
        if len(i)!=1:
            return None
        return i[0].text()

    def contextMenuEvent(self, event):
        import tracing.model
        items = self.listWidget.selectedItems()
        dbname = items[0].data(0).toString()
        
        menu = QtGui.QMenu(self)
        deleteAction = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == deleteAction:
            msg = QtGui.QMessageBox()
            msg.setText("<b>%s</b> will be permanently deleted!" % dbname)
            msg.setInformativeText("Do your really want to delete?")
            msg.setStandardButtons(QtGui.QMessageBox.Yes|QtGui.QMessageBox.Cancel)
            msg.setDefaultButton(QtGui.QMessageBox.Cancel)
            ret = msg.exec_()

            if ret == QtGui.QMessageBox.Yes:
                tracing.model.deleteDB(str(dbname))
                self._readDatabases()

from ui.Dialogues_OpenCampaignDb_ui import Ui_Dialogues_OpenCampaignDb
class OpenCampaignDb(QtGui.QDialog, Ui_Dialogues_OpenCampaignDb):
    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
        self.setupUi(self)

        self.refresh()

    def refresh(self):
        from openwns.wrowser.simdb import Campaigns
        self.campaignsModel = Models.CampaignDb(Campaigns.getCampaignsDict())
        self.campaigns.setModel(self.campaignsModel)

        user = os.getenv("USER")
        userIndex = self.campaignsModel.getUserRow(user)
        if userIndex != -1 :
            self.campaigns.expand(userIndex)
            self.campaigns.scrollTo(userIndex)

        for column in xrange(self.campaignsModel.columnCount()):
            self.campaigns.resizeColumnToContents(column)
        self.connect(self.campaigns, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.campaignSelected)
    
    def campaignSelected(self, index):
           if index.column()>0 and len(self.campaigns.selectedIndexes())>0:
                self.buttonBox.emit(QtCore.SIGNAL("accepted()"))


    def getCampaign(self):
        return self.campaignsModel.getCampaign(self.campaigns.selectedIndexes()[0])

    def contextMenuEvent(self, event):
        items = self.campaigns.selectionModel().selectedIndexes()
        model = self.campaigns.model()

        campaignId = model.getCampaign(items[0])
        dbname = model.data(items[1]).toString()
        
        menu = QtGui.QMenu(self)
        deleteAction = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == deleteAction:
            msg = QtGui.QMessageBox()
            msg.setText("<b>%s (%d)</b> will be permanently deleted!" % (dbname, campaignId))
            msg.setInformativeText("Do your really want to delete?")
            msg.setStandardButtons(QtGui.QMessageBox.Yes|QtGui.QMessageBox.Cancel)
            msg.setDefaultButton(QtGui.QMessageBox.Cancel)
            ret = msg.exec_()

            if ret == QtGui.QMessageBox.Yes:

                from openwns.wrowser.simdb.Database import Database
                cursor = Database.getCursor()
                cursor.execute('SELECT * FROM campaigns WHERE id = %i' % campaignId)
                if len(cursor.fetchall()) != 1:
                    Warning(self, "Campaign not found", "Campaign %s not found" % dbname,
                            "<h4>I cannot find the campaign</h4>")
                    cursor.connection.commit()
                    return


                Database.disconnect()

                import Configuration

                c = Configuration.Configuration()
                c.read()

                Database.connectConf(c)

                Database.deleteCampaign(campaignId)

                Database.disconnect()

                msg = QtGui.QMessageBox()
                msg.setText("<b>%s (%d)</b> successfully deleted!" % (dbname, campaignId))
                msg.setInformativeText("Deletion has finished")
                msg.setStandardButtons(QtGui.QMessageBox.Ok)
                msg.setDefaultButton(QtGui.QMessageBox.Ok)
                ret = msg.exec_()

                self.refresh()


from ui.Dialogues_OpenDSV_ui import Ui_Dialogues_OpenDSV
class OpenDSV(QtGui.QDialog, Ui_Dialogues_OpenDSV):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        self.setupUi(self)

    @QtCore.pyqtSignature("bool")
    def on_openButton_clicked(self, checked):
        Debug.printCall(self, checked)
        fileDialogue = QtGui.QFileDialog(self, "Select a campaign", os.getcwd(), "DSV files (*.csv *.txt)")
        fileDialogue.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        fileDialogue.setFileMode(QtGui.QFileDialog.ExistingFile)
        fileDialogue.setViewMode(QtGui.QFileDialog.Detail)
        if fileDialogue.exec_() == QtGui.QDialog.Accepted:
            fileName = fileDialogue.selectedFiles()[0]
            self.fileNameEdit.setText(fileName)

    @QtCore.pyqtSignature("")
    def on_fileNameEdit_editingFinished(self):
        Debug.printCall(self)
        text = str(self.fileNameEdit.text())
        if not text.startswith("/"):
            text = os.path.abspath(text)
            self.fileNameEdit.setText(text)

    def getSettings(self):
        from Tools import Chameleon as Values

        return Values(fileName = str(self.fileNameEdit.text()),
                      delimiter = str(self.delimiterEdit.text()),
                      directoryColumn = str(self.directoryColumnEdit.text()),
                      subDirectory = str(self.subDirectoryEdit.text()))

class ProgressStatus(QtGui.QProgressBar):
    def __init__(self, progressLabel,  *args):
        QtGui.QProgressBar.__init__(self, *args)
        self.progressLabel = progressLabel
        self.labelText=""
        self.labelLength=80
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed))
        self.reset()

    def reset(self):
        self.setMinimum(0)
        self.startTime = datetime.datetime.now()
        QtGui.QProgressBar.reset(self)

    def setCurrentAndMaximum(self, current, maximum, additionalText = ""):
        import Time
        
        self.setMaximum(maximum)
        self.setValue(current)
        labelText = self.labelText
        timeDelta = ""
        if len(additionalText) > 0:
            additionalText = additionalText.replace('\n',' ')
            labelText += " " + additionalText
        if maximum > 0 and float(current)/maximum >= 0.01:
            elapsed = datetime.datetime.now() - self.startTime
            total = elapsed * maximum / current
            remaining = total - elapsed
            timeDelta = ".. approx. " + Time.Delta(remaining).asString() + " left"
        if QtGui.QApplication.hasPendingEvents():
            QtGui.QApplication.instance().syncX()
            QtGui.QApplication.instance().processEvents()
            if len(labelText) > self.labelLength:
                labelText = timeDelta
            else:
                labelText += timeDelta 
            self.progressLabel.setText(labelText)
        time.sleep(0.006)

class Progress(QtGui.QProgressDialog):
    def __init__(self, labelText, minShow, *args):
        QtGui.QProgressDialog.__init__(self, *args)
        self.setCancelButtonText("Cancel")
        self.labelText = labelText
        self.setLabelText(labelText)
        self.setMinimumDuration(minShow)
        self.setAutoClose(True)
        self.reset()

    def reset(self):
        self.setMinimum(0)
        self.startTime = datetime.datetime.now()
        QtGui.QProgressDialog.reset(self)

    def setCurrentAndMaximum(self, current, maximum, additionalText = ""):
        import Time

        self.setMaximum(maximum)
        self.setValue(current)
        labelText = self.labelText
        if len(additionalText) > 0:
            labelText += "\n" + additionalText
        if maximum > 0 and float(current)/maximum >= 0.01:
            elapsed = datetime.datetime.now() - self.startTime
            total = elapsed * maximum / current
            remaining = total - elapsed
            labelText += "\napprox. " + Time.Delta(remaining).asString() + " left"
        self.setLabelText(labelText)
        if QtGui.QApplication.hasPendingEvents():
            QtGui.QApplication.instance().syncX()
            QtGui.QApplication.instance().processEvents()
        time.sleep(0.006)

from ui.Dialogues_ColumnSelect_ui import Ui_Dialogues_ColumnSelect
class ColumnSelect(QtGui.QDialog, Ui_Dialogues_ColumnSelect):
    def __init__(self, cancelFlag, *args):
        QtGui.QDialog.__init__(self, *args)
        self.cancelFlag = cancelFlag
        self.setupUi(self)

    def do(self, columns, deselectedColumns):
        self.columnList.addItems(columns)
        for row in range(0, self.columnList.count()):
            item = self.columnList.item(row)
            self.columnList.setItemSelected(item, not item.text() in deselectedColumns)
        if self.exec_() == QtGui.QDialog.Accepted:
            parameters = []
            for row in range(0, self.columnList.count()):
                item = self.columnList.item(row)
                if self.columnList.isItemSelected(item):
                    parameters.append(str(item.text()))
            return parameters
        else:
            self.cancelFlag.cancelled = True
            return []

from ui.Dialogues_ConfigureGraph_ui import Ui_Dialogues_ConfigureGraph
class ConfigureGraph(QtGui.QDialog, Ui_Dialogues_ConfigureGraph):

    def __init__(self, figure, *args):
        import matplotlib.numerix as numerix

        self.figure = figure
        self.scales = {"linear": ("linear", None),
                       "ld": ("log", 2),
                       "ln": ("log", numerix.e),
                       "lg": ("log", 10)}
        self.scalesReverse = dict(zip(self.scales.values(),
                                      self.scales.keys()))

        QtGui.QWidget.__init__(self, *args)
        self.setupUi(self)

        if self.figure.grid[0]:
            self.xgridMajor.setCheckState(QtCore.Qt.Checked)
        if self.figure.grid[1]:
            self.xgridMinor.setCheckState(QtCore.Qt.Checked)
        if self.figure.grid[2]:
            self.ygridMajor.setCheckState(QtCore.Qt.Checked)
        if self.figure.grid[3]:
            self.ygridMinor.setCheckState(QtCore.Qt.Checked)

        self.xscale.setCurrentIndex(self.xscale.findText(self.scalesReverse[self.figure.scale[0:2]]))
        self.yscale.setCurrentIndex(self.yscale.findText(self.scalesReverse[self.figure.scale[2:4]]))

        self.marker.setCurrentIndex(self.marker.findText(self.figure.marker))
        if self.figure.legend:
            self.showLegend.setCheckState(QtCore.Qt.Checked)
        self.titleEdit.setText(self.figure.title)
        self.xAxisEdit.setText(self.figure.xAxisTitle)
        self.yAxisEdit.setText(self.figure.yAxisTitle)
        if self.figure.colorbar:
            self.colorbarCheckBox.setCheckState(QtCore.Qt.Checked)
        else:
            self.colorbarCheckBox.setCheckState(QtCore.Qt.Unchecked)

        self.colormapComboBox.setCurrentIndex(self.colormapComboBox.findText(self.figure.colormap))

        self.tabWidget.setCurrentIndex(0)

    @QtCore.pyqtSignature("")
    def on_buttonBox_accepted(self):
        self.applyData()

    @QtCore.pyqtSignature("QAbstractButton*")
    def on_buttonBox_clicked(self, button):
        if self.buttonBox.buttonRole(button) == QtGui.QDialogButtonBox.ApplyRole:
            self.applyData()

    def applyData(self):
        grid = (self.xgridMajor.checkState() == QtCore.Qt.Checked,
                self.xgridMinor.checkState() == QtCore.Qt.Checked,
                self.ygridMajor.checkState() == QtCore.Qt.Checked,
                self.ygridMinor.checkState() == QtCore.Qt.Checked)
        if grid != self.figure.grid:
            self.figure.grid = grid
        scale = self.scales[str(self.xscale.currentText())] + \
                            self.scales[str(self.yscale.currentText())]
        if scale != self.figure.scale:
            self.figure.scale = scale

        marker = str(self.marker.currentText())
        if marker == "None":
            marker = ""
        if marker != self.figure.marker:
            self.figure.marker = marker

        legend = self.showLegend.checkState() == QtCore.Qt.Checked
        if legend != self.figure.legend:
            self.figure.legend = legend

        self.figure.colormap = self.colormapComboBox.currentText()
        self.figure.colorbar = self.colorbarCheckBox.checkState() == QtCore.Qt.Checked

        title = str(self.titleEdit.text())
        if self.figure.title != title:
            self.figure.title = title

        if self.figure.xAxisTitle != str(self.xAxisEdit.text()):
            self.figure.xAxisTitle = str(self.xAxisEdit.text())

        if self.figure.yAxisTitle != str(self.yAxisEdit.text()):
            self.figure.yAxisTitle = str(self.yAxisEdit.text())

class SelectItem(QtGui.QDialog):

    class ComboBox(QtGui.QWidget):

        def __init__(self, caption, items, *args):
            QtGui.QWidget.__init__(self, *args)
            self.mylayout = QtGui.QHBoxLayout(self)
            self.mylayout.setMargin(9)
            self.mylayout.setSpacing(6)
            self.mylayout.setObjectName("mylayout")

            self.label = QtGui.QLabel(self)
            self.label.setText(caption)
            self.mylayout.addWidget(self.label)

            self.comboBox = QtGui.QComboBox(self)
            self.comboBox.addItems(items)
            self.mylayout.addWidget(self.comboBox)

        def selectedIndex(self):
            return self.comboBox.currentIndex()

        def selectedText(self):
            return self.comboBox.currentText()

    class RadioButtons(QtGui.QWidget):

        def __init__(self, caption, items, *args):
            QtGui.QWidget.__init__(self, *args)

            self.mylayout = QtGui.QVBoxLayout(self)
            self.mylayout.setMargin(9)
            self.mylayout.setSpacing(6)
            self.mylayout.setObjectName("mylayout")

            self.groupbox = QtGui.QGroupBox(self)
            self.groupbox.setObjectName("groupbox")
            self.groupbox.setTitle(caption)
            self.mylayout.addWidget(self.groupbox)

            self.groupboxlayout = QtGui.QVBoxLayout(self.groupbox)
            self.groupboxlayout.setMargin(9)
            self.groupboxlayout.setSpacing(6)

            self.radiobuttons = []
            for index, item in enumerate(items):
                radiobutton = QtGui.QRadioButton(self.groupbox)
                radiobutton.setObjectName("radiobutton" + str(index))
                radiobutton.setText(item)
                self.groupboxlayout.addWidget(radiobutton)
                self.radiobuttons.append(radiobutton)

            self.radiobuttons[0].setChecked(True)

        def selectedIndex(self):
            for index in xrange(len(self.radiobuttons)):
                if self.radiobuttons[index].isChecked():
                    return index
            raise Exception("SelectItem.RadioButtons instance in invalid state")

        def selectedText(self):
            return self.radiobuttons[self.selectedIndex()].text()

    def __init__(self, title, caption, items, parent = None, selectWidget = ComboBox, *args):
        assert(len(items) > 0)
        self.items = items
        QtGui.QDialog.__init__(self, parent, *args)
        self.setObjectName("SelectItem")
        self.mylayout = QtGui.QVBoxLayout(self)
        self.mylayout.setMargin(9)
        self.mylayout.setSpacing(6)
        self.mylayout.setObjectName("mylayout")

        self.setWindowTitle(title)

        self.selectWidget = selectWidget(caption, items, self)
        self.selectWidget.setObjectName("selectWidget")
        self.mylayout.addWidget(self.selectWidget)

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.mylayout.addWidget(self.buttonBox)

        self.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), self.reject)

    def selectedIndex(self):
        if len(self.items) == 1:
            return 0
        else:
            return self.selectWidget.selectedIndex()

    def selectedText(self):
        if len(self.items) == 1:
            return self.items[0]
        else:
            return str(self.selectWidget.selectedText())

    def exec_(self):
        if len(self.items) == 1:
            return QtGui.QDialog.Accepted
        else:
            return QtGui.QDialog.exec_(self)


from ui.Dialogues_Warning_ui import Ui_Dialogues_Warning
class Warning(QtGui.QDialog, Ui_Dialogues_Warning):
    def __init__(self, parent, entryname, title, message, *args):
        QtGui.QDialog.__init__(self, *args)
        self.setupUi(self)

        self.setWindowTitle(title)
        self.label.setText(message)
        self.entryname = entryname

        import os
        import os.path
        self.owner = os.environ["USER"]

        import Configuration
        self.cSandbox = Configuration.SandboxConfiguration()
        try:
            self.cSandbox.read()
        except Configuration.MissingConfigurationFile, e:
            setattr(self.cSandbox, 'hiddenwarnings_%s' % (self.entryname), "0")
            c.writeSandboxConf(filename, self.owner)
        except (Configuration.BadConfigurationFile,
                Configuration.MissingConfigurationSection,
                Configuration.MissingConfigurationEntry), e:
            setattr(self.cSandbox, 'hiddenwarnings_%s' % (self.entryname), "0")
            self.cSandbox.writeSandboxConf(self.owner)

        try:
            self.disabled = self.cSandbox.parser.get('Warnings', 'hiddenwarnings_%s' % (self.entryname))
        except:
            self.disabled = "0"
            setattr(self.cSandbox, 'hiddenwarnings_%s' % (self.entryname), "0")
            self.cSandbox.writeSandboxConf(self.owner)

        self.exec_()

    def exec_(self):
        if self.disabled == "0":
            r = QtGui.QDialog.exec_(self)
            if self.checkBox.checkState() == QtCore.Qt.Checked:
                setattr(self.cSandbox, 'hiddenwarnings_%s' % (self.entryname), "1")
                self.cSandbox.writeSandboxConf(self.owner)
