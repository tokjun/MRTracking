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
    This work is supported by NIH (5R01EB022011, P41EB015898, R01EB020667).
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
    self.reloadButton.name = "Reload"
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


    #self.tipLengthSliderWidget = [None] * self.nCath
    self.catheterDiameterSliderWidget = [None] * self.nCath
    self.catheterOpacitySliderWidget = [None] * self.nCath
    self.catheterRegUseCoilCheckBox = [None] * self.nCath
    self.catheterRegPointsLineEdit = [None] * self.nCath
    
    for cath in range(self.nCath):
      
      ##
      ## Tip Length (legnth between the catheter tip and the first coil)
      ##
      #self.tipLengthSliderWidget[cath] = ctk.ctkSliderWidget()
      #self.tipLengthSliderWidget[cath].singleStep = 0.5
      #self.tipLengthSliderWidget[cath].minimum = 0.0
      #self.tipLengthSliderWidget[cath].maximum = 100.0
      #self.tipLengthSliderWidget[cath].value = 10.0
      #self.tipLengthSliderWidget[cath].setToolTip("Set the length of the catheter tip.")
      #configFormLayout.addRow("Cath %d Tip Length (mm): " % cath, self.tipLengthSliderWidget[cath])
      
      #
      # Catheter #cath Catheter diameter
      #
      self.catheterDiameterSliderWidget[cath] = ctk.ctkSliderWidget()
      self.catheterDiameterSliderWidget[cath].singleStep = 0.1
      self.catheterDiameterSliderWidget[cath].minimum = 0.1
      self.catheterDiameterSliderWidget[cath].maximum = 10.0
      self.catheterDiameterSliderWidget[cath].value = 1.0
      self.catheterDiameterSliderWidget[cath].setToolTip("Set the diameter of the catheter")
      configFormLayout.addRow("Cath %d Diameter (mm): " % cath, self.catheterDiameterSliderWidget[cath])
      
      #
      # Catheter #cath Catheter opacity
      #
      self.catheterOpacitySliderWidget[cath] = ctk.ctkSliderWidget()
      self.catheterOpacitySliderWidget[cath].singleStep = 0.1
      self.catheterOpacitySliderWidget[cath].minimum = 0.0
      self.catheterOpacitySliderWidget[cath].maximum = 1.0
      self.catheterOpacitySliderWidget[cath].value = 1.0
      self.catheterOpacitySliderWidget[cath].setToolTip("Set the opacity of the catheter")
      configFormLayout.addRow("Cath %d Opacity: " % cath, self.catheterOpacitySliderWidget[cath])

      #
      # Catheter #cath "Use coil positions for registration" check box
      #
      self.catheterRegUseCoilCheckBox[cath] = qt.QCheckBox()
      self.catheterRegUseCoilCheckBox[cath].checked = 1
      self.catheterRegUseCoilCheckBox[cath].enabled = 1
      self.catheterRegUseCoilCheckBox[cath].setToolTip("Activate Tracking")
      configFormLayout.addRow("Cath %d Use Coil Pos: " % cath, self.catheterRegUseCoilCheckBox[cath])
      
      #
      # Catheter #cath registration points
      #
      #  Format: (<coil index>,<offset>),(<coil index>,<offset>),...
      # 
      self.catheterRegPointsLineEdit[cath] = qt.QLineEdit()
      self.catheterRegPointsLineEdit[cath].text = '5.0,10.0,15.0,20.0'
      self.catheterRegPointsLineEdit[cath].readOnly = False
      self.catheterRegPointsLineEdit[cath].frame = True
      self.catheterRegPointsLineEdit[cath].styleSheet = "QLineEdit { background:transparent; }"
      configFormLayout.addRow("Cath %d Reg. Points: " % cath, self.catheterRegPointsLineEdit[cath])

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
    self.coilOrderButtonGroup = [None]*self.nCath
    
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
      self.coilOrderButtonGroup[cath] = qt.QButtonGroup()
      self.coilOrderButtonGroup[cath].addButton(self.coilOrderDistalRadioButton[cath])
      self.coilOrderButtonGroup[cath].addButton(self.coilOrderProximalRadioButton[cath])
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
    # Stabilizer
    #
    stabilizerGroupBox = ctk.ctkCollapsibleGroupBox()
    stabilizerGroupBox.title = "Stabilizer"
    stabilizerGroupBox.collapsed = True
    
    catheterFormLayout.addWidget(stabilizerGroupBox)
    stabilizerLayout = qt.QFormLayout(stabilizerGroupBox)
    
    self.cutoffFrequencySliderWidget = ctk.ctkSliderWidget()
    self.cutoffFrequencySliderWidget.singleStep = 0.1
    self.cutoffFrequencySliderWidget.minimum = 0.10
    self.cutoffFrequencySliderWidget.maximum = 50.0
    self.cutoffFrequencySliderWidget.value = 7.5
    #self.cutoffFrequencySliderWidget.setToolTip("")
    stabilizerLayout.addRow("Cut-off frequency: ",  self.cutoffFrequencySliderWidget)
    
    
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
    self.registration.setMRTrackingLogic(self.logic)
    self.logic.setRegistration(self.registration)

    
    #--------------------------------------------------
    # Connections
    #--------------------------------------------------
    self.trackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataSelected)
    self.activeTrackingCheckBox.connect('toggled(bool)', self.onActiveTracking)

    for cath in range(self.nCath):
      ## JT: I'd leave this widget in the comment, because it might be useful to show the predicted in the future.
      #self.tipLengthSliderWidget[cath].connect("valueChanged(double)", functools.partial(self.onTipLengthChanged, cath))
      self.catheterRegPointsLineEdit[cath].editingFinished.connect(functools.partial(self.onCatheterRegPointsChanged, cath))
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

    self.cutoffFrequencySliderWidget.connect("valueChanged(double)", self.onStabilizerCutoffChanged)
    
    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass

  
  def enableCoilSelection(self, switch):
    
    if switch:
      for cath in range(self.nCath):
        for ch in range(self.nChannel):
          self.coilCheckBox[cath][ch].enabled = 1
    else:
      for cath in range(self.nCath):
        for ch in range(self.nChannel):
          self.coilCheckBox[cath][ch].enabled = 0

          
  def onActiveTracking(self):
    if self.activeTrackingCheckBox.checked == True:
      self.enableCoilSelection(0)
      self.logic.activateTracking()

    else:
      self.enableCoilSelection(1)
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

  #def onTipLengthChanged(self, cath, checked):
  #  print("onTipLengthChanged(%d)" % cath)
  #  self.logic.setTipLength(self.tipLengthSliderWidget[cath].value, cath)
  
  def onCatheterRegPointsChanged(self, cath):
    text = self.catheterRegPointsLineEdit[cath].text
    print("onCatheterRegPointsChanged(%d, %s)" % (cath, text))

    strarray = text.split(',')
    try:
      array = [float(ns) for ns in strarray]
      self.logic.setCoilPositions(cath, array, True)
    except ValueError:
      print('Format error in coil position string.')

      
  def onCatheterDiameterChanged(self, cath, checked):
    self.logic.setCatheterDiameter(self.catheterDiameterSliderWidget[cath].value, cath)
    
  
  def onCatheterOpacityChanged(self, cath, checked):
    self.logic.setCatheterOpacity(self.catheterOpacitySliderWidget[cath].value, cath)

  def onCoilLabelChecked(self):
    self.logic.setShowCoilLabel(self.showCoilLabelCheckBox.checked)


  def onCoilChecked(self):
    
    activeCoils0 = [0] * self.nChannel
    activeCoils1 = [0] * self.nChannel
    for ch in range(self.nChannel):
      activeCoils0[ch] = self.coilCheckBox[0][ch].checked
      activeCoils1[ch] = self.coilCheckBox[1][ch].checked

    coilOrder0 = 'distal'
    if self.coilOrderProximalRadioButton[0].checked:
      coilOrder0 = 'proximal'
    coilOrder1 = 'distal'
    if self.coilOrderProximalRadioButton[1].checked:
      coilOrder1 = 'proximal'

    self.logic.setActiveCoils(activeCoils0, activeCoils1, coilOrder0, coilOrder1)

    
  def onSelectCoordinate(self):

    rPositive = self.coordinateRPlusRadioButton.checked
    aPositive = self.coordinateAPlusRadioButton.checked
    sPositive = self.coordinateSPlusRadioButton.checked
    
    self.logic.setAxisDirections(rPositive, aPositive, sPositive)

    
  def onStabilizerCutoffChanged(self):

    frequency = self.cutoffFrequencySliderWidget.value
    self.logic.setStabilizerCutoff(frequency)

    
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
      #self.tipLengthSliderWidget[cath].value = tdata.tipLength[cath]
      self.catheterDiameterSliderWidget[cath].value = tdata.radius[cath] * 2.0
      self.catheterOpacitySliderWidget[cath].value = tdata.opacity[cath]

      str = ""
      for p in tdata.coilPositions[cath]:
        str += "%.f," % p
      self.catheterRegPointsLineEdit[cath].text = str[:-1] # Remove the last ','
      
    self.showCoilLabelCheckBox.checked = tdata.showCoilLabel
    

    for ch in range(self.nChannel):
      self.coilCheckBox[0][ch].checked = tdata.activeCoils[0][ch]
      self.coilCheckBox[1][ch].checked = tdata.activeCoils[1][ch]
    
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
    
    self.widget = None

    self.eventTag = {}

    self.currentTrackingDataNodeID = ''
    self.TrackingData = {}

    self.registration = None

    #self.dataProcessingTimer = qt.QTimer(self)

    # Create a parameter node
    self.parameterNode = self.getParameterNode()
    #self.parameterNode.SetParameter("a", str(a))

    # Add observers
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAddedEvent)
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    
  def setRegistration(self, reg):
    self.registration = reg
    self.registration.trackingData = self.TrackingData
  
    
  def addNewTrackingData(self, tdnode):
    if not tdnode:
      return
    
    if tdnode.GetID() in self.TrackingData:
      print('TrackingData "%s" has already been registered.' % tdnode.GetID())
    else:
      td = TrackingData()
      self.TrackingData[tdnode.GetID()] = td
      self.TrackingData[tdnode.GetID()].setID(tdnode.GetID())
      self.TrackingData[tdnode.GetID()].setLogic(self)
      
      self.TrackingData[tdnode.GetID()].loadConfig()
      
      self.setupFiducials(tdnode, 0)
      self.setupFiducials(tdnode, 1)

      self.setTipLength(td.coilPositions[0][0], 0)  # The first coil position match the tip length
      self.setTipLength(td.coilPositions[1][0], 1)  # The first coil position match the tip length            
      
      
  def switchCurrentTrackingData(self, tdnode):
    if not tdnode:
      return

    self.currentTrackingDataNodeID = tdnode.GetID()
    
    if not (tdnode.GetID() in self.TrackingData):
      self.addNewTrackingData(tdnode)

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
        #td.tipLength[index] = length
        td.setTipLength(index, length)
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)

        
  def setCoilPositions(self, index, array, save=False):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        if len(array) <= len(td.coilPositions[index]):
          td.coilPositions[index] = array
          #i = 0
          #for p in array:
          #  td.coilPositions[index][i] = p
          #  td.setCoilPositions(index, p)
          #  i = i + 1
        print(td.coilPositions)
        # Make sure that the registration class instance references the tracking data
        self.registration.trackingData = self.TrackingData
        self.setTipLength(td.coilPositions[index][0], index)  # The first coil position match the tip length

      if save:
        # Save configuration
        tdnode = slicer.mrmlScene.GetNodeByID(nodeID)
        if tdnode:
          name = tdnode.GetName()
          value = td.coilPositions[index]
          settings = qt.QSettings()
          settings.setValue(self.widget.moduleName + '/' + 'CoilConfig.' + str(name) + '.' + str(index), value)
        

  def setCatheterDiameter(self, diameter, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        #td.radius[index] = diameter / 2.0
        td.setRadius(index, diameter / 2.0)
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)
    

  def setCatheterOpacity(self, opacity, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        #td.opacity[index] = opacity
        td.setOpacity(index, opacity)
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)

        
  def setShowCoilLabel(self, show):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        #td.showCoilLabel = show
        td.setShowCoilLabel(show)
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)

        
  def isStringInteger(self, s):
    try:
        int(s)
        return True
    except ValueError:
        return False


  def setActiveCoils(self, coils0, coils1, coilOrder0, coilOrder1):
    #print("setActiveCoils(self, coils1, coils2, coilOrder1, coilOrder2)")
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        #td.activeCoils1 = coils1
        #td.activeCoils2 = coils2
        td.setActiveCoils(0, coils0)
        td.setActiveCoils(1, coils1)
        
        if coilOrder0 == 'distal':
          #td.coilOrder1 = True
          td.setCoilOrder(0, True)
        else:
          #td.coilOrder1 = False
          td.setCoilOrder(0, False)
        if coilOrder1 == 'distal':
          #td.coilOrder2 = True
          td.setCoilOrder(1, True)
        else:
          #td.coilOrder2 = False
          td.setCoilOrder(1, False)

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
          #td.axisDirection[0] = 1.0
          td.setAxisDirection(0, 1.0)
        else:
          #td.axisDirection[0] = -1.0
          td.setAxisDirection(0, -1.0)
          
        if aPositive:
          #td.axisDirection[1] = 1.0
          td.setAxisDirection(1, 1.0)
        else:
          #td.axisDirection[1] = -1.0
          td.setAxisDirection(1, -1.0)
          
        if sPositive:
          #td.axisDirection[2] = 1.0
          td.setAxisDirection(2, 1.0)
        else:
          #td.axisDirection[2] = -1.0
          td.setAxisDirection(2, 1.0)

        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 0)
        self.updateCatheter(tnode, 1)
   
    
  def setupFiducials(self, tdnode, index):

    if not tdnode:
      return
    
    # Set up markups fiducial node, if specified in the connector node
    curveNodeID = tdnode.GetAttribute('MRTracking.CurveNode%d' % index)
    curveNode = None

    #cathName = 'Catheter_%d' % index
    
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)
    else:
      curveNode = self.scene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      ## TODO: Name?
      tdnode.SetAttribute('MRTracking.CurveNode%d' % index, curveNode.GetID())

    td = self.TrackingData[tdnode.GetID()]
    
    # Set up tip model node
    tipModelID = tdnode.GetAttribute('MRTracking.tipModel%d' % index)
    if tipModelID != None:
      #td.tipModelNode[index] = self.scene.GetNodeByID(tipModelID)
      td.setTipModelNode(index, self.scene.GetNodeByID(tipModelID))
    else:
      #td.tipModelNode[index] = None
      td.setTipModelNode(index, None)

    tipTransformNodeID = tdnode.GetAttribute('MRTracking.tipTransform%d' % index)
    if tipTransformNodeID != None:
      #td.tipTransformNode[index] = self.scene.GetNodeByID(tipTransformNodeID)
      td.setTipTransformNode(index, self.scene.GetNodeByID(tipTransformNodeID))
    else:
      #td.tipTransformNode[index] = None
      td.setTipTransformNode(index, None)
      

  def onIncomingNodeModifiedEvent(self, caller, event):

    parentID = caller.GetAttribute('MRTracking.parent')
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)

    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      # Update coordinates in the fiducial node.
      nCoils = tdnode.GetNumberOfTransformNodes()
      td = self.TrackingData[tdnode.GetID()]
      fUpdate = False
      if nCoils > 0:
        # Update timestamp
        # TODO: Should we check all time stamps under the tracking node?
        tnode = tdnode.GetTransformNode(0)
        mTime = tnode.GetTransformToWorldMTime()
        if mTime > td.lastMTime:
          currentTime = time.time()
          td.lastMTime = mTime
          td.lastTS = currentTime
          fUpdate = True
      
      self.updateCatheterNode(tdnode, 0)
      self.updateCatheterNode(tdnode, 1)

      if fUpdate:
        self.registration.updatePoints()

        
  #def processIncomingNodes(self):
  #  print('processIncomingNodes()')
  #  pass
    
      
  def updateCatheterNode(self, tdnode, index):
    #print("updateCatheterNode(%s, %d) is called" % (tdnode.GetID(), index) )
    # node shoud be vtkMRMLIGTLTrackingDataBundleNode

    curveNodeID = tdnode.GetAttribute('MRTracking.CurveNode%d' % index)
    curveNode = None
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)

    if curveNode == None:
      curveNode = self.scene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      tdnode.SetAttribute('MRTracking.CurveNode%d' % index, curveNode.GetID())
    
    prevState = curveNode.StartModify()

    # Update coordinates in the fiducial node.
    nCoils = tdnode.GetNumberOfTransformNodes()
  
    if nCoils > 8: # Max. number of coils is 8.
      nCoils = 8
      
    td = self.TrackingData[tdnode.GetID()]

    mask = td.activeCoils[0][0:nCoils]
    
    # Update time stamp
    ## TODO: Ideally, the time stamp should come from the data source rather than 3D Slicer.
    curveNode.SetAttribute('MRTracking.lastTS', '%f' % td.lastTS)
    
    if index == 1:
      mask = td.activeCoils[1][0:nCoils]
    nActiveCoils = sum(mask)
    
    if curveNode.GetNumberOfControlPoints() != nActiveCoils:
      curveNode.RemoveAllControlPoints()
      for i in range(nActiveCoils):
        p = vtk.vtkVector3d()
        p.SetX(0.0)
        p.SetY(0.0)
        p.SetZ(0.0)
        curveNode.AddControlPoint(p, "P_%d" % i)
        
    lastCoil = nCoils - 1
    fFlip = False
    if index == 0:
      fFlip = (not td.coilOrder[0])
    else: # index == 1:
      fFlip = (not td.coilOrder[1])

    j = 0
    for i in range(nCoils):
      if mask[i]:
        #tnode = tdnode.GetTransformNode(i)
        tnode = td.filteredTransformNodes[i]
        trans = tnode.GetTransformToParent()
        v = trans.GetPosition()
        
        # Apply the registration transform, if activated. (GUI is defined in registration.py)
        if self.registration and self.registration.applyTransform and (self.registration.applyTransform.GetID() == tdnode.GetID()):
          if self.registration.registrationTransform:
            v = self.registration.registrationTransform.TransformPoint(v)

        coilID = j
        if fFlip:
          coilID = lastCoil - j
        curveNode.SetNthControlPointPosition(coilID, v[0] * td.axisDirection[0], v[1] * td.axisDirection[1], v[2] * td.axisDirection[2])
        j += 1

    #print('curveNode.GetNumberOfPointsPerInterpolatingSegment(): %d' % curveNode.GetNumberOfPointsPerInterpolatingSegment())
    curveNode.EndModify(prevState)
    
    self.updateCatheter(tdnode, index)

    
  def updateCatheter(self, tdnode, index):

    if tdnode == None:
      return
    
    curveNode = None
    curveNodeID = tdnode.GetAttribute('MRTracking.CurveNode%d' % index)
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)

    if curveNode == None:
      return

    td = self.TrackingData[tdnode.GetID()]

    curveDisplayNode = curveNode.GetDisplayNode()
    if curveDisplayNode:
      prevState = curveDisplayNode.StartModify()
      curveDisplayNode.SetSelectedColor(td.modelColor[index])
      curveDisplayNode.SetColor(td.modelColor[index])
      curveDisplayNode.SetOpacity(td.opacity[index])
      #curveDisplayNode.SliceIntersectionVisibilityOn()
      curveDisplayNode.Visibility2DOn()
      curveDisplayNode.EndModify(prevState)
      # Show/hide labels for coils
      curveDisplayNode.SetPointLabelsVisibility(td.showCoilLabel);
      curveDisplayNode.SetUseGlyphScale(False)
      curveDisplayNode.SetGlyphSize(td.radius[index]*4.0)
      curveDisplayNode.SetLineThickness(0.5)  # Thickness is defined as a scale from the glyph size.
    
    # Add a extended tip
    # make sure that there is more than one points
    if curveNode.GetNumberOfControlPoints() < 2:
      return

    if td.tipPoly[index]==None:
      td.tipPoly[index] = vtk.vtkPolyData()
    
    if td.tipModelNode[index] == None:
      td.tipModelNode[index] = self.scene.AddNewNodeByClass('vtkMRMLModelNode')
      td.tipModelNode[index].SetName('Tip')
      tdnode.SetAttribute('MRTracking.tipModel%d' % index, td.tipModelNode[index].GetID())
        
    if td.tipTransformNode[index] == None:
      td.tipTransformNode[index] = self.scene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
      td.tipTransformNode[index].SetName('TipTransform')
      tdnode.SetAttribute('MRTracking.tipTransform%d' % index, td.tipTransformNode[index].GetID())

    ## The 'curve end point matrix' (normal vectors + the curve end position)
    matrix = vtk.vtkMatrix4x4()
    
    ## Assuming that the tip is at index=0 
    n10 = [0.0, 0.0, 0.0]
    p0  = [0.0, 0.0, 0.0]
    cpi = curveNode.GetCurvePointIndexFromControlPointIndex(0)

    curveNode.GetNthControlPointPosition(0, p0)
    curveNode.GetCurvePointToWorldTransformAtPointIndex(cpi, matrix)
    n10[0] = matrix.GetElement(0, 2)
    n10[1] = matrix.GetElement(1, 2)
    n10[2] = matrix.GetElement(2, 2)

    # Tip location
    # The sign for the normal vector is '-' because the normal vector point toward points
    # with larger indecies.
    pe = numpy.array(p0) - numpy.array(n10) * td.tipLength[index]
  
    self.updateTipModelNode(td.tipModelNode[index], td.tipPoly[index], p0, pe, td.radius[index], td.modelColor[index], td.opacity[index])

    ## Update the 'catheter tip matrix' (normal vectors + the catheter tip position)
    ## Note that the catheter tip matrix is different from the curve end matrix
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    td.tipTransformNode[index].SetMatrixTransformToParent(matrix)
    
    #matrix = vtk.vtkMatrix4x4()
    #matrix.DeepCopy((t[0], s[0], n10[0], pe[0],
    #                 t[1], s[1], n10[1], pe[1],
    #                 t[2], s[2], n10[2], pe[2],
    #                 0, 0, 0, 1))

    
  def updateTipModelNode(self, tipModelNode, poly, p0, pe, radius, color, opacity):

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
      tipDispNode = self.scene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
      tipDispNode.SetScene(self.scene)
      tipModelNode.SetAndObserveDisplayNodeID(tipDispNode.GetID());
      tipDispID = tipModelNode.GetDisplayNodeID()
      
    tipDispNode = self.scene.GetNodeByID(tipDispID)

    prevState = tipDispNode.StartModify()
    tipDispNode.SetColor(color)
    tipDispNode.SetOpacity(opacity)
    #tipDispNode.SliceIntersectionVisibilityOn()
    tipDispNode.Visibility2DOn()
    tipDispNode.SetSliceDisplayModeToIntersection()
    tipDispNode.EndModify(prevState)


  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAddedEvent(self, caller, eventId, callData):
    print("Node added")
    print("New node: {0}".format(callData.GetName()))
        
    if callData.GetAttribute("ModuleName") == self.moduleName:
      print ("parameterNode added!!!!!!")


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


  #
  # To fileter the transforms under the TrackingDataBundleNode, prepare transform nodes
  # to store the filtered transforms.
  def setFilteredTransforms(self, tdnode):
    td = self.TrackingData[tdnode.GetID()]

    nTransforms =  tdnode.GetNumberOfTransformNodes()
    for i in range(nTransforms):
      inputNode = tdnode.GetTransformNode(i)
      if td.filteredTransformNodes[i] == None:
        td.filteredTransformNodes[i] = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
      if td.transformProcessorNodes[i] == None:
        td.transformProcessorNodes[i] = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformProcessorNode')

      td.filteredTransformNodes[i].SetName('%s_filtered' % inputNode.GetName())
      
      tpnode = td.transformProcessorNodes[i]
      tpnode.SetProcessingMode(slicer.vtkMRMLTransformProcessorNode.PROCESSING_MODE_STABILIZE)
      tpnode.SetStabilizationCutOffFrequency(7.50)
      tpnode.SetStabilizationEnabled(1)
      tpnode.SetUpdateModeToAuto()
      tpnode.SetAndObserveInputUnstabilizedTransformNode(inputNode)
      tpnode.SetAndObserveOutputTransformNode(td.filteredTransformNodes[i])
    
      
  def activateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)

    #
    # The following section adds an observer invoked by an NodeModifiedEvent
    # NOTE on 09/10/2020: This mechanism does not work well for the tracker stabilizer. 
    #
    
    if tdnode:
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        # Create transform nodes for filtered tracking data
        self.setFilteredTransforms(tdnode)

        ## TODO: Using the first node to trigger the event may cause a timing issue.
        ## TODO: Using the filtered transform node will invoke the event handler every 15 ms as fixed in
        ##       TrackerStabilizer module. It is not guaranteed that every tracking data is used when
        ##       the tracking frame rate is higher than 66.66 fps (=1000ms/15ms). 
        #childNode = tdnode.GetTransformNode(0)
        childNode = td.filteredTransformNodes[0]
        
        childNode.SetAttribute('MRTracking.parent', tdnode.GetID())
        td.eventTag = childNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        print("Observer for TrackingDataBundleNode added.")
        return True
      else:
        return False  # Could not add observer.

    ##
    ## The following section adds a timer-driven observer
    ## NOTE: The timer interval is set to 15 ms as assumed in TrackerStabilizer (see vtkSlicerTrackerStabilizerLogic.cxx)
    #if tdnode:
    #  if self.dataProcessingTimer.isActive() == False:
    #    self.dataProcessingTimer.timeout.connect(self.processIncomingNodes)
    #    self.dataProcessingTimer.start(15)
    #    print("Timer started")
    #    return True
    #  else:
    #    return False  # Could not add observer.
    
      
  
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

      
  def setStabilizerCutoff(self, frequency):
    
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    if td and tdnode:
      nTransforms = tdnode.GetNumberOfTransformNodes()
      for i in range(nTransforms):
        tpnode = td.transformProcessorNodes[i]
        tpnode.SetStabilizationCutOffFrequency(frequency)

      
  def isTrackingActive(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    return td.isActive()
    
      
