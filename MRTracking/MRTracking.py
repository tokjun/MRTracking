import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *


#------------------------------------------------------------
#
# MRTracking
#
class MRTracking(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MRTracking" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda, Wei Wang, Ehud Schmidt (BWH)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    A communication interface for Koh Young's 3D sensors.
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH National Center for Image Guided Therapy (P41EB015898).
    """ 
    # replace with organization, grant and thanks.


#------------------------------------------------------------
#
# MRTrackingWidget
#
class MRTrackingWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = MRTrackingLogic(None)
    self.logic.setWidget(self)

    #--------------------------------------------------
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    reloadCollapsibleButton.collapsed = True
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "CurveMaker Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------


    #--------------------------------------------------
    # GUI components
    
    #
    # Setup Area
    #
    setupCollapsibleButton = ctk.ctkCollapsibleButton()
    setupCollapsibleButton.text = "Setup"
    self.layout.addWidget(setupCollapsibleButton)

    # Layout within the dummy collapsible button
    setupFormLayout = qt.QFormLayout(setupCollapsibleButton)

    #
    # input volume selector
    #
    self.connectorSelector = slicer.qMRMLNodeComboBox()
    self.connectorSelector.nodeTypes = ( ("vtkMRMLIGTLConnectorNode"), "" )
    self.connectorSelector.selectNodeUponCreation = True
    self.connectorSelector.addEnabled = True
    self.connectorSelector.removeEnabled = False
    self.connectorSelector.noneEnabled = False
    self.connectorSelector.showHidden = False
    self.connectorSelector.showChildNodeTypes = False
    self.connectorSelector.setMRMLScene( slicer.mrmlScene )
    self.connectorSelector.setToolTip( "Establish a connection with the server" )
    setupFormLayout.addRow("Connector: ", self.connectorSelector)
    
    #self.connectorAddressLineEdit = qt.QLineEdit()
    #self.connectorAddressLineEdit.text = "localhost"
    #self.connectorAddressLineEdit.readOnly = False
    #self.connectorAddressLineEdit.frame = True
    #self.connectorAddressLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    #self.connectorAddressLineEdit.cursor = qt.QCursor(qt.Qt.IBeamCursor)
    #setupFormLayout.addRow("Address: ", self.connectorAddressLineEdit)

    self.connectorPort = qt.QSpinBox()
    self.connectorPort.objectName = 'PortSpinBox'
    self.connectorPort.setMaximum(64000)
    self.connectorPort.setValue(18944)
    self.connectorPort.setToolTip("Port number of the server")
    setupFormLayout.addRow("Port: ", self.connectorPort)

    #
    # check box to trigger transform conversion
    #
    self.activeCheckBox = qt.QCheckBox()
    self.activeCheckBox.checked = 0
    self.activeCheckBox.setToolTip("Activate OpenIGTLink connection")
    setupFormLayout.addRow("Active: ", self.activeCheckBox)

    #
    # Registration Matrix Selection Area
    #
    selectionCollapsibleButton = ctk.ctkCollapsibleButton()
    selectionCollapsibleButton.text = "Registration Matrix Selection"
    self.layout.addWidget(selectionCollapsibleButton)

    selectionFormLayout = qt.QFormLayout(selectionCollapsibleButton)

    self.regIDLineEdit = qt.QLineEdit()
    self.regIDLineEdit.text = ''
    self.regIDLineEdit.readOnly = True
    self.regIDLineEdit.frame = True
    self.regIDLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    self.regIDLineEdit.cursor = qt.QCursor(qt.Qt.IBeamCursor)

    self.freLineEdit = qt.QLineEdit()
    self.freLineEdit.text = 'FRE not available'
    self.freLineEdit.readOnly = True
    self.freLineEdit.frame = True
    self.freLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    self.freLineEdit.cursor = qt.QCursor(qt.Qt.IBeamCursor)

    currentRegLayout = qt.QHBoxLayout()
    currentIDLabel = qt.QLabel('ID:')
    currentFRELabel = qt.QLabel('  FRE:')
    currentUnitLabel = qt.QLabel('mm')
    currentRegLayout.addWidget(currentIDLabel)
    currentRegLayout.addWidget(self.regIDLineEdit)
    currentRegLayout.addWidget(currentFRELabel)
    currentRegLayout.addWidget(self.freLineEdit)
    currentRegLayout.addWidget(currentUnitLabel)
    selectionFormLayout.addRow("Current:", currentRegLayout)

    self.newRegIDLineEdit = qt.QLineEdit()
    self.newRegIDLineEdit.text = ''
    self.newRegIDLineEdit.readOnly = True
    self.newRegIDLineEdit.frame = True
    self.newRegIDLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    self.newRegIDLineEdit.cursor = qt.QCursor(qt.Qt.IBeamCursor)

    self.newFreLineEdit = qt.QLineEdit()
    self.newFreLineEdit.text = 'FRE not available'
    self.newFreLineEdit.readOnly = True
    self.newFreLineEdit.frame = True
    self.newFreLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    self.newFreLineEdit.cursor = qt.QCursor(qt.Qt.IBeamCursor)

    newRegLayout = qt.QHBoxLayout()
    newIDLabel = qt.QLabel('ID:')
    newFRELabel = qt.QLabel('  FRE:')
    newUnitLabel = qt.QLabel('mm')
    newRegLayout.addWidget(newIDLabel)
    newRegLayout.addWidget(self.newRegIDLineEdit)
    newRegLayout.addWidget(newFRELabel)
    newRegLayout.addWidget(self.newFreLineEdit)
    newRegLayout.addWidget(newUnitLabel)
    selectionFormLayout.addRow("New:", newRegLayout)

    self.acceptButton = qt.QPushButton("Accept New")
    self.acceptButton.toolTip = "Accept new registration"
    self.acceptButton.enabled = False
    selectionFormLayout.addRow(self.acceptButton)

    self.rejectButton = qt.QPushButton("Use Current")
    self.rejectButton.toolTip = "Reject new registration and use current one"
    self.rejectButton.enabled = False
    selectionFormLayout.addRow(self.rejectButton)
    
    matrixSelectionLayout = qt.QHBoxLayout()
    matrixSelectionLayout.addWidget(self.acceptButton)
    matrixSelectionLayout.addWidget(self.rejectButton)
    selectionFormLayout.addRow(matrixSelectionLayout)

    #--------------------------------------------------
    # connections
    #
    self.connectorSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onConnectorSelect)
    self.activeCheckBox.connect('toggled(bool)', self.onActive)

    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass


  def onActive(self):
    
    if self.connectorSelector.currentNode() == None:
      return

    if self.activeCheckBox.checked == True:
      if self.logic.connected() != True:
        # Setup connector
        #addr  = self.connectorAddressLineEdit.text
        port  = self.connectorPort.value
        #self.logic.connectToServer(addr, port)
        self.logic.waitForClient(port)
    else:
      self.logic.disconnect()

    #time.sleep(1)
    #self.updateGUI()


  def onConnectorSelect(self):
    cnode = self.connectorSelector.currentNode()    
    self.logic.setConnector(cnode)


  def onRejectRegistration(self):
    self.logic.acceptNewMatrix(self, False)


  def onReload(self, moduleName="MRTracking"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


  def updateGUI(self):
    # Enable/disable GUI components based on the state machine

    #if self.logic.connected():
    if self.logic.active():
      self.activeCheckBox.setChecked(True)
    else:
      self.activeCheckBox.setChecked(False)

    # Enable/disable 'Active' checkbox 
    if self.connectorSelector.currentNode():
      self.activeCheckBox.setEnabled(True)
    else:
      self.activeCheckBox.setEnabled(False)



#------------------------------------------------------------
#
# MRTrackingLogic
#
class MRTrackingLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent):
    ScriptedLoadableModuleLogic.__init__(self, parent)

    self.scene = slicer.mrmlScene
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)

    self.widget = None

    self.eventTag = {}

    # IGTL Conenctor Node ID
    self.connectorNodeID = ''

    self.count = 0
    
  def setWidget(self, widget):
    self.widget = widget


  def setConnector(self, cnode):

    if cnode == None:
      self.connectorNodeID = ''
      return

    if self.connectorNodeID != cnode.GetID():
      if self.connectorNodeID != '':
        self.deactivateEvent()
      self.connectorNodeID = cnode.GetID()
      self.activateEvent()

  def connectToServer(self, addr, port):

    if self.connectorNodeID == '':
      return

    cnode = self.scene.GetNodeByID(self.connectorNodeID)

    cnode.SetTypeClient(addr, port)
    cnode.Start()


  def waitForClient(self, port):
  
    if self.connectorNodeID == '':
      return

    cnode = self.scene.GetNodeByID(self.connectorNodeID)

    cnode.SetTypeServer(port)
    cnode.Start()


    
  def disconnect(self):

    cnode = self.scene.GetNodeByID(self.connectorNodeID)
    
    if cnode == None:
      return False

    cnode.Stop()

  def active(self):
    # Check the activation status.
    # Return True, if the connector is connected to the server

    cnode = self.scene.GetNodeByID(self.connectorNodeID)

    if cnode == None:
      return False
      
    if cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.STATE_WAIT_CONNECTION or cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.STATE_CONNECTED:
      return True
    else:
      return False
    
    cnode = self.scene.GetNodeByID(self.connectorNodeID)

  def connected(self):
    # Check the connection status.
    # Return True, if the connector is connected to the server

    cnode = self.scene.GetNodeByID(self.connectorNodeID)

    if cnode == None:
      return False
      
    if cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.STATE_CONNECTED:
      return True
    else:
      return False

  def onMessageReceived(self, node):
    pass
    # A message handler for the Tracking state.
    # Return True, if the message has been processed

    #print "onMessageReceivedTracking(self, node)"
    
    #if node.GetNodeTagName() == 'IGTLStatus' and node.GetName() == 'CUR_REG':
    #
    #  if node.GetCode() == slicer.vtkMRMLIGTLStatusNode.STATUS_OK:
    #    # Current registration matrix ID is received
    #    self.currentRegID = node.GetErrorName()
    #
    #  elif node.GetCode() == slicer.vtkMRMLIGTLStatusNode.STATUS_CONFIG_ERROR:
    #    # Registration has not been completed
    #    self.currentRegID = ''
    #
    #  return True
    #
    #elif node.GetNodeTagName() == 'IGTLStatus' and node.GetName() == 'NEW_REG':
    #  
    #  if node.GetCode() == slicer.vtkMRMLIGTLStatusNode.STATUS_OK:
    #    self.widget.updateGUI()          
    #      
    #  return True
    #
    #else:
    #
    #  return False
    pass
    


  def onConnectedEvent(self, caller, event):
    #if self.widget != None:
    #  self.widget.updateGUI()
    pass


  def onDisconnectedEvent(self, caller, event):
    #if self.widget != None:
    #  self.widget.updateGUI()
    pass


  def onNewDeviceEvent(self, caller, event, obj=None):

    cnode = self.scene.GetNodeByID(self.connectorNodeID)
    nInNode = cnode.GetNumberOfIncomingMRMLNodes()
    print nInNode
    for i in range (nInNode):
      node = cnode.GetIncomingMRMLNode(i)
      if not node.GetID() in self.eventTag:
        self.eventTag[node.GetID()] = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        if node.GetNodeTagName() == 'IGTLTrackingDataSplitter':
          n = node.GetNumberOfTransformNodes()
          for id in range (n):
            tnode = node.GetTransformNode(id)
            if tnode and tnode.GetAttribute('MRTracking') == None:
              print "No MRTracking"
              needleModelID = self.createNeedleModelNode("Needle_%s" % tnode.GetName())
              needleModel = self.scene.GetNodeByID(needleModelID)
              needleModel.SetAndObserveTransformNodeID(tnode.GetID())
              needleModel.InvokeEvent(slicer.vtkMRMLTransformableNode.TransformModifiedEvent)
              tnode.SetAttribute('MRTracking', needleModelID)

  def createNeedleModel(self, node):
    if node and node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      n = node.GetNumberOfTransformNodes()
      print n
      for id in range (n):
        tnode = node.GetTransformNode(id)
        if tnode:
          needleModelID = self.createNeedleModelNode("Needle_%s" % tnode.GetName())
          needleModel = self.scene.GetNodeByID(needleModelID)
          needleModel.SetAndObserveTransformNodeID(tnode.GetID())
          needleModel.InvokeEvent(slicer.vtkMRMLTransformableNode.TransformModifiedEvent)

        
  def createNeedleModelNode(self, name):

    locatorModel = self.scene.CreateNodeByClass('vtkMRMLModelNode')
    
    # Cylinder represents the locator stick
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetRadius(1.5)
    cylinder.SetHeight(100)
    cylinder.SetCenter(0, 0, 0)
    cylinder.Update()

    # Rotate cylinder
    tfilter = vtk.vtkTransformPolyDataFilter()
    trans =   vtk.vtkTransform()
    trans.RotateX(90.0)
    trans.Translate(0.0, -50.0, 0.0)
    trans.Update()
    if vtk.VTK_MAJOR_VERSION <= 5:
      tfilter.SetInput(cylinder.GetOutput())
    else:
      tfilter.SetInputConnection(cylinder.GetOutputPort())
    tfilter.SetTransform(trans)
    tfilter.Update()

    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(3.0)
    sphere.SetCenter(0, 0, 0)
    sphere.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tfilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tfilter.GetOutputPort())
    apd.Update()
    
    locatorModel.SetAndObservePolyData(apd.GetOutput());

    self.scene.AddNode(locatorModel)
    locatorModel.SetScene(self.scene);
    locatorModel.SetName(name)
    
    locatorDisp = locatorModel.GetDisplayNodeID()
    if locatorDisp == None:
      locatorDisp = self.scene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      self.scene.AddNode(locatorDisp)
      locatorDisp.SetScene(self.scene)
      locatorModel.SetAndObserveDisplayNodeID(locatorDisp.GetID());
      
    color = [0, 0, 0]
    color[0] = 0.5
    color[1] = 0.5
    color[2] = 1.0
    locatorDisp.SetColor(color)
    
    return locatorModel.GetID()


  def onIncomingNodeModifiedEvent(self, caller, event):
    self.onMessageReceived(caller)


  def onNodeRemovedEvent(self, caller, event, obj=None):
    delkey = ''
    if obj == None:
      for k in self.eventTag:
        node = self.scene.GetNodeByID(k)
        if node == None:
          delkey = k
          break

    if delkey != '':
      del self.eventTag[delkey]


  def activateEvent(self):
    cnode = self.scene.GetNodeByID(self.connectorNodeID)    
    if cnode != None:
      self.tagConnected = cnode.AddObserver(slicer.vtkMRMLIGTLConnectorNode.ConnectedEvent, self.onConnectedEvent)
      self.tagDisconnected = cnode.AddObserver(slicer.vtkMRMLIGTLConnectorNode.DisconnectedEvent, self.onDisconnectedEvent)
      self.tagNewDevice = cnode.AddObserver(slicer.vtkMRMLIGTLConnectorNode.NewDeviceEvent, self.onNewDeviceEvent)


  def deactivateEvent(self):
    cnode = self.scene.GetNodeByID(self.connectorNodeID)
    if cnode != None:
      cnode.RemoveObserver(self.tagConnected)
      cnode.RemoveObserver(self.tagDisconnected)
      cnode.RemoveObserver(self.tagNewDevice)

      
