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
    # Tip Length (legnth between the catheter tip and the first coil)
    #
    self.tipLengthSliderWidget = ctk.ctkSliderWidget()
    self.tipLengthSliderWidget.singleStep = 0.5
    self.tipLengthSliderWidget.minimum = 0.0
    self.tipLengthSliderWidget.maximum = 100.0
    self.tipLengthSliderWidget.value = 10.0
    self.tipLengthSliderWidget.setToolTip("Set the length of the catheter tip.")
    selectionFormLayout.addRow("Tip Length (mm): ", self.tipLengthSliderWidget)
    
    #
    # Catheter diameter
    #
    self.catheterDiameterSliderWidget = ctk.ctkSliderWidget()
    self.catheterDiameterSliderWidget.singleStep = 0.1
    self.catheterDiameterSliderWidget.minimum = 0.1
    self.catheterDiameterSliderWidget.maximum = 10.0
    self.catheterDiameterSliderWidget.value = 1.0
    self.catheterDiameterSliderWidget.setToolTip("Set the diameter of the catheter")
    selectionFormLayout.addRow("Diameter (mm): ", self.catheterDiameterSliderWidget)

    #
    # Catheter opacity
    #
    self.catheterOpacitySliderWidget = ctk.ctkSliderWidget()
    self.catheterOpacitySliderWidget.singleStep = 0.1
    self.catheterOpacitySliderWidget.minimum = 0.0
    self.catheterOpacitySliderWidget.maximum = 1.0
    self.catheterOpacitySliderWidget.value = 1.0
    self.catheterOpacitySliderWidget.setToolTip("Set the opacity of the catheter")
    selectionFormLayout.addRow("Opacity: ", self.catheterOpacitySliderWidget)
    
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
    self.coil1CheckBox = qt.QCheckBox()
    self.coil1CheckBox.checked = 1
    self.coil1CheckBox.text = "CH 1"
    self.coil2CheckBox = qt.QCheckBox()
    self.coil2CheckBox.checked = 1
    self.coil2CheckBox.text = "CH 2"
    self.coil3CheckBox = qt.QCheckBox()
    self.coil3CheckBox.checked = 1
    self.coil3CheckBox.text = "CH 3"
    self.coil4CheckBox = qt.QCheckBox()
    self.coil4CheckBox.checked = 1
    self.coil4CheckBox.text = "CH 4"
    self.coil5CheckBox = qt.QCheckBox()
    self.coil5CheckBox.checked = 1
    self.coil5CheckBox.text = "CH 5"
    self.coil6CheckBox = qt.QCheckBox()
    self.coil6CheckBox.checked = 1
    self.coil6CheckBox.text = "CH 6"
    self.coil7CheckBox = qt.QCheckBox()
    self.coil7CheckBox.checked = 1
    self.coil7CheckBox.text = "CH 7"
    self.coil8CheckBox = qt.QCheckBox()
    self.coil8CheckBox.checked = 1
    self.coil8CheckBox.text = "CH 8"

    self.coilGroup1Layout = qt.QHBoxLayout()
    self.coilGroup1Layout.addWidget(self.coil1CheckBox)
    self.coilGroup1Layout.addWidget(self.coil2CheckBox)
    self.coilGroup1Layout.addWidget(self.coil3CheckBox)
    self.coilGroup1Layout.addWidget(self.coil4CheckBox)
    coilSelectionLayout.addRow("Active Coils:", self.coilGroup1Layout)

    self.coilGroup2Layout = qt.QHBoxLayout()
    self.coilGroup2Layout.addWidget(self.coil5CheckBox)
    self.coilGroup2Layout.addWidget(self.coil6CheckBox)
    self.coilGroup2Layout.addWidget(self.coil7CheckBox)
    self.coilGroup2Layout.addWidget(self.coil8CheckBox)
    coilSelectionLayout.addRow("", self.coilGroup2Layout)

    #
    # Reslice
    #
    resliceCollapsibleButton = ctk.ctkCollapsibleButton()
    resliceCollapsibleButton.text = "Image Reslice"
    self.layout.addWidget(resliceCollapsibleButton)
    
    resliceLayout = qt.QFormLayout(resliceCollapsibleButton)
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
    self.tipLengthSliderWidget.connect("valueChanged(double)", self.onTipLengthChanged)
    self.catheterDiameterSliderWidget.connect("valueChanged(double)", self.onCatheterDiameterChanged)
    self.catheterOpacitySliderWidget.connect("valueChanged(double)", self.onCatheterOpacityChanged)
    self.showCoilLabelCheckBox.connect('toggled(bool)', self.onCoilLabelChecked)
    
    self.coil1CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil2CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil3CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil4CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil5CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil6CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil7CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil8CheckBox.connect('toggled(bool)', self.onCoilChecked)

    self.resliceAxCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceSagCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceCorCheckBox.connect('toggled(bool)', self.onResliceChecked)
    
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

    
  def onTipLengthChanged(self):
    self.logic.setTipLength(self.tipLengthSliderWidget.value)

    
  def onCatheterDiameterChanged(self):
    self.logic.setCatheterDiameter(self.catheterDiameterSliderWidget.value)
    

  def onCatheterOpacityChanged(self):
    self.logic.setCatheterOpacity(self.catheterOpacitySliderWidget.value)
    
    
  def onCoilLabelChecked(self):
    self.logic.setShowCoilLabel(self.showCoilLabelCheckBox.checked)


  def onCoilChecked(self):
    activeCoils = [
      self.coil1CheckBox.checked,
      self.coil2CheckBox.checked,
      self.coil3CheckBox.checked,
      self.coil4CheckBox.checked,
      self.coil5CheckBox.checked,
      self.coil6CheckBox.checked,
      self.coil7CheckBox.checked,
      self.coil8CheckBox.checked
    ]
    self.logic.setActiveCoils(activeCoils)

    
  def onResliceChecked(self):
    ax  = self.resliceAxCheckBox.checked
    sag = self.resliceSagCheckBox.checked
    cor = self.resliceCorCheckBox.checked

    self.logic.setReslice(ax, sag, cor)

    
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
    self.cmOpacity = 1.0
    self.cmRadius = 0.5

    # Tip model
    self.tipLength = 10.0
    self.tipModelNode = None
    self.tipTransformNode = None
    self.tipPoly = None
    self.showCoilLabel = False
    self.activeCoils = [True, True, True, True, True, True, True, True]
    self.reslice = [False, False, False]
    self.resliceDriverLogic= slicer.modules.volumereslicedriver.logic()

    self.sliceNodeRed = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
    self.sliceNodeYellow = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()
    self.sliceNodeGreen = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()

    self.incomingNode = None

    
  def setWidget(self, widget):
    self.widget = widget


  def setTipLength(self, length):
    self.tipLength = length
    self.updateCatheter()


  def setCatheterDiameter(self, diameter):
    self.cmRadius = diameter / 2.0
    self.updateCatheter()


  def setCatheterOpacity(self, opacity):
    self.cmOpacity = opacity
    self.updateCatheter()
    
    
  def setShowCoilLabel(self, show):
    self.showCoilLabel = show
    self.updateCatheter()
    

  def setActiveCoils(self, coils):
    self.activeCoils = coils
    self.updateCatheter()


  def setReslice(self, ax, sag, cor):
    self.reslice = [ax, sag, cor]
    self.updateCatheter()

  def setConnector(self, cnode):

    if cnode == None:
      self.connectorNodeID = ''
      return

    if self.connectorNodeID != cnode.GetID():
      if self.connectorNodeID != '':
        self.deactivateEvent()
      self.connectorNodeID = cnode.GetID()
      self.activateEvent()

    # Set up markups fiducial node, if specified in the connector node
    cmFiducialsID = cnode.GetAttribute('MRTracking.cmFiducials')
    if cmFiducialsID != None:
      self.cmLogic.SourceNode = self.scene.GetNodeByID(cmFiducialsID)
    else:
      self.cmLogic.SourceNode = None
      
    # Set up model node, if specified in the connector node
    cmModelID = cnode.GetAttribute('MRTracking.cmModel')
    if cmModelID != None:
      self.cmLogic.DestinationNode = self.scene.GetNodeByID(cmModelID)
      if self.cmLogic.SourceNode:
        self.cmLogic.SourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.DestinationNode.GetID())
    else:
      self.cmLogic.DestinationNode = None
      
    #if self.cmLogic.SourceNode:
    #  cnode.SetAttribute('CoilPositions', cmFiducialsID)

    # Set up tip model node, if specified in the connector node
    tipModelID = cnode.GetAttribute('MRTracking.tipModel')
    if tipModelID != None:
      self.tipModelNode = self.scene.GetNodeByID(tipModelID)
    else:
      self.tipModelNode = None

    tipTransformNodeID = cnode.GetAttribute('MRTracking.tipTransform')
    if tipTransformNodeID != None:
      self.tipTransformNode = self.scene.GetNodeByID(tipTransformNodeID)
    else:
      self.tipTransformNode = None

    # Set up incoming node, if specified in the connector node
    incomingNodeID = cnode.GetAttribute('MRTracking.incomingNode')
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

    #if node.GetName() == 'WWTracker':
    if node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':

      # Check if the fiducial node exists; if not, create one.
      cnode = self.scene.GetNodeByID(self.connectorNodeID)
        
      fiducialNode = None

      fiducialNodeID = node.GetAttribute('CoilPositions')
      if fiducialNodeID != None:
        fiducialNode = self.scene.GetNodeByID(fiducialNodeID)
      
      if fiducialNode == None:
        fiducialNode = self.scene.CreateNodeByClass("vtkMRMLMarkupsFiducialNode")
        fiducialNode.SetLocked(True)
        fiducialNode.SetName('Coil')
        self.scene.AddNode(fiducialNode)
        fiducialNodeID = fiducialNode.GetID()
        node.SetAttribute('CoilPositions', fiducialNodeID)
        self.cmLogic.SourceNode = fiducialNode

      # Check if the curve model exists; if not, create one.
      if self.cmLogic.DestinationNode == None:
        cmModel = self.scene.CreateNodeByClass("vtkMRMLModelNode")
        cmModel.SetName('Catheter')
        self.scene.AddNode(cmModel)
        #self.scene.AddNode(modelDisplayNode)
        self.cmLogic.DestinationNode = cmModel

      if cnode:
        if self.cmLogic.DestinationNode:
          cnode.SetAttribute('MRTracking.cmModel', self.cmLogic.DestinationNode.GetID())
        if self.cmLogic.SourceNode:
          cnode.SetAttribute('MRTracking.cmFiducials', self.cmLogic.SourceNode.GetID())
          
      if self.cmLogic.DestinationNode and self.cmLogic.SourceNode:
        self.cmLogic.SourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.DestinationNode.GetID())
                
        
      # Update coordinates in the fiducial node.
      nCoils = node.GetNumberOfTransformNodes()
      mask = self.activeCoils[0:nCoils]
      nActiveCoils = sum(mask)
      if fiducialNode.GetNumberOfFiducials() != nActiveCoils:
        fiducialNode.RemoveAllMarkups()
        for i in range(nActiveCoils):
          fiducialNode.AddFiducial(0.0, 0.0, 0.0)
      j = 0
      for i in range(nCoils):
        if self.activeCoils[i]:
          tnode = node.GetTransformNode(i)
          trans = tnode.GetTransformToParent()
          fiducialNode.SetNthFiducialPositionFromArray(j, trans.GetPosition())
          j += 1
        
      self.updateCatheter()


  def updateCatheter(self):

    if self.cmLogic.DestinationNode == None:
      return
    
    modelDisplayNode = self.cmLogic.DestinationNode.GetDisplayNode()
    if modelDisplayNode:
      modelDisplayNode.SetColor(self.cmLogic.ModelColor)
      modelDisplayNode.SetOpacity(self.cmOpacity)
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetSliceDisplayModeToIntersection()

    # Update catheter using the CurveMaker module
    self.cmLogic.setTubeRadius(self.cmRadius)
    self.cmLogic.enableAutomaticUpdate(1)
    self.cmLogic.setInterpolationMethod(1)
    self.cmLogic.updateCurve()

    # Skip if the model has not been created. (Don't call this section before self.cmLogic.updateCurve()
    if self.cmLogic.CurvePoly == None or self.cmLogic.SourceNode == None:
      return

    # Show/hide fiducials for coils
    fiducialDisplayNode = self.cmLogic.SourceNode.GetDisplayNode()
    if fiducialDisplayNode:
      fiducialDisplayNode.SetVisibility(self.showCoilLabel)

    # Add a extended tip
    lines = self.cmLogic.CurvePoly.GetLines()
    points = self.cmLogic.CurvePoly.GetPoints()
    pts = vtk.vtkIdList()
    
    lines.GetCell(0, pts)
    n = pts.GetNumberOfIds()
    if n > 1:
      p0 = numpy.array(points.GetPoint(pts.GetId(0)))
      p1 = numpy.array(points.GetPoint(pts.GetId(1)))
      v10 = p0 - p1
      n10 = v10 / numpy.linalg.norm(v10) # Normal vector at the tip
      pe = p0 + n10 * self.tipLength

    if self.tipPoly==None:
      self.tipPoly = vtk.vtkPolyData()

    if self.tipModelNode == None:
      self.tipModelNode = self.scene.CreateNodeByClass('vtkMRMLModelNode')
      self.tipModelNode.SetName('Tip')
      self.scene.AddNode(self.tipModelNode)
      cnode = self.scene.GetNodeByID(self.connectorNodeID)
      if cnode:
        cnode.SetAttribute('MRTracking.tipModel', self.tipModelNode.GetID())
        
    if self.tipTransformNode == None:
      self.tipTransformNode = self.scene.CreateNodeByClass('vtkMRMLLinearTransformNode')
      self.tipTransformNode.SetName('TipTransform')
      self.scene.AddNode(self.tipTransformNode)
      cnode = self.scene.GetNodeByID(self.connectorNodeID)
      if cnode:
        cnode.SetAttribute('MRTracking.tipTransform', self.tipTransformNode.GetID())

    matrix = vtk.vtkMatrix4x4()
    matrix.Identity()
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    self.tipTransformNode.SetMatrixTransformToParent(matrix)

    
    if self.reslice[0]:
      self.resliceDriverLogic.SetDriverForSlice(self.tipTransformNode.GetID(), self.sliceNodeRed)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_AXIAL, self.sliceNodeRed)
    else:
      self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeRed)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeRed)
      
      
    if self.reslice[1]:
      self.resliceDriverLogic.SetDriverForSlice(self.tipTransformNode.GetID(), self.sliceNodeYellow)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_SAGITTAL, self.sliceNodeYellow)
    else:
      self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeYellow)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeYellow)

    if self.reslice[2]:
      self.resliceDriverLogic.SetDriverForSlice(self.tipTransformNode.GetID(), self.sliceNodeGreen)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_CORONAL, self.sliceNodeGreen)
    else:
      self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeGreen)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeGreen)

    self.updateTipModelNode(self.tipModelNode, self.tipPoly, p0, pe, self.cmRadius, self.cmLogic.ModelColor, self.cmOpacity)


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
        
#        if node.GetNodeTagName() == 'IGTLTrackingDataSplitter':
#          n = node.GetNumberOfTransformNodes()
#          for id in range (n):
#            tnode = node.GetTransformNode(id)
#            if tnode and tnode.GetAttribute('MRTracking') == None:
#              needleModelID = self.createNeedleModelNode("Needle_%s" % tnode.GetName())
#              needleModel = self.scene.GetNodeByID(needleModelID)
#              needleModel.SetAndObserveTransformNodeID(tnode.GetID())
#              needleModel.InvokeEvent(slicer.vtkMRMLTransformableNode.TransformModifiedEvent)
#              tnode.SetAttribute('MRTracking', needleModelID)


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
    

  def createNeedleModel(self, node):
    if node and node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      n = node.GetNumberOfTransformNodes()
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

      
