import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from MRTrackingUtils.trackingdata import *
from MRTrackingUtils.connector import *
from MRTrackingUtils.reslice import *
from MRTrackingUtils.registration import *
import numpy
import functools

import CurveMaker
    
#------------------------------------------------------------
#
# MRTracking
#
class MRTracking(ScriptedLoadableModule):
  """MRTrakcing module is available at:
  https://github.com/tokjun/MRTracking
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MRTracking" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda (BWH), Wei Wang (BWH), Ehud Schmidt (BWH, JHU)"]
    self.parent.helpText = """
    Visualization of MR-tracked catheter. 
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH (P41EB015898, R01EB020667).
    """ 


#------------------------------------------------------------
#
# MRTrackingWidget
#
class MRTrackingWidget(ScriptedLoadableModuleWidget):
  
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

    self.nChannel = 8   # Number of channels / catheter
    self.nCath = 2 # Number of catheters

    #--------------------------------------------------
    # GUI components
    
    #
    # Connection Area
    #
    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "Connection (OpenIGTLink)"
    self.layout.addWidget(connectionCollapsibleButton)

    # Layout within the dummy collapsible button
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

    #--------------------------------------------------
    # Connector Selector
    #--------------------------------------------------

    self.igtlConnector1 = MRTrackingIGTLConnector("Connector 1 (MRI)")
    self.igtlConnector1.port = 18944
    self.igtlConnector1.buildGUI(connectionFormLayout)

    self.igtlConnector2 = MRTrackingIGTLConnector("Connector 2 (NavX)")
    self.igtlConnector2.port = 18945
    self.igtlConnector2.buildGUI(connectionFormLayout)
    
    #--------------------------------------------------
    # Catheter
    #--------------------------------------------------

    catheterCollapsibleButton = ctk.ctkCollapsibleButton()
    catheterCollapsibleButton.text = "Tracking Node"
    self.layout.addWidget(catheterCollapsibleButton)

    catheterFormLayout = qt.QFormLayout(catheterCollapsibleButton)

    #--------------------------------------------------
    # Tracking node selector

    trackingNodeGroupBox = ctk.ctkCollapsibleGroupBox()
    trackingNodeGroupBox.title = "Tracking Node"
    catheterFormLayout.addWidget(trackingNodeGroupBox)
    trackingNodeFormLayout = qt.QFormLayout(trackingNodeGroupBox)
    
    self.trackingDataSelector = slicer.qMRMLNodeComboBox()
    self.trackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.trackingDataSelector.selectNodeUponCreation = True
    self.trackingDataSelector.addEnabled = True
    self.trackingDataSelector.removeEnabled = False
    self.trackingDataSelector.noneEnabled = False
    self.trackingDataSelector.showHidden = True
    self.trackingDataSelector.showChildNodeTypes = False
    self.trackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.trackingDataSelector.setToolTip( "Incoming tracking data" )
    trackingNodeFormLayout.addRow("TrackingData: ", self.trackingDataSelector)

    #
    # check box to trigger transform conversion
    #
    self.activeTrackingCheckBox = qt.QCheckBox()
    self.activeTrackingCheckBox.checked = 0
    self.activeTrackingCheckBox.enabled = 1
    self.activeTrackingCheckBox.setToolTip("Activate Tracking")
    trackingNodeFormLayout.addRow("Active: ", self.activeTrackingCheckBox)
    
    #--------------------------------------------------
    # Catheter Configuration

    configGroupBox = ctk.ctkCollapsibleGroupBox()
    configGroupBox.title = "Catheter Configuration"
    configGroupBox.collapsed = True

    catheterFormLayout.addWidget(configGroupBox)
    configFormLayout = qt.QFormLayout(configGroupBox)


    self.tipLengthSliderWidget = [None] * self.nCath
    self.catheterDiameterSliderWidget = [None] * self.nCath
    self.catheterOpacitySliderWidget = [None] * self.nCath
    
    for cath in range(self.nCath):
      
      #
      # Tip Length (legnth between the catheter tip and the first coil)
      #
      self.tipLengthSliderWidget[cath] = ctk.ctkSliderWidget()
      self.tipLengthSliderWidget[cath].singleStep = 0.5
      self.tipLengthSliderWidget[cath].minimum = 0.0
      self.tipLengthSliderWidget[cath].maximum = 100.0
      self.tipLengthSliderWidget[cath].value = 10.0
      self.tipLengthSliderWidget[cath].setToolTip("Set the length of the catheter tip.")
      configFormLayout.addRow("Cath %d Tip Length (mm): " % cath, self.tipLengthSliderWidget[cath])
      
      #
      # Catheter #1 Catheter diameter
      #
      self.catheterDiameterSliderWidget[cath] = ctk.ctkSliderWidget()
      self.catheterDiameterSliderWidget[cath].singleStep = 0.1
      self.catheterDiameterSliderWidget[cath].minimum = 0.1
      self.catheterDiameterSliderWidget[cath].maximum = 10.0
      self.catheterDiameterSliderWidget[cath].value = 1.0
      self.catheterDiameterSliderWidget[cath].setToolTip("Set the diameter of the catheter")
      configFormLayout.addRow("Cath %d Diameter (mm): " % cath, self.catheterDiameterSliderWidget[cath])
      
      #
      # Catheter #1 Catheter opacity
      #
      self.catheterOpacitySliderWidget[cath] = ctk.ctkSliderWidget()
      self.catheterOpacitySliderWidget[cath].singleStep = 0.1
      self.catheterOpacitySliderWidget[cath].minimum = 0.0
      self.catheterOpacitySliderWidget[cath].maximum = 1.0
      self.catheterOpacitySliderWidget[cath].value = 1.0
      self.catheterOpacitySliderWidget[cath].setToolTip("Set the opacity of the catheter")
      configFormLayout.addRow("Cath %d Opacity: " % cath, self.catheterOpacitySliderWidget[cath])

    #--------------------------------------------------
    # Coil Selection Aare
    #
    coilGroupBox = ctk.ctkCollapsibleGroupBox()
    coilGroupBox.title = "Coil Selection"
    coilGroupBox.collapsed = True
    
    catheterFormLayout.addWidget(coilGroupBox)
    coilSelectionLayout = qt.QFormLayout(coilGroupBox)

    #
    # Check box to show/hide coil labels 
    #
    self.showCoilLabelCheckBox = qt.QCheckBox()
    self.showCoilLabelCheckBox.checked = 0
    self.showCoilLabelCheckBox.setToolTip("Show/hide coil labels")
    coilSelectionLayout.addRow("Show Coil Labels: ", self.showCoilLabelCheckBox)

    #
    # Coil seleciton check boxes
    #
    self.coilCheckBox = [[None for i in range(self.nChannel)] for j in range(self.nCath)]
    self.coilOrderDistalRadioButton = [None]*self.nCath
    self.coilOrderProximalRadioButton = [None]*self.nCath
    
    for cath in range(self.nCath):
      for ch in range(self.nChannel):
        self.coilCheckBox[cath][ch] = qt.QCheckBox()
        self.coilCheckBox[cath][ch].checked = 0
        self.coilCheckBox[cath][ch].text = "CH %d" % (ch + 1)

      nChannelHalf = int(self.nChannel/2)

      coilGroup1Layout = qt.QHBoxLayout()
      for ch in range(nChannelHalf):
        coilGroup1Layout.addWidget(self.coilCheckBox[cath][ch])
      coilSelectionLayout.addRow("Cath %d Active Coils:" % cath, coilGroup1Layout)
      
      coilGroup2Layout = qt.QHBoxLayout()
      for ch in range(nChannelHalf):
        coilGroup2Layout.addWidget(self.coilCheckBox[cath][ch+nChannelHalf])
      coilSelectionLayout.addRow("", coilGroup2Layout)
        
      self.coilOrderDistalRadioButton[cath] = qt.QRadioButton("Distal First")
      self.coilOrderDistalRadioButton[cath].checked = 1
      self.coilOrderProximalRadioButton[cath] = qt.QRadioButton("Proximal First")
      self.coilOrderProximalRadioButton[cath].checked = 0
      coilOrderButtonGroup = qt.QButtonGroup()
      coilOrderButtonGroup.addButton(self.coilOrderDistalRadioButton[cath])
      coilOrderButtonGroup.addButton(self.coilOrderProximalRadioButton[cath])
      coilOrderGroupLayout = qt.QHBoxLayout()
      coilOrderGroupLayout.addWidget(self.coilOrderDistalRadioButton[cath])
      coilOrderGroupLayout.addWidget(self.coilOrderProximalRadioButton[cath])
      coilSelectionLayout.addRow("Cath %d Coil Order:" % cath, coilOrderGroupLayout)

    #--------------------------------------------------
    # Coordinate System
    #
    coordinateGroupBox = ctk.ctkCollapsibleGroupBox()
    coordinateGroupBox.title = "Coordinate System"
    coordinateGroupBox.collapsed = True
    
    catheterFormLayout.addWidget(coordinateGroupBox)
    coordinateLayout = qt.QFormLayout(coordinateGroupBox)
    
    self.coordinateRPlusRadioButton = qt.QRadioButton("+X")
    self.coordinateRMinusRadioButton = qt.QRadioButton("-X")
    self.coordinateRPlusRadioButton.checked = 1
    self.coordinateRBoxLayout = qt.QHBoxLayout()
    self.coordinateRBoxLayout.addWidget(self.coordinateRPlusRadioButton)
    self.coordinateRBoxLayout.addWidget(self.coordinateRMinusRadioButton)
    self.coordinateRGroup = qt.QButtonGroup()
    self.coordinateRGroup.addButton(self.coordinateRPlusRadioButton)
    self.coordinateRGroup.addButton(self.coordinateRMinusRadioButton)
    coordinateLayout.addRow("Right:", self.coordinateRBoxLayout)

    self.coordinateAPlusRadioButton = qt.QRadioButton("+Y")
    self.coordinateAMinusRadioButton = qt.QRadioButton("-Y")
    self.coordinateAPlusRadioButton.checked = 1
    self.coordinateABoxLayout = qt.QHBoxLayout()
    self.coordinateABoxLayout.addWidget(self.coordinateAPlusRadioButton)
    self.coordinateABoxLayout.addWidget(self.coordinateAMinusRadioButton)
    self.coordinateAGroup = qt.QButtonGroup()
    self.coordinateAGroup.addButton(self.coordinateAPlusRadioButton)
    self.coordinateAGroup.addButton(self.coordinateAMinusRadioButton)
    coordinateLayout.addRow("Anterior:", self.coordinateABoxLayout)

    self.coordinateSPlusRadioButton = qt.QRadioButton("+Z")
    self.coordinateSMinusRadioButton = qt.QRadioButton("-Z")
    self.coordinateSPlusRadioButton.checked = 1
    self.coordinateSBoxLayout = qt.QHBoxLayout()
    self.coordinateSBoxLayout.addWidget(self.coordinateSPlusRadioButton)
    self.coordinateSBoxLayout.addWidget(self.coordinateSMinusRadioButton)
    self.coordinateSGroup = qt.QButtonGroup()
    self.coordinateSGroup.addButton(self.coordinateSPlusRadioButton)
    self.coordinateSGroup.addButton(self.coordinateSMinusRadioButton)
    coordinateLayout.addRow("Superior:", self.coordinateSBoxLayout)

    #--------------------------------------------------
    # Reslice
    #
    resliceCollapsibleButton = ctk.ctkCollapsibleButton()
    resliceCollapsibleButton.text = "Image Reslice"
    self.layout.addWidget(resliceCollapsibleButton)

    #resliceLayout = qt.QFormLayout(resliceCollapsibleButton)

    self.reslice = MRTrackingReslice("Image Reslice")
    self.reslice.nCath = self.nCath
    self.reslice.buildGUI(resliceCollapsibleButton)
    
    #--------------------------------------------------
    # Point-to-Point registration
    #
    registrationCollapsibleButton = ctk.ctkCollapsibleButton()
    registrationCollapsibleButton.text = "Point-to-Point Registration"
    self.layout.addWidget(registrationCollapsibleButton)

    self.registration =  MRTrackingFiducialRegistration()
    self.registration.buildGUI(registrationCollapsibleButton)
    
    #registrationLayout = qt.QFormLayout(registrationCollapsibleButton)
    #
    #self.reg1TrackingDataSelector = slicer.qMRMLNodeComboBox()
    #self.reg1TrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    #self.reg1TrackingDataSelector.selectNodeUponCreation = True
    #self.reg1TrackingDataSelector.addEnabled = True
    #self.reg1TrackingDataSelector.removeEnabled = False
    #self.reg1TrackingDataSelector.noneEnabled = False
    #self.reg1TrackingDataSelector.showHidden = True
    #self.reg1TrackingDataSelector.showChildNodeTypes = False
    #self.reg1TrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    #self.reg1TrackingDataSelector.setToolTip( "Tracking data 1" )
    #registrationLayout.addRow("TrackingData 1: ", self.reg1TrackingDataSelector)
    #
    #self.reg2TrackingDataSelector = slicer.qMRMLNodeComboBox()
    #self.reg2TrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    #self.reg2TrackingDataSelector.selectNodeUponCreation = True
    #self.reg2TrackingDataSelector.addEnabled = True
    #self.reg2TrackingDataSelector.removeEnabled = False
    #self.reg2TrackingDataSelector.noneEnabled = False
    #self.reg2TrackingDataSelector.showHidden = True
    #self.reg2TrackingDataSelector.showChildNodeTypes = False
    #self.reg2TrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    #self.reg2TrackingDataSelector.setToolTip( "Tracking data 2" )
    #registrationLayout.addRow("TrackingData 2: ", self.reg2TrackingDataSelector)

    
    #--------------------------------------------------
    # Connections
    #--------------------------------------------------
    self.trackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataSelected)
    self.activeTrackingCheckBox.connect('toggled(bool)', self.onActiveTracking)

    for cath in range(self.nCath):
      self.tipLengthSliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onTipLengthChanged, cath))
      self.catheterDiameterSliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onCatheterDiameterChanged, cath))
      self.catheterOpacitySliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onCatheterOpacityChanged, cath))

    self.showCoilLabelCheckBox.connect('toggled(bool)', self.onCoilLabelChecked)

    for cath in range(self.nCath):
      for ch in range(self.nChannel):
        self.coilCheckBox[cath][ch].connect('toggled(bool)', self.onCoilChecked)
    
    for cath in range(self.nCath):
      self.coilOrderDistalRadioButton[cath].connect('clicked(bool)', self.onCoilChecked)
      self.coilOrderProximalRadioButton[cath].connect('clicked(bool)', self.onCoilChecked)
    
    self.coordinateRPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateRMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)

    
    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass

  def onActiveTracking(self):
    if self.activeTrackingCheckBox.checked == True:
      self.logic.activateTracking()
    else:
      self.logic.deactivateTracking()

    
  def onTrackingDataSelected(self):
    tdnode = self.trackingDataSelector.currentNode()    
    tdata = self.logic.switchCurrentTrackingData(tdnode)
    self.updateTrackingDataGUI(tdata)

    if tdata.eventTag != '':
      self.activeTrackingCheckBox.checked == True
    else:
      self.activeTrackingCheckBox.checked == False
      
      
  def onRejectRegistration(self):
    self.logic.acceptNewMatrix(self, False)


  def onTipLengthChanged(self, cath, checked):
    print("onTipLengthChanged(%d)" % cath)
    self.logic.setTipLength(self.tipLengthSliderWidget[cath].value, cath)
  
    
  def onCatheterDiameterChanged(self, cath, checked):
    self.logic.setCatheterDiameter(self.catheterDiameterSliderWidget[cath].value, cath)
    
  
  def onCatheterOpacityChanged(self, cath, checked):
    self.logic.setCatheterOpacity(self.catheterOpacitySliderWidget[cath].value, cath)

  def onCoilLabelChecked(self):
    self.logic.setShowCoilLabel(self.showCoilLabelCheckBox.checked)


  def onCoilChecked(self):
    
    activeCoils1 = [0] * self.nChannel
    activeCoils2 = [0] * self.nChannel
    for ch in range(self.nChannel):
      activeCoils1[ch] = self.coilCheckBox[0][ch].checked
      activeCoils2[ch] = self.coilCheckBox[1][ch].checked

    coilOrder1 = 'distal'
    if self.coilOrderProximalRadioButton[0].checked:
      coilOrder1 = 'proximal'
    coilOrder2 = 'distal'
    if self.coilOrderProximalRadioButton[1].checked:
      coilOrder2 = 'proximal'

    self.logic.setActiveCoils(activeCoils1, activeCoils2, coilOrder1, coilOrder2)

    
  def onSelectCoordinate(self):

    rPositive = self.coordinateRPlusRadioButton.checked
    aPositive = self.coordinateAPlusRadioButton.checked
    sPositive = self.coordinateSPlusRadioButton.checked
    
    self.logic.setAxisDirections(rPositive, aPositive, sPositive)
    
      
  def onReload(self, moduleName="MRTracking"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


  def updateTrackingDataGUI(self, tdata):
    # Enable/disable GUI components based on the state machine
    
    if self.logic.isTrackingActive():
      self.activeTrackingCheckBox.checked = True
    else:
      self.activeTrackingCheckBox.checked = False


    for cath in range(self.nCath):
      self.tipLengthSliderWidget[cath].value = tdata.tipLength[cath]
      self.catheterDiameterSliderWidget[cath].value = tdata.cmRadius[cath] * 2
      self.catheterOpacitySliderWidget[cath].value = tdata.cmOpacity[cath]
      
    self.showCoilLabelCheckBox.checked = tdata.showCoilLabel

    for ch in range(self.nChannel):
      self.coilCheckBox[0][ch].checked = tdata.activeCoils1[ch]
      self.coilCheckBox[1][ch].checked = tdata.activeCoils2[ch]
    
    if tdata.axisDirection[0] > 0.0:
      self.coordinateRPlusRadioButton.checked = 1
    else:
      self.coordinateRMinusRadioButton.checked = 1
      
    if tdata.axisDirection[1] > 0.0:
      self.coordinateAPlusRadioButton.checked = 1
    else:
      self.coordinateAMinusRadioButton.checked = 1

    if tdata.axisDirection[2] > 0.0:
      self.coordinateSPlusRadioButton.checked = 1
    else:
      self.coordinateSMinusRadioButton.checked = 1

      
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

    # CurveMaker
    self.cmLogic = CurveMaker.CurveMakerLogic()

    self.currentTrackingDataNodeID = ''
    self.TrackingData = {}


  def addNewTrackingData(self, tdnode):
    if not tdnode:
      return
    
    if tdnode.GetID() in self.TrackingData:
      print('TrackingData "%s" has already been registered.' % tdnode.GetID())
    else:
      td = TrackingData()
      td.cmLogic = self.cmLogic
      self.TrackingData[tdnode.GetID()] = td
      
      self.setupFiducials(tdnode, 0)
      self.setupFiducials(tdnode, 1)

      
  def switchCurrentTrackingData(self, tdnode):
    if not tdnode:
      return

    if not (tdnode.GetID() in self.TrackingData):
      self.addNewTrackingData(tdnode)

    self.currentTrackingDataNodeID = tdnode.GetID()
    return self.TrackingData[tdnode.GetID()]
  

  def getCurrentTrackingData(self):
    return self.TrackingData[self.currentTrackingDataNodeID]
  

  def setWidget(self, widget):
    self.widget = widget


  def setTipLength(self, length, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.tipLength[index] = length
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)


  def setCatheterDiameter(self, diameter, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.cmRadius[index] = diameter / 2.0
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)
    

  def setCatheterOpacity(self, opacity, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.cmOpacity[index] = opacity
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)

        
  def setShowCoilLabel(self, show):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.showCoilLabel = show
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)

        
  def isStringInteger(self, s):
    try:
        int(s)
        return True
    except ValueError:
        return False


  def setActiveCoils(self, coils1, coils2, coilOrder1, coilOrder2):
    #print("setActiveCoils(self, coils1, coils2, coilOrder1, coilOrder2)")
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.activeCoils1 = coils1
        td.activeCoils2 = coils2
        if coilOrder1 == 'distal':
          td.coilOrder1 = True
        else:
          td.coilOrder1 = False
        if coilOrder2 == 'distal':
          td.coilOrder2 = True
        else:
          td.coilOrder2 = False

        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)
        
    return True


  def setAxisDirections(self, rPositive, aPositive, sPositive):
    
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        if rPositive:
          td.axisDirection[0] = 1.0
        else:
          td.axisDirection[0] = -1.0
          
        if aPositive:
          td.axisDirection[1] = 1.0
        else:
          td.axisDirection[1] = -1.0
          
        if sPositive:
          td.axisDirection[2] = 1.0
        else:
          td.axisDirection[2] = -1.0

        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)
   
    
  def setupFiducials(self, tdnode, index):

    if not tdnode:
      return
    
    # Set up markups fiducial node, if specified in the connector node
    cmFiducialsID = tdnode.GetAttribute('MRTracking.cmFiducials%d' % index)
    if cmFiducialsID != None:
      self.cmLogic.CurrentSourceNode = self.scene.GetNodeByID(cmFiducialsID)
    else:
      self.cmLogic.CurrentSourceNode = None
      
    # Set up model node, if specified in the connector node
    cmModelID = tdnode.GetAttribute('MRTracking.cmModel%d' % index)
    if cmModelID != None:
      self.cmLogic.CurrentDestinationNode = self.scene.GetNodeByID(cmModelID)
      if self.cmLogic.CurrentSourceNode:
        self.cmLogic.CurrentSourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.CurrentDestinationNode.GetID())
    else:
      self.cmLogic.CurrentDestinationNode = None
      
    #if self.cmLogic.CurrentSourceNode:
    #  cnode.SetAttribute('CoilPositions', cmFiducialsID)

    td = self.TrackingData[tdnode.GetID()]
    
    # Set up tip model node
    tipModelID = tdnode.GetAttribute('MRTracking.tipModel%d' % index)
    if tipModelID != None:
      td.tipModelNode[index] = self.scene.GetNodeByID(tipModelID)
    else:
      td.tipModelNode[index] = None

    tipTransformNodeID = tdnode.GetAttribute('MRTracking.tipTransform%d' % index)
    if tipTransformNodeID != None:
      td.tipTransformNode[index] = self.scene.GetNodeByID(tipTransformNodeID)
    else:
      td.tipTransformNode[index] = None

    ## Set up incoming node, if specified in the connector node
    #incomingNodeID = tdnode.GetAttribute('MRTracking.incomingNode%d' % index)
    #if incomingNodeID != None:
    #  incomingNode = self.scene.GetNodeByID(incomingNodeID)
    #  if incomingNode:
    #      self.eventTag[incomingNodeID] = incomingNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
    #tdnode.eventTag = incomingNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
    

  def onIncomingNodeModifiedEvent(self, caller, event):
    
    parentID = caller.GetAttribute('MRTracking.parent')
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)
    
    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      self.updateCatheterNode(tdnode, 0)
      self.updateCatheterNode(tdnode, 1)

      
  def updateCatheterNode(self, tdnode, index):
    #print("updateCatheterNode(%s, %d) is called" % (tdnode.GetID(), index) )
    # node shoud be vtkMRMLIGTLTrackingDataBundleNode

    fiducialNode = None

    cathName = 'Catheter_%d' % index

    ## Catheter 1
    fiducialNodeID = tdnode.GetAttribute(cathName)
    if fiducialNodeID != None:
      fiducialNode = self.scene.GetNodeByID(fiducialNodeID)
    
    if fiducialNode == None:
      fiducialNode = self.scene.CreateNodeByClass("vtkMRMLMarkupsFiducialNode")
      fiducialNode.SetLocked(True)
      fiducialNode.SetName('CoilGroup_%d' % index)
      self.scene.AddNode(fiducialNode)
      fiducialNodeID = fiducialNode.GetID()
      tdnode.SetAttribute(cathName, fiducialNodeID)
      
    self.cmLogic.CurrentSourceNode = fiducialNode

    # Check if the curve model exists; if not, create one.
    destinationNode = None
    nodeID = self.cmLogic.CurrentSourceNode.GetAttribute('CurveMaker.CurveModel')
    if nodeID:
      destinationNode = self.scene.GetNodeByID(nodeID)
    if destinationNode == None:
      destinationNode = self.scene.CreateNodeByClass("vtkMRMLModelNode")
      destinationNode.SetName('Catheter')
      self.scene.AddNode(destinationNode)
      #self.scene.AddNode(modelDisplayNode)
      
    self.cmLogic.CurrentDestinationNode = destinationNode

    if self.cmLogic.CurrentDestinationNode:
      tdnode.SetAttribute('MRTracking.cmModel%d' % index, self.cmLogic.CurrentDestinationNode.GetID())
    if self.cmLogic.CurrentSourceNode:
      tdnode.SetAttribute('MRTracking.cmFiducials%d' % index, self.cmLogic.CurrentSourceNode.GetID())
        
    if self.cmLogic.CurrentDestinationNode and self.cmLogic.CurrentSourceNode:
      self.cmLogic.CurrentSourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.CurrentDestinationNode.GetID())
              
    # Update coordinates in the fiducial node.
    nCoils = tdnode.GetNumberOfTransformNodes()
    td = self.TrackingData[tdnode.GetID()]
    mask = td.activeCoils1[0:nCoils]
    if index == 1:
      mask = td.activeCoils2[0:nCoils]
    nActiveCoils = sum(mask)
    if fiducialNode.GetNumberOfFiducials() != nActiveCoils:
      fiducialNode.RemoveAllMarkups()
      for i in range(nActiveCoils):
        fiducialNode.AddFiducial(0.0, 0.0, 0.0)
    j = 0

    # Max. number of coils is 8.
    if nCoils > 8:
      nCoils = 8
      
    for i in range(nCoils):
      if mask[i]:
        tnode = tdnode.GetTransformNode(i)
        trans = tnode.GetTransformToParent()
        #fiducialNode.SetNthFiducialPositionFromArray(j, trans.GetPosition())
        v = trans.GetPosition()
        coilID = j
        if index == 0 and td.coilOrder1 == False:
          coilID = nCoils - j - 1
        if index == 1 and td.coilOrder2 == False:
          coilID = nCoils - j - 1
        fiducialNode.SetNthFiducialPosition(coilID, v[0] * td.axisDirection[0], v[1] * td.axisDirection[1], v[2] * td.axisDirection[2])
        j += 1
      
    self.updateCatheter(tdnode, index)


  def updateCatheter(self, tdnode, index):

    if tdnode == None:
      return
    
    cmFiducialsID = tdnode.GetAttribute('MRTracking.cmFiducials%d' % index)
    if cmFiducialsID == None:
      return

    sourceNode = self.scene.GetNodeByID(cmFiducialsID)

    if sourceNode == None:
      return

    cmModelID = sourceNode.GetAttribute('CurveMaker.CurveModel')
    if cmModelID == None:
      return
    
    destinationNode = self.scene.GetNodeByID(cmModelID)

    td = self.TrackingData[tdnode.GetID()]
    
    modelDisplayNode = destinationNode.GetDisplayNode()
    if modelDisplayNode:
      modelDisplayNode.SetColor(td.cmModelColor[index])
      modelDisplayNode.SetOpacity(td.cmOpacity[index])
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetSliceDisplayModeToIntersection()

    # Update catheter using the CurveMaker module
    self.cmLogic.setTubeRadius(td.cmRadius[index], sourceNode)
    self.cmLogic.enableAutomaticUpdate(1, sourceNode)
    self.cmLogic.setInterpolationMethod('cardinal', sourceNode)
    self.cmLogic.updateCurve()

    # Skip if the model has not been created. (Don't call this section before self.cmLogic.updateCurve()
    if not (sourceNode.GetID() in self.cmLogic.CurvePoly) or (self.cmLogic.CurvePoly[sourceNode.GetID()] == None):
      return
    
    # Show/hide fiducials for coils
    fiducialDisplayNode = sourceNode.GetDisplayNode()
    if fiducialDisplayNode:
      fiducialDisplayNode.SetVisibility(td.showCoilLabel)

    # Add a extended tip
    ## make sure that there is more than one points
    if sourceNode.GetNumberOfFiducials() < 2:
      return
    
    curvePoly = self.cmLogic.CurvePoly[sourceNode.GetID()]
    lines = curvePoly.GetLines()
    points = curvePoly.GetPoints()
    pts = vtk.vtkIdList()
    
    lines.GetCell(0, pts)
    n = pts.GetNumberOfIds()
    if n > 1:
      p0 = numpy.array(points.GetPoint(pts.GetId(0)))
      p1 = numpy.array(points.GetPoint(pts.GetId(1)))
      v10 = p0 - p1
      n10 = v10 / numpy.linalg.norm(v10) # Normal vector at the tip
      pe = p0 + n10 * td.tipLength[index]

      ## Calculate rotation matrix
      ## Check if <n10> is not parallel to <s>=(0.0, 1.0, 0.0)
      s = numpy.array([0.0, 1.0, 0.0])
      t = numpy.array([1.0, 0.0, 0.0])
      if n10[1] < 0.95:
        t = numpy.cross(s, n10)
        s = numpy.cross(n10, t)
      else:
        s = numpy.cross(n10, t)
        t = numpy.cross(s, n10)

    if td.tipPoly[index]==None:
      td.tipPoly[index] = vtk.vtkPolyData()

    if td.tipModelNode[index] == None:
      td.tipModelNode[index] = self.scene.CreateNodeByClass('vtkMRMLModelNode')
      td.tipModelNode[index].SetName('Tip')
      self.scene.AddNode(td.tipModelNode[index])
      tdnode.SetAttribute('MRTracking.tipModel%d' % index, td.tipModelNode[index].GetID())
        
    if td.tipTransformNode[index] == None:
      td.tipTransformNode[index] = self.scene.CreateNodeByClass('vtkMRMLLinearTransformNode')
      td.tipTransformNode[index].SetName('TipTransform')
      self.scene.AddNode(td.tipTransformNode[index])
      tdnode.SetAttribute('MRTracking.tipTransform%d' % index, td.tipTransformNode[index].GetID())

    matrix = vtk.vtkMatrix4x4()
    matrix.SetElement(0, 0, t[0])
    matrix.SetElement(1, 0, t[1])
    matrix.SetElement(2, 0, t[2])
    matrix.SetElement(0, 1, s[0])
    matrix.SetElement(1, 1, s[1])
    matrix.SetElement(2, 1, s[2])
    matrix.SetElement(0, 2, n10[0])
    matrix.SetElement(1, 2, n10[1])
    matrix.SetElement(2, 2, n10[2])
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    td.tipTransformNode[index].SetMatrixTransformToParent(matrix)
    
    self.updateTipModelNode(td.tipModelNode[index], td.tipPoly[index], p0, pe, td.cmRadius[index], td.cmModelColor[index], td.cmOpacity[index])


  def updateTipModelNode(self, tipModelNode, poly, p0, pe, radius, color, opacity):
    #tipModel = self.scene.CreateNodeByClass('vtkMRMLModelNode')

    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    points.SetNumberOfPoints(2)
    cellArray.InsertNextCell(2)
    
    points.SetPoint(0, p0)
    cellArray.InsertCellPoint(0)
    points.SetPoint(1, pe)
    cellArray.InsertCellPoint(1)

    poly.Initialize()
    poly.SetPoints(points)
    poly.SetLines(cellArray)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetInputData(poly)
    tubeFilter.SetRadius(radius)
    tubeFilter.SetNumberOfSides(20)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius*2.0)
    sphere.SetCenter(pe)
    sphere.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tubeFilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tubeFilter.GetOutputPort())
    apd.Update()
    
    tipModelNode.SetAndObservePolyData(apd.GetOutput())
    tipModelNode.Modified()

    tipDispID = tipModelNode.GetDisplayNodeID()
    if tipDispID == None:
      tipDispNode = self.scene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      self.scene.AddNode(tipDispNode)
      tipDispNode.SetScene(self.scene)
      tipModelNode.SetAndObserveDisplayNodeID(tipDispNode.GetID());
      tipDispID = tipModelNode.GetDisplayNodeID()
      
    tipDispNode = self.scene.GetNodeByID(tipDispID)
      
    tipDispNode.SetColor(color)
    tipDispNode.SetOpacity(opacity)
    tipDispNode.SliceIntersectionVisibilityOn()
    tipDispNode.SetSliceDisplayModeToIntersection()
    

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

  def activateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    
    if tdnode:
      print("Observer added.")
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        childNode = tdnode.GetTransformNode(0)
        childNode.SetAttribute('MRTracking.parent', tdnode.GetID())
        td.eventTag = childNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        return True
      else:
        return False  # Could not add observer.

  
  def deactivateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    if tdnode:
      if tdnode.GetNumberOfTransformNodes() > 0 and td.eventTag != '':
        childNode = tdnode.GetTransformNode(0)
        childNode.RemoveObserver(td.eventTag)
        td.eventTag = ''
        return True
      else:
        return False

  def isTrackingActive(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    return td.isActive()
    
      
