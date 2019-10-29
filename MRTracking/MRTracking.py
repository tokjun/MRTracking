import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy

import CurveMaker
    
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
    self.parent.contributors = ["Junichi Tokuda, Wei Wang, Ehud Schmidt (BWH)"]
    self.parent.helpText = """
    Visualization of MR-tracked catheter. 
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH (P41EB015898, R01EB020667).
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
    # Connection Area
    #
    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "Connection (OpenIGTLink)"
    self.layout.addWidget(connectionCollapsibleButton)

    # Layout within the dummy collapsible button
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

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
    connectionFormLayout.addRow("Connector: ", self.connectorSelector)
    
    #self.connectorAddressLineEdit = qt.QLineEdit()
    #self.connectorAddressLineEdit.text = "localhost"
    #self.connectorAddressLineEdit.readOnly = False
    #self.connectorAddressLineEdit.frame = True
    #self.connectorAddressLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    #self.connectorAddressLineEdit.cursor = qt.QCursor(qt.Qt.IBeamCursor)
    #connectionFormLayout.addRow("Address: ", self.connectorAddressLineEdit)

    self.connectorPort = qt.QSpinBox()
    self.connectorPort.objectName = 'PortSpinBox'
    self.connectorPort.setMaximum(64000)
    self.connectorPort.setValue(18944)
    self.connectorPort.setToolTip("Port number of the server")
    connectionFormLayout.addRow("Port: ", self.connectorPort)

    #
    # check box to trigger transform conversion
    #
    self.activeCheckBox = qt.QCheckBox()
    self.activeCheckBox.checked = 0
    self.activeCheckBox.enabled = 0
    self.activeCheckBox.setToolTip("Activate OpenIGTLink connection")
    connectionFormLayout.addRow("Active: ", self.activeCheckBox)

    #
    # Configuration Selection Area
    #
    selectionCollapsibleButton = ctk.ctkCollapsibleButton()
    selectionCollapsibleButton.text = "Catheter Configuration"
    self.layout.addWidget(selectionCollapsibleButton)

    selectionFormLayout = qt.QFormLayout(selectionCollapsibleButton)

    #
    # Catheter #1 Tip Length (legnth between the catheter tip and the first coil)
    #
    self.tipLength1SliderWidget = ctk.ctkSliderWidget()
    self.tipLength1SliderWidget.singleStep = 0.5
    self.tipLength1SliderWidget.minimum = 0.0
    self.tipLength1SliderWidget.maximum = 100.0
    self.tipLength1SliderWidget.value = 10.0
    self.tipLength1SliderWidget.setToolTip("Set the length of the catheter tip.")
    selectionFormLayout.addRow("Cath 1 Tip Length (mm): ", self.tipLength1SliderWidget)
    
    #
    # Catheter #1 Catheter diameter
    #
    self.catheter1DiameterSliderWidget = ctk.ctkSliderWidget()
    self.catheter1DiameterSliderWidget.singleStep = 0.1
    self.catheter1DiameterSliderWidget.minimum = 0.1
    self.catheter1DiameterSliderWidget.maximum = 10.0
    self.catheter1DiameterSliderWidget.value = 1.0
    self.catheter1DiameterSliderWidget.setToolTip("Set the diameter of the catheter")
    selectionFormLayout.addRow("Cath 1 Diameter (mm): ", self.catheter1DiameterSliderWidget)

    #
    # Catheter #1 Catheter opacity
    #
    self.catheter1OpacitySliderWidget = ctk.ctkSliderWidget()
    self.catheter1OpacitySliderWidget.singleStep = 0.1
    self.catheter1OpacitySliderWidget.minimum = 0.0
    self.catheter1OpacitySliderWidget.maximum = 1.0
    self.catheter1OpacitySliderWidget.value = 1.0
    self.catheter1OpacitySliderWidget.setToolTip("Set the opacity of the catheter")
    selectionFormLayout.addRow("Cath 1 Opacity: ", self.catheter1OpacitySliderWidget)


    #
    # Catheter #2 Tip Length (legnth between the catheter tip and the first coil)
    #
    self.tipLength2SliderWidget = ctk.ctkSliderWidget()
    self.tipLength2SliderWidget.singleStep = 0.5
    self.tipLength2SliderWidget.minimum = 0.0
    self.tipLength2SliderWidget.maximum = 100.0
    self.tipLength2SliderWidget.value = 10.0
    self.tipLength2SliderWidget.setToolTip("Set the length of the catheter tip.")
    selectionFormLayout.addRow("Cath 2 Tip Length (mm): ", self.tipLength2SliderWidget)
    
    #
    # Catheter #2 diameter
    #
    self.catheter2DiameterSliderWidget = ctk.ctkSliderWidget()
    self.catheter2DiameterSliderWidget.singleStep = 0.1
    self.catheter2DiameterSliderWidget.minimum = 0.1
    self.catheter2DiameterSliderWidget.maximum = 10.0
    self.catheter2DiameterSliderWidget.value = 1.0
    self.catheter2DiameterSliderWidget.setToolTip("Set the diameter of the catheter")
    selectionFormLayout.addRow("Cath 2 Diameter (mm): ", self.catheter2DiameterSliderWidget)

    #
    # Catheter #2 opacity
    #
    self.catheter2OpacitySliderWidget = ctk.ctkSliderWidget()
    self.catheter2OpacitySliderWidget.singleStep = 0.1
    self.catheter2OpacitySliderWidget.minimum = 0.0
    self.catheter2OpacitySliderWidget.maximum = 1.0
    self.catheter2OpacitySliderWidget.value = 1.0
    self.catheter2OpacitySliderWidget.setToolTip("Set the opacity of the catheter")
    selectionFormLayout.addRow("Cath 2 Opacity: ", self.catheter2OpacitySliderWidget)

    #
    # Coil Selection Aare
    #
    coilCollapsibleButton = ctk.ctkCollapsibleButton()
    coilCollapsibleButton.text = "Coil Selection"
    self.layout.addWidget(coilCollapsibleButton)
    
    coilSelectionLayout = qt.QFormLayout(coilCollapsibleButton)
    
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
    self.coil_1_1_CheckBox = qt.QCheckBox()
    self.coil_1_1_CheckBox.checked = 1
    self.coil_1_1_CheckBox.text = "CH 1"
    self.coil_1_2_CheckBox = qt.QCheckBox()
    self.coil_1_2_CheckBox.checked = 1
    self.coil_1_2_CheckBox.text = "CH 2"
    self.coil_1_3_CheckBox = qt.QCheckBox()
    self.coil_1_3_CheckBox.checked = 1
    self.coil_1_3_CheckBox.text = "CH 3"
    self.coil_1_4_CheckBox = qt.QCheckBox()
    self.coil_1_4_CheckBox.checked = 1
    self.coil_1_4_CheckBox.text = "CH 4"
    self.coil_1_5_CheckBox = qt.QCheckBox()
    self.coil_1_5_CheckBox.checked = 0
    self.coil_1_5_CheckBox.text = "CH 5"
    self.coil_1_6_CheckBox = qt.QCheckBox()
    self.coil_1_6_CheckBox.checked = 0
    self.coil_1_6_CheckBox.text = "CH 6"
    self.coil_1_7_CheckBox = qt.QCheckBox()
    self.coil_1_7_CheckBox.checked = 0
    self.coil_1_7_CheckBox.text = "CH 7"
    self.coil_1_8_CheckBox = qt.QCheckBox()
    self.coil_1_8_CheckBox.checked = 0
    self.coil_1_8_CheckBox.text = "CH 8"

    self.coilGroup11Layout = qt.QHBoxLayout()
    self.coilGroup11Layout.addWidget(self.coil_1_1_CheckBox)
    self.coilGroup11Layout.addWidget(self.coil_1_2_CheckBox)
    self.coilGroup11Layout.addWidget(self.coil_1_3_CheckBox)
    self.coilGroup11Layout.addWidget(self.coil_1_4_CheckBox)
    coilSelectionLayout.addRow("Cath 1 Active Coils:", self.coilGroup11Layout)

    self.coilGroup12Layout = qt.QHBoxLayout()
    self.coilGroup12Layout.addWidget(self.coil_1_5_CheckBox)
    self.coilGroup12Layout.addWidget(self.coil_1_6_CheckBox)
    self.coilGroup12Layout.addWidget(self.coil_1_7_CheckBox)
    self.coilGroup12Layout.addWidget(self.coil_1_8_CheckBox)
    coilSelectionLayout.addRow("", self.coilGroup12Layout)

    self.coil_2_1_CheckBox = qt.QCheckBox()
    self.coil_2_1_CheckBox.checked = 0
    self.coil_2_1_CheckBox.text = "CH 1"
    self.coil_2_2_CheckBox = qt.QCheckBox()
    self.coil_2_2_CheckBox.checked = 0
    self.coil_2_2_CheckBox.text = "CH 2"
    self.coil_2_3_CheckBox = qt.QCheckBox()
    self.coil_2_3_CheckBox.checked = 0
    self.coil_2_3_CheckBox.text = "CH 3"
    self.coil_2_4_CheckBox = qt.QCheckBox()
    self.coil_2_4_CheckBox.checked = 0
    self.coil_2_4_CheckBox.text = "CH 4"
    self.coil_2_5_CheckBox = qt.QCheckBox()
    self.coil_2_5_CheckBox.checked = 1
    self.coil_2_5_CheckBox.text = "CH 5"
    self.coil_2_6_CheckBox = qt.QCheckBox()
    self.coil_2_6_CheckBox.checked = 1
    self.coil_2_6_CheckBox.text = "CH 6"
    self.coil_2_7_CheckBox = qt.QCheckBox()
    self.coil_2_7_CheckBox.checked = 1
    self.coil_2_7_CheckBox.text = "CH 7"
    self.coil_2_8_CheckBox = qt.QCheckBox()
    self.coil_2_8_CheckBox.checked = 1
    self.coil_2_8_CheckBox.text = "CH 8"
    
    self.coilGroup21Layout = qt.QHBoxLayout()
    self.coilGroup21Layout.addWidget(self.coil_2_1_CheckBox)
    self.coilGroup21Layout.addWidget(self.coil_2_2_CheckBox)
    self.coilGroup21Layout.addWidget(self.coil_2_3_CheckBox)
    self.coilGroup21Layout.addWidget(self.coil_2_4_CheckBox)
    coilSelectionLayout.addRow("Cath 2 Active Coils:", self.coilGroup21Layout)

    self.coilGroup22Layout = qt.QHBoxLayout()
    self.coilGroup22Layout.addWidget(self.coil_2_5_CheckBox)
    self.coilGroup22Layout.addWidget(self.coil_2_6_CheckBox)
    self.coilGroup22Layout.addWidget(self.coil_2_7_CheckBox)
    self.coilGroup22Layout.addWidget(self.coil_2_8_CheckBox)
    coilSelectionLayout.addRow("", self.coilGroup22Layout)
    
    #
    # Reslice
    #
    resliceCollapsibleButton = ctk.ctkCollapsibleButton()
    resliceCollapsibleButton.text = "Image Reslice"
    self.layout.addWidget(resliceCollapsibleButton)

    resliceLayout = qt.QFormLayout(resliceCollapsibleButton)
    
    self.resliceCath1RadioButton = qt.QRadioButton("Cath 1")
    self.resliceCath2RadioButton = qt.QRadioButton("Cath 2")
    self.resliceCath1RadioButton.checked = 0
    self.resliceCathBoxLayout = qt.QHBoxLayout()
    self.resliceCathBoxLayout.addWidget(self.resliceCath1RadioButton)
    self.resliceCathBoxLayout.addWidget(self.resliceCath2RadioButton)

    self.resliceCathGroup = qt.QButtonGroup()
    self.resliceCathGroup.addButton(self.resliceCath1RadioButton)
    self.resliceCathGroup.addButton(self.resliceCath2RadioButton)
    resliceLayout.addRow("Reslice Catheter:", self.resliceCathBoxLayout)
    
    self.resliceAxCheckBox = qt.QCheckBox()
    self.resliceAxCheckBox.checked = 0
    self.resliceAxCheckBox.text = "AX"
    self.resliceSagCheckBox = qt.QCheckBox()
    self.resliceSagCheckBox.checked = 0
    self.resliceSagCheckBox.text = "SAG"
    self.resliceCorCheckBox = qt.QCheckBox()
    self.resliceCorCheckBox.checked = 0
    self.resliceCorCheckBox.text = "COR"

    self.resliceBoxLayout = qt.QHBoxLayout()
    self.resliceBoxLayout.addWidget(self.resliceAxCheckBox)
    self.resliceBoxLayout.addWidget(self.resliceSagCheckBox)
    self.resliceBoxLayout.addWidget(self.resliceCorCheckBox)
    resliceLayout.addRow("Reslice Plane:", self.resliceBoxLayout)

    #
    # Connections
    #
    self.connectorSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onConnectorSelected)
    self.activeCheckBox.connect('toggled(bool)', self.onActive)
    self.tipLength1SliderWidget.connect("valueChanged(double)", self.onTipLength1Changed)
    self.catheter1DiameterSliderWidget.connect("valueChanged(double)", self.onCatheter1DiameterChanged)
    self.catheter1OpacitySliderWidget.connect("valueChanged(double)", self.onCatheter1OpacityChanged)
    self.tipLength2SliderWidget.connect("valueChanged(double)", self.onTipLength2Changed)
    self.catheter2DiameterSliderWidget.connect("valueChanged(double)", self.onCatheter2DiameterChanged)
    self.catheter2OpacitySliderWidget.connect("valueChanged(double)", self.onCatheter2OpacityChanged)
    self.showCoilLabelCheckBox.connect('toggled(bool)', self.onCoilLabelChecked)
    
    self.coil_1_1_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_2_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_3_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_4_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_5_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_6_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_7_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_8_CheckBox.connect('toggled(bool)', self.onCoilChecked)

    self.coil_2_1_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_2_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_3_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_4_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_5_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_6_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_7_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_8_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    
    self.resliceAxCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceSagCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceCorCheckBox.connect('toggled(bool)', self.onResliceChecked)

    self.resliceCath1RadioButton.connect('clicked(bool)', self.onSelectResliceCath)
    self.resliceCath2RadioButton.connect('clicked(bool)', self.onSelectResliceCath)
    
    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass


  #--------------------------------------------------
  # GUI Call Back functions
  #

  def onActive(self):
    
    if self.connectorSelector.currentNode() == None:
      return

    if self.activeCheckBox.checked == True:
      if self.logic.connected() != True:
        port  = self.connectorPort.value
        self.logic.waitForClient(port)
    else:
      self.logic.disconnect()

    #time.sleep(1)
    #self.updateGUI()


  def onConnectorSelected(self):
    cnode = self.connectorSelector.currentNode()    
    self.logic.setConnector(cnode)
    self.updateGUI()


  def onRejectRegistration(self):
    self.logic.acceptNewMatrix(self, False)

    
  def onTipLength1Changed(self):
    self.logic.setTipLength(self.tipLength1SliderWidget.value, 1)

    
  def onCatheter1DiameterChanged(self):
    self.logic.setCatheterDiameter(self.catheter1DiameterSliderWidget.value, 1)
    

  def onCatheter1OpacityChanged(self):
    self.logic.setCatheterOpacity(self.catheter1OpacitySliderWidget.value, 1)
    
  def onTipLength2Changed(self):
    self.logic.setTipLength(self.tipLength2SliderWidget.value, 2)

  def onCatheter2DiameterChanged(self):
    self.logic.setCatheterDiameter(self.catheter2DiameterSliderWidget.value, 2)
    

  def onCatheter2OpacityChanged(self):
    self.logic.setCatheterOpacity(self.catheter2OpacitySliderWidget.value, 2)
    
    
  def onCoilLabelChecked(self):
    self.logic.setShowCoilLabel(self.showCoilLabelCheckBox.checked)


  def onCoilChecked(self):
    activeCoils1 = [
      self.coil_1_1_CheckBox.checked,
      self.coil_1_2_CheckBox.checked,
      self.coil_1_3_CheckBox.checked,
      self.coil_1_4_CheckBox.checked,
      self.coil_1_5_CheckBox.checked,
      self.coil_1_6_CheckBox.checked,
      self.coil_1_7_CheckBox.checked,
      self.coil_1_8_CheckBox.checked
    ]
    activeCoils2 = [
      self.coil_2_1_CheckBox.checked,
      self.coil_2_2_CheckBox.checked,
      self.coil_2_3_CheckBox.checked,
      self.coil_2_4_CheckBox.checked,
      self.coil_2_5_CheckBox.checked,
      self.coil_2_6_CheckBox.checked,
      self.coil_2_7_CheckBox.checked,
      self.coil_2_8_CheckBox.checked
    ]
    self.logic.setActiveCoils(activeCoils1, activeCoils2)

    
  def onResliceChecked(self):
    ax  = self.resliceAxCheckBox.checked
    sag = self.resliceSagCheckBox.checked
    cor = self.resliceCorCheckBox.checked

    self.logic.setReslice(ax, sag, cor)

  def onSelectResliceCath(self):

    if self.resliceCath1RadioButton.checked:
      self.logic.setResliceCath(1)
    else:
      self.logic.setResliceCath(2)
      
    
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

    # CurveMaker
    self.cmLogic = CurveMaker.CurveMakerLogic()
    self.cmOpacity = [1.0, 1.0]
    self.cmRadius = [0.5, 0.5]
    self.cmModelColor = [[0.0, 0.0, 1.0], [1.0, 0.359375, 0.0]]

    # Tip model
    self.tipLength = [10.0, 10.0]
    self.tipModelNode = [None, None]
    self.tipTransformNode = [None, None]
    self.tipPoly = [None, None]
    self.showCoilLabel = False
    self.activeCoils1 = [False, False, False, False, True, True, True, True]
    self.activeCoils2 = [True, True, True, True, False, False, False, False]
    self.reslice = [False, False, False]
    self.resliceDriverLogic= slicer.modules.volumereslicedriver.logic()

    self.sliceNodeRed = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
    self.sliceNodeYellow = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()
    self.sliceNodeGreen = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()

    self.incomingNode = None
    self.resliceCath = 1

    
  def setWidget(self, widget):
    self.widget = widget


  def setTipLength(self, length, index):
    self.tipLength[index-1] = length
    self.updateCatheter(index)


  def setCatheterDiameter(self, diameter, index):
    self.cmRadius[index-1] = diameter / 2.0
    self.updateCatheter(index)
    

  def setCatheterOpacity(self, opacity, index):
    self.cmOpacity[index-1] = opacity
    self.updateCatheter(index)
    
    
  def setShowCoilLabel(self, show):
    self.showCoilLabel = show
    self.updateCatheter(1)
    self.updateCatheter(2)
    

  def setActiveCoils(self, coils1, coils2):
    self.activeCoils1 = coils1
    self.activeCoils2 = coils2
    self.updateCatheter(1)
    self.updateCatheter(2)


  def setReslice(self, ax, sag, cor):
    self.reslice = [ax, sag, cor]
    self.updateCatheter(1)
    self.updateCatheter(2)

  def setResliceCath(self, index):
    self.resliceCath = index
  

  def setConnector(self, cnode):

    if cnode == None:
      self.connectorNodeID = ''
      return

    if self.connectorNodeID != cnode.GetID():
      if self.connectorNodeID != '':
        self.deactivateEvent()
      self.connectorNodeID = cnode.GetID()
      self.activateEvent()
      
    self.setupFiducials(cnode, 1)
    self.setupFiducials(cnode, 2)

  def setupFiducials(self, cnode, index):
    
    # Set up markups fiducial node, if specified in the connector node
    cmFiducialsID = cnode.GetAttribute('MRTracking.cmFiducials%d' % index)
    if cmFiducialsID != None:
      self.cmLogic.CurrentSourceNode = self.scene.GetNodeByID(cmFiducialsID)
    else:
      self.cmLogic.CurrentSourceNode = None
      
    # Set up model node, if specified in the connector node
    cmModelID = cnode.GetAttribute('MRTracking.cmModel%d' % index)
    if cmModelID != None:
      self.cmLogic.CurrentDestinationNode = self.scene.GetNodeByID(cmModelID)
      if self.cmLogic.CurrentSourceNode:
        self.cmLogic.CurrentSourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.CurrentDestinationNode.GetID())
    else:
      self.cmLogic.CurrentDestinationNode = None
      
    #if self.cmLogic.CurrentSourceNode:
    #  cnode.SetAttribute('CoilPositions', cmFiducialsID)

    # Set up tip model node, if specified in the connector node
    tipModelID = cnode.GetAttribute('MRTracking.tipModel%d' % index)
    if tipModelID != None:
      self.tipModelNode[index-1] = self.scene.GetNodeByID(tipModelID)
    else:
      self.tipModelNode[index-1] = None

    tipTransformNodeID = cnode.GetAttribute('MRTracking.tipTransform%d' % index)
    if tipTransformNodeID != None:
      self.tipTransformNode[index-1] = self.scene.GetNodeByID(tipTransformNodeID)
    else:
      self.tipTransformNode[index-1] = None

    # Set up incoming node, if specified in the connector node
    incomingNodeID = cnode.GetAttribute('MRTracking.incomingNode%d' % index)
    if incomingNodeID != None:
      incomingNode = self.scene.GetNodeByID(incomingNodeID)
      if incomingNode:
          self.eventTag[incomingNodeID] = incomingNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        
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

    if node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':

      self.updateCatheterNode(1, node)
      self.updateCatheterNode(2, node)

      
  def updateCatheterNode(self, index, node):
    # node shoud be vtkMRMLIGTLTrackingDataBundleNode

    fiducialNode = None

    cathName = 'Catheter_%d' % index

    ## Catheter 1
    fiducialNodeID = node.GetAttribute(cathName)
    if fiducialNodeID != None:
      fiducialNode = self.scene.GetNodeByID(fiducialNodeID)
    
    if fiducialNode == None:
      fiducialNode = self.scene.CreateNodeByClass("vtkMRMLMarkupsFiducialNode")
      fiducialNode.SetLocked(True)
      fiducialNode.SetName('Coil_%d' % index)
      self.scene.AddNode(fiducialNode)
      fiducialNodeID = fiducialNode.GetID()
      node.SetAttribute(cathName, fiducialNodeID)
      
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

    cnode = self.scene.GetNodeByID(self.connectorNodeID)

    if cnode:
      if self.cmLogic.CurrentDestinationNode:
        cnode.SetAttribute('MRTracking.cmModel%d' % index, self.cmLogic.CurrentDestinationNode.GetID())
      if self.cmLogic.CurrentSourceNode:
        cnode.SetAttribute('MRTracking.cmFiducials%d' % index, self.cmLogic.CurrentSourceNode.GetID())
        
    if self.cmLogic.CurrentDestinationNode and self.cmLogic.CurrentSourceNode:
      self.cmLogic.CurrentSourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.CurrentDestinationNode.GetID())
              
    # Update coordinates in the fiducial node.
    nCoils = node.GetNumberOfTransformNodes()
    mask = self.activeCoils1[0:nCoils]
    if index == 2:
      mask = self.activeCoils2[0:nCoils]
    nActiveCoils = sum(mask)
    if fiducialNode.GetNumberOfFiducials() != nActiveCoils:
      fiducialNode.RemoveAllMarkups()
      for i in range(nActiveCoils):
        fiducialNode.AddFiducial(0.0, 0.0, 0.0)
    j = 0
    for i in range(nCoils):
      if mask[i]:
        tnode = node.GetTransformNode(i)
        trans = tnode.GetTransformToParent()
        #fiducialNode.SetNthFiducialPositionFromArray(j, trans.GetPosition())
        v = trans.GetPosition()
        fiducialNode.SetNthFiducialPosition(j, -v[0], v[1], v[2])
        j += 1
      
    self.updateCatheter(index)


  def updateCatheter(self, index):

    cnode = self.scene.GetNodeByID(self.connectorNodeID)
    if cnode == None:
      return
    cmFiducialsID = cnode.GetAttribute('MRTracking.cmFiducials%d' % index)
    if cmFiducialsID == None:
      return

    sourceNode = self.scene.GetNodeByID(cmFiducialsID)

    if sourceNode == None:
      return

    cmModelID = sourceNode.GetAttribute('CurveMaker.CurveModel')
    if cmModelID == None:
      return
    
    destinationNode = self.scene.GetNodeByID(cmModelID)
    
    modelDisplayNode = destinationNode.GetDisplayNode()
    if modelDisplayNode:
      modelDisplayNode.SetColor(self.cmModelColor[index-1])
      modelDisplayNode.SetOpacity(self.cmOpacity[index-1])
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetSliceDisplayModeToIntersection()

    # Update catheter using the CurveMaker module
    self.cmLogic.setTubeRadius(self.cmRadius[index-1], sourceNode)
    self.cmLogic.enableAutomaticUpdate(1, sourceNode)
    self.cmLogic.setInterpolationMethod('cardinal', sourceNode)
    self.cmLogic.updateCurve()

    # Skip if the model has not been created. (Don't call this section before self.cmLogic.updateCurve()
    if not (sourceNode.GetID() in self.cmLogic.CurvePoly) or (self.cmLogic.CurvePoly[sourceNode.GetID()] == None):
      return
    
    # Show/hide fiducials for coils
    fiducialDisplayNode = sourceNode.GetDisplayNode()
    if fiducialDisplayNode:
      fiducialDisplayNode.SetVisibility(self.showCoilLabel)

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
      pe = p0 + n10 * self.tipLength[index-1]

    if self.tipPoly[index-1]==None:
      self.tipPoly[index-1] = vtk.vtkPolyData()

    if self.tipModelNode[index-1] == None:
      self.tipModelNode[index-1] = self.scene.CreateNodeByClass('vtkMRMLModelNode')
      self.tipModelNode[index-1].SetName('Tip')
      self.scene.AddNode(self.tipModelNode[index-1])
      cnode = self.scene.GetNodeByID(self.connectorNodeID)
      if cnode:
        cnode.SetAttribute('MRTracking.tipModel%d' % index, self.tipModelNode[index-1].GetID())
        
    if self.tipTransformNode[index-1] == None:
      self.tipTransformNode[index-1] = self.scene.CreateNodeByClass('vtkMRMLLinearTransformNode')
      self.tipTransformNode[index-1].SetName('TipTransform')
      self.scene.AddNode(self.tipTransformNode[index-1])
      cnode = self.scene.GetNodeByID(self.connectorNodeID)
      if cnode:
        cnode.SetAttribute('MRTracking.tipTransform%d' % index, self.tipTransformNode[index-1].GetID())

    matrix = vtk.vtkMatrix4x4()
    matrix.Identity()
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    self.tipTransformNode[index-1].SetMatrixTransformToParent(matrix)


    if self.resliceCath == index:
      if self.reslice[0]:
        self.resliceDriverLogic.SetDriverForSlice(self.tipTransformNode[index-1].GetID(), self.sliceNodeRed)
        self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_AXIAL, self.sliceNodeRed)
      else:
        self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeRed)
        self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeRed)
        
      if self.reslice[1]:
        self.resliceDriverLogic.SetDriverForSlice(self.tipTransformNode[index-1].GetID(), self.sliceNodeYellow)
        self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_SAGITTAL, self.sliceNodeYellow)
      else:
        self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeYellow)
        self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeYellow)
      
      if self.reslice[2]:
        self.resliceDriverLogic.SetDriverForSlice(self.tipTransformNode[index-1].GetID(), self.sliceNodeGreen)
        self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_CORONAL, self.sliceNodeGreen)
      else:
        self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeGreen)
        self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeGreen)

    self.updateTipModelNode(self.tipModelNode[index-1], self.tipPoly[index-1], p0, pe, self.cmRadius[index-1], self.cmModelColor[index-1], self.cmOpacity[index-1])


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
    for i in range (nInNode):
      node = cnode.GetIncomingMRMLNode(i)
      if not node.GetID() in self.eventTag:
        self.eventTag[node.GetID()] = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
      if cnode.GetAttribute('MRTracking.incomingNode') != node.GetID():
        cnode.SetAttribute('MRTracking.incomingNode', node.GetID())
        

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

      
