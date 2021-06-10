import ctk
import qt
import slicer
from MRTrackingUtils.qcomboboxcatheter import *
from MRTrackingUtils.panelbase import *

#------------------------------------------------------------
#
# MRTrackingCatheterConfig
#

class MRTrackingCatheterConfig(MRTrackingPanelBase):

  def __init__(self, label="CatheterConfig"):
    super(MRTrackingCatheterConfig, self).__init__(label)
    
    self.label = label
    self.catheters = None     #CatheterCollection
    self.currentCatheter = None

  def buildMainPanel(self, frame):

    layout = qt.QVBoxLayout(frame)
    selectorLayout = qt.QFormLayout()
    layout.addLayout(selectorLayout)
    
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
    selectorLayout.addRow("Source: ", self.trackingDataSelector)
    
    self.activeTrackingCheckBox = qt.QCheckBox()
    self.activeTrackingCheckBox.checked = 0
    self.activeTrackingCheckBox.enabled = 1
    self.activeTrackingCheckBox.setToolTip("Activate Tracking")
    selectorLayout.addRow("Active: ", self.activeTrackingCheckBox)

    #--------------------------------------------------
    # Catheter Configuration

    configGroupBox = ctk.ctkCollapsibleGroupBox()
    configGroupBox.title = "Catheter Configuration"
    configGroupBox.collapsed = False

    layout.addWidget(configGroupBox)
    configFormLayout = qt.QFormLayout(configGroupBox)

    ##
    ## Tip Length (legnth between the catheter tip and the first coil)
    ##
    #self.tipLengthSliderWidget = ctk.ctkSliderWidget()
    #self.tipLengthSliderWidget.singleStep = 0.5
    #self.tipLengthSliderWidget.minimum = 0.0
    #self.tipLengthSliderWidget.maximum = 100.0
    #self.tipLengthSliderWidget.value = 10.0
    #self.tipLengthSliderWidget.setToolTip("Set the length of the catheter tip.")
    #configFormLayout.addRow("Cath %d Tip Length (mm): " % cath, self.tipLengthSliderWidget[cath])
    
    #
    # Catheter #cath Catheter diameter
    #
    self.catheterDiameterSliderWidget = ctk.ctkSliderWidget()
    self.catheterDiameterSliderWidget.singleStep = 0.1
    self.catheterDiameterSliderWidget.minimum = 0.1
    self.catheterDiameterSliderWidget.maximum = 10.0
    self.catheterDiameterSliderWidget.value = 1.0
    self.catheterDiameterSliderWidget.setToolTip("Set the diameter of the catheter")
    configFormLayout.addRow("Diameter (mm): ", self.catheterDiameterSliderWidget)
    
    #
    # Catheter #cath Catheter opacity
    #
    self.catheterOpacitySliderWidget = ctk.ctkSliderWidget()
    self.catheterOpacitySliderWidget.singleStep = 0.1
    self.catheterOpacitySliderWidget.minimum = 0.0
    self.catheterOpacitySliderWidget.maximum = 1.0
    self.catheterOpacitySliderWidget.value = 1.0
    self.catheterOpacitySliderWidget.setToolTip("Set the opacity of the catheter")
    configFormLayout.addRow("Opacity: ", self.catheterOpacitySliderWidget)

    #
    # Catheter #cath "Use coil positions for registration" check box
    #
    self.catheterRegUseCoilCheckBox = qt.QCheckBox()
    self.catheterRegUseCoilCheckBox.checked = 1
    self.catheterRegUseCoilCheckBox.enabled = 1
    self.catheterRegUseCoilCheckBox.setToolTip("Activate Tracking")
    configFormLayout.addRow("Cath Use Coil Pos: ", self.catheterRegUseCoilCheckBox)
    
    #
    # Catheter #cath registration points
    #
    #  Format: (<coil index>,<offset>),(<coil index>,<offset>),...
    # 
    self.catheterRegPointsLineEdit = qt.QLineEdit()
    self.catheterRegPointsLineEdit.text = '5.0,10.0,15.0,20.0'
    self.catheterRegPointsLineEdit.readOnly = False
    self.catheterRegPointsLineEdit.frame = True
    self.catheterRegPointsLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    configFormLayout.addRow("Cath Reg. Points: ", self.catheterRegPointsLineEdit)

    #--------------------------------------------------
    # Coil Selection
    #
    coilGroupBox = ctk.ctkCollapsibleGroupBox()
    coilGroupBox.title = "Coil Selection"
    coilGroupBox.collapsed = False
    
    layout.addWidget(coilGroupBox)
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
    self.nChannel = 8
    self.coilCheckBox = [None for i in range(self.nChannel)]
    
    for ch in range(self.nChannel):
      self.coilCheckBox[ch] = qt.QCheckBox()
      self.coilCheckBox[ch].checked = 0
      self.coilCheckBox[ch].text = "CH %d" % (ch + 1)

    nChannelHalf = int(self.nChannel/2)

    coilGroup1Layout = qt.QHBoxLayout()
    for ch in range(nChannelHalf):
      coilGroup1Layout.addWidget(self.coilCheckBox[ch])
    coilSelectionLayout.addRow("Active Coils:", coilGroup1Layout)
    
    coilGroup2Layout = qt.QHBoxLayout()
    for ch in range(nChannelHalf):
      coilGroup2Layout.addWidget(self.coilCheckBox[ch+nChannelHalf])
    coilSelectionLayout.addRow("", coilGroup2Layout)
      
    self.coilOrderDistalRadioButton = qt.QRadioButton("Distal First")
    self.coilOrderDistalRadioButton.checked = 1
    self.coilOrderProximalRadioButton = qt.QRadioButton("Proximal First")
    self.coilOrderProximalRadioButton.checked = 0
    self.coilOrderButtonGroup = qt.QButtonGroup()
    self.coilOrderButtonGroup.addButton(self.coilOrderDistalRadioButton)
    self.coilOrderButtonGroup.addButton(self.coilOrderProximalRadioButton)
    
    coilOrderGroupLayout = qt.QHBoxLayout()
    coilOrderGroupLayout.addWidget(self.coilOrderDistalRadioButton)
    coilOrderGroupLayout.addWidget(self.coilOrderProximalRadioButton)
    coilSelectionLayout.addRow("Coil Order:", coilOrderGroupLayout)

    #--------------------------------------------------
    # Coordinate System
    #
    coordinateGroupBox = ctk.ctkCollapsibleGroupBox()
    coordinateGroupBox.title = "Coordinate System"
    coordinateGroupBox.collapsed = False
    
    layout.addWidget(coordinateGroupBox)
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
    stabilizerGroupBox.collapsed = False
    
    layout.addWidget(stabilizerGroupBox)
    stabilizerLayout = qt.QFormLayout(stabilizerGroupBox)
    
    self.cutoffFrequencySliderWidget = ctk.ctkSliderWidget()
    self.cutoffFrequencySliderWidget.singleStep = 0.1
    self.cutoffFrequencySliderWidget.minimum = 0.10
    self.cutoffFrequencySliderWidget.maximum = 50.0
    self.cutoffFrequencySliderWidget.value = 7.5
    #self.cutoffFrequencySliderWidget.setToolTip("")
    stabilizerLayout.addRow("Cut-off frequency: ",  self.cutoffFrequencySliderWidget)

    #--------------------------------------------------
    # Egram 
    #
    egramGroupBox = ctk.ctkCollapsibleGroupBox()
    egramGroupBox.title = "Egram Data"
    egramGroupBox.collapsed = False
    
    layout.addWidget(egramGroupBox)
    egramLayout = qt.QFormLayout(egramGroupBox)

    self.egramDataSelector = slicer.qMRMLNodeComboBox()
    self.egramDataSelector.nodeTypes = ( ("vtkMRMLTextNode"), "" )
    self.egramDataSelector.selectNodeUponCreation = True
    self.egramDataSelector.addEnabled = True
    self.egramDataSelector.removeEnabled = False
    self.egramDataSelector.noneEnabled = False
    self.egramDataSelector.showHidden = True
    self.egramDataSelector.showChildNodeTypes = False
    self.egramDataSelector.setMRMLScene( slicer.mrmlScene )
    self.egramDataSelector.setToolTip( "Incoming Egram data" )

    egramLayout.addRow("Egram Cath: ", self.egramDataSelector)

    #--------------------------------------------------
    # Save Configuration
    #
    
    trackingDataSaveFrame = qt.QFrame()
    trackingDataSaveLayout = qt.QHBoxLayout(trackingDataSaveFrame)

    trackingDataSaveLayout.addStretch(1)
    
    self.saveTrackingDataDefaultConfigButton = qt.QPushButton()
    self.saveTrackingDataDefaultConfigButton.setCheckable(False)
    self.saveTrackingDataDefaultConfigButton.text = 'Save Current Configuration as Default'
    self.saveTrackingDataDefaultConfigButton.setToolTip("Save above configurations as default.")
    
    trackingDataSaveLayout.addWidget(self.saveTrackingDataDefaultConfigButton)
    
    layout.addWidget(trackingDataSaveFrame)
    
    #--------------------------------------------------
    # Connections
    #
    self.activeTrackingCheckBox.connect('clicked(bool)', self.onActiveTracking)
    self.trackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataSelected)
    self.egramDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onEgramDataSelected)
    self.catheterRegPointsLineEdit.editingFinished.connect(self.onCatheterRegPointsChanged)
    self.catheterDiameterSliderWidget.connect("valueChanged(double)", self.onCatheterDiameterChanged)
    self.catheterOpacitySliderWidget.connect("valueChanged(double)", self.onCatheterOpacityChanged)
    self.showCoilLabelCheckBox.connect('clicked(bool)', self.onCoilLabelChecked)

    for ch in range(self.nChannel):
      self.coilCheckBox[ch].connect('clicked(bool)', self.onCoilChecked)
    
    self.coilOrderDistalRadioButton.connect('clicked(bool)', self.onCoilChecked)
    self.coilOrderProximalRadioButton.connect('clicked(bool)', self.onCoilChecked)
    self.coordinateRPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateRMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.cutoffFrequencySliderWidget.connect("valueChanged(double)", self.onStabilizerCutoffChanged)
    self.saveTrackingDataDefaultConfigButton.connect('clicked(bool)', self.onSaveTrackingDataDefaultConfig)

    
  def onSwitchCatheter(self):
    td = self.currentCatheter
    if td == None:
      return

    if td.eventTag != '':
      self.activeTrackingCheckBox.checked == True
    else:
      self.activeTrackingCheckBox.checked == False
    
    # Enable/disable GUI components based on the state machine
    
    if self.isTrackingActive():
      self.activeTrackingCheckBox.checked = True
    else:
      self.activeTrackingCheckBox.checked = False

    self.catheterDiameterSliderWidget.value = td.radius * 2.0
    self.catheterOpacitySliderWidget.value = td.opacity

    str = ""
    for p in td.coilPositions:
      str += "%.f," % p
    self.catheterRegPointsLineEdit.text = str[:-1] # Remove the last ','
      
    self.showCoilLabelCheckBox.checked = td.showCoilLabel

    for ch in range(self.nChannel):
      self.coilCheckBox[ch].checked = td.activeCoils[ch]
    
    if td.axisDirections[0] > 0.0:
      self.coordinateRPlusRadioButton.checked = 1
    else:
      self.coordinateRMinusRadioButton.checked = 1
      
    if td.axisDirections[1] > 0.0:
      self.coordinateAPlusRadioButton.checked = 1
    else:
      self.coordinateAMinusRadioButton.checked = 1

    if td.axisDirections[2] > 0.0:
      self.coordinateSPlusRadioButton.checked = 1
    else:
      self.coordinateSMinusRadioButton.checked = 1

    self.egramDataSelector.setCurrentNode(td.egramDataNode)

    
  def enableCoilSelection(self, switch):
    
    if switch:
      for ch in range(self.nChannel):
        self.coilCheckBox[ch].enabled = 1
    else:
      for ch in range(self.nChannel):
        self.coilCheckBox[ch].enabled = 0

          
  def onActiveTracking(self):
    td = self.currentCatheter
    
    if td == None:
      return
    
    if self.activeTrackingCheckBox.checked == True:
      self.enableCoilSelection(0)
      td.activateTracking()

    else:
      self.enableCoilSelection(1)
      td.deactivateTracking()

      
  def onTrackingDataSelected(self):
    tdnode = self.trackingDataSelector.currentNode()
    if self.currentCatheter:
      self.currentCatheter.setTrackingDataNodeID(tdnode.GetID())
    

  def onEgramDataSelected(self):
    tdnode = self.trackingDataSelector.currentNode()
    edatanode = self.egramDataSelector.currentNode()
    self.setEgramDataNode(tdnode, edatanode)
      

  def onCatheterRegPointsChanged(self):
    text = self.catheterRegPointsLineEdit.text
    print("onCatheterRegPointsChanged(%s)" % (text))

    strarray = text.split(',')
    try:
      array = [float(ns) for ns in strarray]
      self.setCoilPositions(array, True)
    except ValueError:
      print('Format error in coil position string.')


  def onCatheterDiameterChanged(self, checked):
    self.setCatheterDiameter(self.catheterDiameterSliderWidget.value)
    
  
  def onCatheterOpacityChanged(self, checked):
    self.setCatheterOpacity(self.catheterOpacitySliderWidget.value, cath)

    
  def onCoilLabelChecked(self):
    self.setShowCoilLabel(self.showCoilLabelCheckBox.checked)

      
  def onCoilChecked(self):

    print("onCoilChecked(self):")
    activeCoils0 = [0] * self.nChannel
    for ch in range(self.nChannel):
      activeCoils0[ch] = self.coilCheckBox[ch].checked

    coilOrder0 = 'distal'
    if self.coilOrderProximalRadioButton.checked:
      coilOrder0 = 'proximal'

    self.setActiveCoils(activeCoils0, coilOrder0)

    
  def onSelectCoordinate(self):

    rPositive = self.coordinateRPlusRadioButton.checked
    aPositive = self.coordinateAPlusRadioButton.checked
    sPositive = self.coordinateSPlusRadioButton.checked
    
    self.setAxisDirections(rPositive, aPositive, sPositive)

    
  def onStabilizerCutoffChanged(self):

    frequency = self.cutoffFrequencySliderWidget.value
    self.setStabilizerCutoff(frequency)

  def onSaveTrackingDataDefaultConfig(self):
    
    self.saveDefaultTrackingDataConfig()

    
  #--------------------------------------------------
  # Logic fucntions
  #
  
  def setAxisDirections(self, rPositive, aPositive, sPositive):

    td = self.currentCatheter
    if td == None:
      print('setAxisDirections(): Error - No catheter specified.')

    if rPositive:
      td.setAxisDirection(0, 1.0)
    else:
      td.setAxisDirection(0, -1.0)
      
    if aPositive:
      td.setAxisDirection(1, 1.0)
    else:
      td.setAxisDirection(1, -1.0)
      
    if sPositive:
      td.setAxisDirection(2, 1.0)
    else:
      td.setAxisDirection(2, 1.0)

    td.updateCatheter()
    
      
  def setStabilizerCutoff(self, frequency):
    # TODO: Should the following be moved to catheter.py?

    td = self.currentCatheter
    tdnode = slicer.mrmlScene.GetNodeByID(td.trackingDataNodeID)
    
    if td and tdnode:
      nTransforms = tdnode.GetNumberOfTransformNodes()
      for i in range(nTransforms):
        tpnode = td.transformProcessorNodes[i]
        tpnode.SetStabilizationCutOffFrequency(frequency)

        
  def isTrackingActive(self):
    td = self.currentCatheter
    if td:
      return td.isActive()
    else:
      return False
    
      
  def saveDefaultTrackingDataConfig(self):
    td = self.currentCatheter
    if td:
      td.saveDefaultConfig()

        
  def switchCurrentTrackingData(self, tdnode):
    if not tdnode:
      return

    # if not (tdnode.GetID() in self.TrackingData):
    #   self.addNewTrackingData(tdnode)
    # 
    # return self.TrackingData[tdnode.GetID()]

  
  def setEgramDataNode(self, tdnode, edatanode):
    if not tdnode:
      return
    if not (tdnode.GetID() in self.TrackingData):
      print('Error - Current TrackingData is not valid')
    self.TrackingData[tdnode.GetID()].egramDataNode = edatanode

    
  #def addNewTrackingData(self, tdnode):
  #  if not tdnode:
  #    return
  #
  #  for key in self.TrackingData:
  #    if key == tdnode.GetID():
  #      print('TrackingData "%s" has already been registered.' % tdnode.GetID())
  #      return
  #    node = self.scene.GetNodeByID(key)
  #    if node:
  #      if node.GetName() == tdnode.GetName():
  #        print('TrackingData "%s" has an object with the same name: %s.' % (tdnode.GetID(), tdnode.GetName()))
  #        self.TrackingData[tdnode.GetID()] = self.TrackingData[key]
  #        del self.TrackingData[key] ## TODO: Should the existing one be kept?
  #        self.TrackingData[tdnode.GetID()].setID(tdnode.GetID())
  #        return
  #
  #  td = TrackingData()
  #  self.TrackingData[tdnode.GetID()] = td
  #  self.TrackingData[tdnode.GetID()].setID(tdnode.GetID())
  #  self.TrackingData[tdnode.GetID()].setLogic(self)
  #  
  #  self.TrackingData[tdnode.GetID()].loadDefaultConfig()
  #  
  #  self.setupFiducials(tdnode, 0)
  #  self.setupFiducials(tdnode, 1)
  #
  #  self.setTipLength(td.coilPositions[0][0], 0)  # The first coil position match the tip length
  #  self.setTipLength(td.coilPositions[1][0], 1)  # The first coil position match the tip length            
      

  def setTipLength(self, length):
    td = self.currentCatheter      
    if td:
      td.setTipLength(length)
      td.updateCatheter()

        
  def setCoilPositions(self, array, save=False):
    td = self.currentCatheter            
    if td:
      if len(array) <= len(td.coilPositions):
        td.coilPositions = array
        #i = 0
        #for p in array:
        #  td.coilPositions[index][i] = p
        #  td.setCoilPositions(index, p)
        #  i = i + 1
      print(td.coilPositions)
      # Make sure that the registration class instance references the tracking data
      self.registration.trackingData = self.TrackingData
      self.setTipLength(td.coilPositions[0])  # The first coil position match the tip length

        
  def setCatheterDiameter(self, diameter):
    td = self.currentCatheter
    if td:
      #td.radius[index] = diameter / 2.0
      td.setRadius(diameter / 2.0)
      td.updateCatheter()
    

  def setCatheterOpacity(self, opacity):
    td = self.currentCatheter      
    if td:
      #td.opacity[index] = opacity
      td.setOpacity(opacity)
      td.updateCatheter()

        
  def setShowCoilLabel(self, show):
    td = self.currentCatheter
    if td:
      #td.showCoilLabel = show
      td.setShowCoilLabel(show)
      td.updateCatheter()
        
    
  def setActiveCoils(self, coils0, coilOrder0):
    print("setActiveCoils(self, coils1, coilOrder1)")
    td = self.currentCatheter      
    if td:
      td.setActiveCoils(coils0)
      
      if coilOrder0 == 'distal':
        td.setCoilOrder(True)
      else:
        td.setCoilOrder(False)

      td.updateCatheter()
        
    return True


  def setupFiducials(self, tdnode):

    if not tdnode:
      return
    
    # Set up markups fiducial node, if specified in the connector node
    curveNodeID = str(tdnode.GetAttribute('MRTracking.' + self.catheterID + '.CurveNode'))
    curveNode = None

    #cathName = 'Catheter_%d' % index
    
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)
    else:
      curveNode = self.scene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      ## TODO: Name?
      tdnode.SetAttribute('MRTracking.CurveNode%d' % index, curveNode.GetID())

    td = self.currentCatheter
    
    # Set up tip model node
    tipModelID = tdnode.GetAttribute('MRTracking.tipModel%d' % index)
    if tipModelID != None:
      td.setTipModelNode(index, self.scene.GetNodeByID(tipModelID))
    else:
      td.setTipModelNode(index, None)

    tipTransformNodeID = str(tdnode.GetAttribute('MRTracking.tipTransform%d' % index))
    if tipTransformNodeID != None:
      td.setTipTransformNode(index, self.scene.GetNodeByID(tipTransformNodeID))
    else:
      td.setTipTransformNode(index, None)
      
          
    
    

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAddedEvent(self, caller, eventId, callData):
    print("Node added")
    print("New node: {0}".format(callData.GetName()))
        
    if str(callData.GetAttribute("ModuleName")) == self.moduleName:
      print ("parameterNode added")

    if callData.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      self.startTimer()

