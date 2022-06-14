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
    self.moduleName = 'MRTracking'   #Used for config

  def buildMainPanel(self, frame):

    layout = qt.QVBoxLayout(frame)
    selectorLayout = qt.QFormLayout()
    layout.addLayout(selectorLayout)
    
    self.activeTrackingCheckBox = qt.QCheckBox()
    self.activeTrackingCheckBox.checked = 0
    self.activeTrackingCheckBox.enabled = 1
    self.activeTrackingCheckBox.setToolTip("Activate Tracking")
    selectorLayout.addRow("Active: ", self.activeTrackingCheckBox)

    #--------------------------------------------------
    # Coil Selection
    #
    coilGroupBox = ctk.ctkCollapsibleGroupBox()
    coilGroupBox.title = "Source / Coil Selection"
    coilGroupBox.collapsed = False
    
    layout.addWidget(coilGroupBox)
    coilSelectionLayout = qt.QFormLayout(coilGroupBox)

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
    coilSelectionLayout.addRow("Source: ", self.trackingDataSelector)
    
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
    # Catheter Configuration

    configGroupBox = ctk.ctkCollapsibleGroupBox()
    configGroupBox.title = "Catheter Configuration"
    configGroupBox.collapsed = False

    layout.addWidget(configGroupBox)
    configFormLayout = qt.QFormLayout(configGroupBox)
    
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
    # Catheter color
    #
    colorLayout = qt.QHBoxLayout()
    self.colorButton = qt.QPushButton()
    self.colorButton.setCheckable(False)
    self.colorButton.text = '  '
    self.colorButton.setToolTip("Change the color of the catheter.")
    colorLayout.addWidget(self.colorButton)
    colorLayout.addStretch(2) 
    #configFormLayout.addRow("Color: ", self.colorButton)
    configFormLayout.addRow("Color: ", colorLayout )
    
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
    #self.catheterRegPointsLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    configFormLayout.addRow("Coil positions: ", self.catheterRegPointsLineEdit)

    #
    # Check box to show/hide coil labels 
    #
    self.showCoilLabelCheckBox = qt.QCheckBox()
    self.showCoilLabelCheckBox.checked = 0
    self.showCoilLabelCheckBox.setToolTip("Show/hide coil labels")
    configFormLayout.addRow("Show Coil Labels: ", self.showCoilLabelCheckBox)

    #
    # Sheath
    #
    self.sheathRangeLineEdit = qt.QLineEdit()
    self.sheathRangeLineEdit.text = '0-3'
    self.sheathRangeLineEdit.readOnly = False
    self.sheathRangeLineEdit.frame = True
    configFormLayout.addRow('Sheath Coils (e.g., "0-3"): ', self.sheathRangeLineEdit)

    
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

    self.triggerComboBox = QComboBoxCatheter()
    self.triggerComboBox.setCatheterCollection(self.catheters)
    self.triggerComboBox.setCurrentCatheterNone()
    stabilizerLayout.addRow("Acq. Trigger:", self.triggerComboBox)

    #-- Tracking data acquisition window.
    self.windowRangeWidget = ctk.ctkRangeWidget()
    self.windowRangeWidget.setToolTip("Set acquisition window (ms)")
    self.windowRangeWidget.setDecimals(3)
    self.windowRangeWidget.singleStep = 1
    self.windowRangeWidget.minimumValue = 0.0
    self.windowRangeWidget.maximumValue = 1000.0
    self.windowRangeWidget.minimum = 0.0
    self.windowRangeWidget.maximum = 1000.0
    stabilizerLayout.addRow("Acq. Window:", self.windowRangeWidget)
    

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
    
    self.saveConfigButton = qt.QPushButton()
    self.saveConfigButton.setCheckable(False)
    self.saveConfigButton.text = 'Save'
    self.saveConfigButton.setToolTip("Save/add current configurations.")

    self.removeConfigButton = qt.QPushButton()
    self.removeConfigButton.setCheckable(False)
    self.removeConfigButton.text = 'Remove'
    self.removeConfigButton.setToolTip("Remove current configurations.")

    self.saveDefaultConfigButton = qt.QPushButton()
    self.saveDefaultConfigButton.setCheckable(False)
    self.saveDefaultConfigButton.text = 'Save as Default'
    self.saveDefaultConfigButton.setToolTip("Save above configurations as default.")

    trackingDataSaveLayout.addWidget(self.saveConfigButton)
    trackingDataSaveLayout.addWidget(self.removeConfigButton)    
    trackingDataSaveLayout.addWidget(self.saveDefaultConfigButton)
    
    layout.addWidget(trackingDataSaveFrame)
    
    #--------------------------------------------------
    # Connections
    #
    self.activeTrackingCheckBox.connect('clicked(bool)', self.onActiveTracking)
    self.trackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataSelected)
    self.egramDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onEgramDataSelected)
    self.catheterRegPointsLineEdit.editingFinished.connect(self.onCatheterRegPointsChanged)
    self.sheathRangeLineEdit.editingFinished.connect(self.onCatheterSheathRangeChanged)
    self.catheterDiameterSliderWidget.connect("valueChanged(double)", self.onCatheterDiameterChanged)
    self.catheterOpacitySliderWidget.connect("valueChanged(double)", self.onCatheterOpacityChanged)
    self.colorButton.connect('clicked(bool)', self.onColorButtonClicked)
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
    self.windowRangeWidget.connect('valuesChanged(double, double)', self.onUpdateWindow)

    self.saveConfigButton.connect('clicked(bool)', self.onSaveConfig)
    self.removeConfigButton.connect('clicked(bool)', self.onRemoveConfig)
    self.saveDefaultConfigButton.connect('clicked(bool)', self.onSaveDefaultConfig)

    self.triggerComboBox.currentIndexChanged.connect(self.onTriggerSelected)
    
    #--------------------------------------------------
    # Load catheter configurations
    #
    
    # TODO: Should it be done in MRTrackingLogic or CatheterCollection?

    self.loadSavedConfig()

    
  def onSwitchCatheter(self):
    td = self.currentCatheter
    if td == None:
      return

    if td.eventTag != '':
      self.activeTrackingCheckBox.checked == True
    else:
      self.activeTrackingCheckBox.checked == False
    
    # Enable/disable GUI components based on the state machine

    # Active
    if td.isActive():
      self.activeTrackingCheckBox.checked = True
      self.enableCoilSelection(0)
    else:
      self.activeTrackingCheckBox.checked = False
      self.enableCoilSelection(1)

    # Source / Coils Selection
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentCatheter.trackingDataNodeID)
    self.trackingDataSelector.setCurrentNode(tdnode)
    
    for ch in range(self.nChannel):
      self.coilCheckBox[ch].checked = td.activeCoils[ch]

    # Catheter Configuration
    self.catheterDiameterSliderWidget.value = td.radius * 2.0
    self.catheterOpacitySliderWidget.value = td.opacity
    
    c = qt.QColor()
    c.setRedF(td.modelColor[0])
    c.setGreenF(td.modelColor[1])
    c.setBlueF(td.modelColor[2])
    self.colorButton.setStyleSheet("background-color : " + str(c))

    strReg = ""
    for p in td.coilPositions:
      strReg += "%.f," % p
    self.catheterRegPointsLineEdit.text = strReg[:-1] # Remove the last ','
      
    self.showCoilLabelCheckBox.checked = td.showCoilLabel

    # Coordinate System
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

    # Stabilizer
    self.cutoffFrequencySliderWidget.value = td.cutOffFrequency
    
    if td.acquisitionTrigger:
      self.triggerComboBox.blockSignals(True)
      self.triggerComboBox.setCurrentCatheter(td.acquisitionTrigger)
      self.triggerComboBox.blockSignals(False)
      self.windowRangeWidget.blockSignals(True)      
      self.windowRangeWidget.minimumValue = td.acquisitionWindowDelay[0]
      self.windowRangeWidget.maximumValue = td.acquisitionWindowDelay[1]
      self.windowRangeWidget.blockSignals(False)      
    else:
      self.triggerComboBox.setCurrentCatheterNone()
      self.windowRangeWidget.enabled = False
      
    # Egram Data
    if td.egramDataNodeID:
      enode = slicer.mrmlScene.GetNodeByID(td.egramDataNodeID)
      if enode:
        self.egramDataSelector.setCurrentNode(enode)

    
  def enableCoilSelection(self, switch):
    #
    # Disable widgets under "Source/Coil Selection" while tracking is active.
    #
    
    if switch:
      for ch in range(self.nChannel):
        self.coilCheckBox[ch].enabled = 1
      self.trackingDataSelector.enabled = 1
    else:
      for ch in range(self.nChannel):
        self.coilCheckBox[ch].enabled = 0
      self.trackingDataSelector.enabled = 0

          
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
    if tdnode and self.currentCatheter:
      self.currentCatheter.setTrackingDataNodeID(tdnode.GetID())
    

  def onEgramDataSelected(self):
    edatanode = self.egramDataSelector.currentNode()
    if edatanode:
      self.setEgramDataNode(edatanode)
      

  def onCatheterRegPointsChanged(self):
    text = self.catheterRegPointsLineEdit.text
    print("onCatheterRegPointsChanged(%s)" % (text))

    strarray = text.split(',')
    print(strarray)
    try:
      array = [float(ns) for ns in strarray]
      self.setCoilPositions(array, True)
    except ValueError:
      print('Format error in coil position string.')

  def onCatheterSheathRangeChanged(self):
    text = self.sheathRangeLineEdit.text
    print("onCatheterSheathRangeChanged(%s)" % (text))
    
    strarray = text.split('-')
    try:
      array = [int(ns) for ns in strarray]
      if len(array) == 2:
        self.setSheathRange(array[0], array[1])
      else:
        print('Illegal format.')
    except ValueError:
      print('Format error in coil position string.')


  def onCatheterDiameterChanged(self, checked):
    self.setCatheterDiameter(self.catheterDiameterSliderWidget.value)
    
  
  def onCatheterOpacityChanged(self, checked):
    self.setCatheterOpacity(self.catheterOpacitySliderWidget.value)


  def onColorButtonClicked(self):
    qc =  qt.QColorDialog.getColor()
    r = qc.redF()
    g = qc.greenF()
    b = qc.blueF()
    color = [r, g, b]
    self.setCatheterColor(color)
    self.colorButton.setStyleSheet("background-color : " + str(qc))

    
    
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


  def onTriggerSelected(self):
    
    if self.triggerComboBox.getCurrentCatheter() == None:
      self.windowRangeWidget.enabled = 0
      self.disableAcquisitionWindow()
    else:
      self.windowRangeWidget.enabled = 1
      self.enableAcquisitionWindow()


  def onUpdateWindow(self, min, max):
    td = self.currentCatheter
    if td:
      td.setAcquisitionWindow(min, max)
      
    
  def onSaveConfig(self):
    
    td = self.currentCatheter
    if td:
      name = td.name
      self.saveConfig(name)

    
  def onRemoveConfig(self):
    
    td = self.currentCatheter
    if td:
      name = td.name
      self.removeConfig(name)

    
  def onSaveDefaultConfig(self):

    td = self.currentCatheter
    if td:
      self.saveConfig('default')

    
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
      td.setAxisDirection(2, -1.0)

    td.updateCatheter()
    
      
  def setStabilizerCutoff(self, frequency):

    td = self.currentCatheter
    td.setCutOffFrequency(frequency)
    # if tpnode in td.transformProcessorNodes:
    #   tpnode.SetStabilizationCutOffFrequency(frequency)


  def enableAcquisitionWindow(self):
    td = self.currentCatheter
    trigger = self.triggerComboBox.getCurrentCatheter()
    if td and trigger:
      startDelay = self.windowRangeWidget.minimum
      endDelay = self.windowRangeWidget.maximum
      td.setAcquisitionTrigger(trigger, startDelay, endDelay)

      
  def disableAcquisitionWindow(self):
    td = self.currentCatheter
    if td:
      td.removeAcquisitionTrigger()

      
  def switchCurrentTrackingData(self, tdnode):
    if not tdnode:
      return

    
  def setEgramDataNode(self, edatanode):
    td = self.currentCatheter
    if not td:
      return
    td.egramDataNodeID = edatanode.GetID()


  def setCoilPositions(self, array, save=False):
    td = self.currentCatheter            
    if td:
      n = len(array)
      max_n = len(td.coilPositions)
      if n > max_n:
        print ("Warning: The number of coil positions is greater than the number of coils.")
        n = 8
        
      coilPositions = [0.0] * 8
      coilPositions[:n] = array[:n]
      if n < max_n:
        coilPositions[n:] = [0.0]*(max_n-n)

      td.setCoilPosition(coilPositions)


  def setCatheterDiameter(self, diameter):
    td = self.currentCatheter
    if td:
      #td.radius[index] = diameter / 2.0
      td.setRadius(diameter / 2.0)
      td.updateCatheter()
    

  def setCatheterOpacity(self, opacity):
    td = self.currentCatheter      
    if td:
      td.setOpacity(opacity)
      td.updateCatheter()

  
  def setCatheterColor(self, color):
    td = self.currentCatheter      
    if td:
      td.setModelColor(color)
      td.updateCatheter()

        
  def setShowCoilLabel(self, show):
    td = self.currentCatheter
    if td:
      #td.showCoilLabel = show
      td.setShowCoilLabel(show)
      td.updateCatheter()
        
  def setSheathRange(self, ch0, ch1):
    td = self.currentCatheter
    if td:
      td.setSheathRange(ch0, ch1)
      
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


  def loadSavedConfig(self):

    if self.catheters == None:
      print('MRTrackingCatheterConfig.loadSavedConfig(): No catheter colleciton is found.')
      return
    
    cathList = self.getCatheterNameListFromConfig()
    
    for name in cathList:
      newCath = Catheter(name)
      self.catheters.add(newCath)
      self.loadConfig(name, newCath)

    # Switch to the first catheter
    self.switchCatheterByIndex(0)
    

  def loadDefaultConfig(self):
    
    loadConfig('default')

    
  def loadConfig(self, cathName, cath=None):

    td = cath
    if td == None:
      td = self.currentCatheter
    
    ## Load config
    settings = qt.QSettings()
    setting = []

    # Show coil label
    setting = settings.value(self.moduleName + '/' + 'ShowCoilLabel.' + cathName)
    if setting != None:
      #td.showCoilLabel = bool(int(setting)) # TODO: Does this work?
      td.showCoilLabel = (setting == 'true')

    # Source
    setting = settings.value(self.moduleName + '/' + 'TrackingDataBundleNode.' + cathName)
    if setting != '':
      # Try to find the TrackingDataBundleNode in the scene
      col = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLIGTLTrackingDataBundleNode", setting)
      tdnode = None
      if col.GetNumberOfItems() > 0:
        tdnode = col.GetItemAsObject(0) # Set the first one, if there are more than one nodes
      else:
        # If no node is found in the scene, create one.
        tdnode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLIGTLTrackingDataBundleNode")
        tdnode.SetName(setting)
      td.setTrackingDataNodeID(tdnode.GetID())
      
    # Active coils
    setting = settings.value(self.moduleName + '/' + 'ActiveCoils.' + cathName)
    if setting != None:
      array = [bool(int(i)) for i in setting]
      
      if len(array) > 0:
        try:
          if len(array) <= len(td.activeCoils):
            td.activeCoils = array
        except ValueError:
          print('Format error in activeCoils string.')
          
    # Coil positions
    setting = settings.value(self.moduleName + '/' + 'CoilPositions.' + cathName)
    array = []
    if setting != None:
      print('Found ' + cathName + ' in Setting')
      array = [float(f) for f in setting]
        
    if len(array) > 0:
      try:
        if len(array) <= len(td.coilPositions):
          td.coilPositions = array
      except ValueError:
        print('Format error in coilConfig string.')

    # Coil order
    setting = settings.value(self.moduleName + '/' + 'CoilOrder.' + cathName)
    if setting != None:
      td.coilOrder = bool(int(setting)) # TODO: Does this work?

    # Axis direction
    setting = settings.value(self.moduleName + '/' + 'AxisDirections.' + cathName)
    if setting != None:
      td.axisDirections = [float(s) for s in setting]

    # Cut-off frequency
    setting = settings.value(self.moduleName + '/' + 'CutOffFrequency.' + cathName)
    if setting != None:
      td.cutOffFrequency = float(setting) # TODO: Does this work?

    # Opacity
    setting = settings.value(self.moduleName + '/' + 'Opacity.' + cathName)
    if setting != None:
      td.opacity = float(setting)

    # Radius
    setting = settings.value(self.moduleName + '/' + 'Radius.' + cathName)
    if setting != None:
      td.radius = float(setting)

    # Model color
    setting = settings.value(self.moduleName + '/' + 'ModelColor.' + cathName)
    if setting != None:
      td.modelColor = [float(s) for s in setting]

    # Egram
    setting = settings.value(self.moduleName + '/' + 'EgramDataNode.' + cathName)
    if setting != '':
      # Try to find the TrackingDataBundleNode in the scene
      col = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLTextNode", setting)
      tnode = None
      if col.GetNumberOfItems() > 0:
        tnode = col.GetItemAsObject(0) # Set the first one, if there are more than one nodes
      else:
        # If no node is found in the scene, create one.        
        tnode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode")
        tnode.SetName(setting)
      td.setEgramDataNodeID(tnode.GetID())

      
  def saveConfig(self, cathName, cath=None):

    saveSource=True
    saveEgram=True

    if cathName == 'default':
      saveSource=False
      saveEgram=False
    
    self.addCatheterNameToConfig(cathName)

    td = cath
    if td == None:
      td = self.currentCatheter

    if td == None:
      print('MRTrackingCatheterConfig.saveConfig(): No catheter is selected')
      return

    settings = qt.QSettings()

    settings.setValue(self.moduleName + '/' + 'ShowCoilLabel.' + cathName, td.showCoilLabel)

    if saveSource:
      tdnode = slicer.mrmlScene.GetNodeByID(td.trackingDataNodeID)
      if tdnode:
        settings.setValue(self.moduleName + '/' + 'TrackingDataBundleNode.' + cathName, tdnode.GetName())
      else:
        settings.setValue(self.moduleName + '/' + 'TrackingDataBundleNode.' + cathName, '')
    else:
      settings.setValue(self.moduleName + '/' + 'TrackingDataBundleNode.' + cathName, '')
    
    value = [int(b) for b in td.activeCoils]
    settings.setValue(self.moduleName + '/' + 'ActiveCoils.' + cathName, value)
    settings.setValue(self.moduleName + '/' + 'CoilPositions.' + cathName, td.coilPositions)
    settings.setValue(self.moduleName + '/' + 'CoilOrder.' + cathName, int(td.coilOrder))
    settings.setValue(self.moduleName + '/' + 'AxisDirections.' + cathName, td.axisDirections)
    settings.setValue(self.moduleName + '/' + 'CutOffFrequency.' + cathName, td.cutOffFrequency)
    settings.setValue(self.moduleName + '/' + 'Opacity.' + cathName, td.opacity)
    settings.setValue(self.moduleName + '/' + 'Radius.' + cathName, td.radius)
    settings.setValue(self.moduleName + '/' + 'ModelColor.' + cathName, td.modelColor)
    if saveEgram:
      enode = slicer.mrmlScene.GetNodeByID(td.egramDataNodeID)
      if enode:
        settings.setValue(self.moduleName + '/' + 'EgramDataNode.' + cathName, enode.GetName())
      else:
        settings.setValue(self.moduleName + '/' + 'EgramDataNode.' + cathName, '')
    else:
      settings.setValue(self.moduleName + '/' + 'EgramDataNode.' + cathName, '')
      

  def removeConfig(self, cathName, cath=None):

    self.removeCatheterNameFromConfig(cathName)
    
    td = cath
    if td == None:
      td = self.currentCatheter

    if td == None:
      print('MRTrackingCatheterConfig.removeConfig(): No catheter is selected')
      return

    settings = qt.QSettings()

    settings.remove(self.moduleName + '/' + 'ShowCoilLabel.' + cathName)
    settings.remove(self.moduleName + '/' + 'TrackingDataBundleNode.' + cathName)
    settings.remove(self.moduleName + '/' + 'ActiveCoils.' + cathName)
    settings.remove(self.moduleName + '/' + 'CoilPositions.' + cathName)
    settings.remove(self.moduleName + '/' + 'CoilOrder.' + cathName)
    settings.remove(self.moduleName + '/' + 'AxisDirections.' + cathName)
    settings.remove(self.moduleName + '/' + 'CutOffFrequency.' + cathName)
    settings.remove(self.moduleName + '/' + 'Opacity.' + cathName)
    settings.remove(self.moduleName + '/' + 'Radius.' + cathName)
    settings.remove(self.moduleName + '/' + 'ModelColor.' + cathName)
    settings.remove(self.moduleName + '/' + 'EgramDataNode.' + cathName)
      
    
  def getCatheterNameListFromConfig(self):

    settings = qt.QSettings()
    
    setting = settings.value(self.moduleName + '/' + 'CathList')
    if setting == None:
      return []
    else:
      return list(setting)

    
  def addCatheterNameToConfig(self, cathName):

    nameList = self.getCatheterNameListFromConfig()

    if cathName == None or cathName == '':
      return 0

    if (type(nameList) == list) and (cathName in nameList):
      # The name already exists in the config
      return 0

    settings = qt.QSettings()
    
    setting = settings.value(self.moduleName + '/' + 'CathList')

    if type(setting) == tuple:
      setting = list(setting)
      setting.append(cathName)
    else:
      setting = [cathName]
      
    settings.setValue(self.moduleName + '/' + 'CathList', setting)
    
    return 1


  def removeCatheterNameFromConfig(self, cathName):
    
    nameList = self.getCatheterNameListFromConfig()
    
    print(nameList)
    
    if cathName in nameList:
      nameList.remove(cathName)

    settings = qt.QSettings()
    settings.setValue(self.moduleName + '/' + 'CathList', nameList)
      
      
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
    

