import qt
import ctk
from MRTrackingUtils.catheter import *
from MRTrackingUtils.qcomboboxcatheter import *
from qt import QFrame

class QPointRecordingFrame(QFrame):

  # Signals
    
  def __init__(self, catheterComboBox=None, catheters=None, trigger=None):

    if catheterComboBox==None and catheters == None:
      print("QPointRecordingFrame: Error - 'catheters must be specified when catheterComboBox is not given.")
      return
      
    super(QFrame, self).__init__()
    self.nChannel = 8

    self.catheters = None
    self.activeCoils = [0] * self.nChannel
    self.recordPointsNodeID = None

    catheterComboBoxOn = True
    if catheterComboBox:
      self.catheterComboBox = catheterComboBox
      catheterComboBoxOn = False

    self.trigger = {
      'manual': True,
      'distance' : True,
      'timer' : True
    }
    
    if trigger:
      for key, value in trigger.items():
        if key in self.trigger:
          self.trigger[key] = value
        else:
          print('key=%s is not allowed.' % key)
      
    self.buildGUI(catheterComboBoxOn)

    if catheters:
      self.catheterComboBox.setCatheterCollection(catheters)
      
    self.catheterComboBox.currentIndexChanged.connect(self.onCatheterSelected)
    

  def getCurrentFiducials(self):
      return self.recordPointsSelector.currentNode()

    
  def buildGUI(self, catheterComboBoxOn):

    pointLayout = qt.QFormLayout(self)

    if catheterComboBoxOn:
      self.catheterComboBox = QComboBoxCatheter()
      pointLayout.addRow("Catheter: ", self.catheterComboBox)

    self.recordPointsSelector = slicer.qMRMLNodeComboBox()
    self.recordPointsSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.recordPointsSelector.selectNodeUponCreation = True
    self.recordPointsSelector.addEnabled = True
    self.recordPointsSelector.renameEnabled = True
    self.recordPointsSelector.removeEnabled = True
    self.recordPointsSelector.noneEnabled = True
    self.recordPointsSelector.showHidden = True
    self.recordPointsSelector.showChildNodeTypes = False
    self.recordPointsSelector.setMRMLScene( slicer.mrmlScene )
    self.recordPointsSelector.setToolTip( "Fiducials for recorded points" )
    pointLayout.addRow("Fiducial Node: ", self.recordPointsSelector)

    self.recordPointsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onRecordPointsSelected)

    #
    # Coil seleciton check boxes
    #
    self.coilCheckBox = [None for i in range(self.nChannel)]
    
    for ch in range(self.nChannel):
      self.coilCheckBox[ch] = qt.QCheckBox()
      self.coilCheckBox[ch].checked = self.activeCoils[ch]
      self.coilCheckBox[ch].text = "CH %d" % (ch + 1)

    for ch in range(self.nChannel):
      self.coilCheckBox[ch].connect('clicked(bool)', self.onCoilChecked)

    # Disable the coil check boxes.
    self.enableCoilSelection(False)

    nChannelHalf = int(self.nChannel/2)

    coilGroup1Layout = qt.QHBoxLayout()
    for ch in range(nChannelHalf):
      coilGroup1Layout.addWidget(self.coilCheckBox[ch])
    pointLayout.addRow("Active Coils:", coilGroup1Layout)
    
    coilGroup2Layout = qt.QHBoxLayout()
    for ch in range(nChannelHalf):
      coilGroup2Layout.addWidget(self.coilCheckBox[ch+nChannelHalf])
    pointLayout.addRow("", coilGroup2Layout)

    visibilityBoxLayout = qt.QHBoxLayout()
    self.visibilityGroup = qt.QButtonGroup()
    self.visibilityOnRadioButton = qt.QRadioButton("ON")
    self.visibilityOffRadioButton = qt.QRadioButton("Off")
    self.visibilityOffRadioButton.checked = 1
    visibilityBoxLayout.addWidget(self.visibilityOnRadioButton)
    self.visibilityGroup.addButton(self.visibilityOnRadioButton)
    visibilityBoxLayout.addWidget(self.visibilityOffRadioButton)
    self.visibilityGroup.addButton(self.visibilityOffRadioButton)

    pointLayout.addRow("Visibility: ", visibilityBoxLayout)
    self.visibilityOnRadioButton.connect("clicked(bool)", self.onVisibilityChanged)
    self.visibilityOffRadioButton.connect("clicked(bool)", self.onVisibilityChanged)


    ## Trigger
    #if sum(self.trigger.values()) > 1: # If there is a choice for trigger
    #  triggerBoxLayout = qt.QHBoxLayout()
    #  self.triggerGroup = qt.QButtonGroup()
    #  
    #  if self.trigger['manual']:
    #    self.triggerManualRadioButton = qt.QRadioButton("Manual")
    #    self.triggerManualRadioButton.checked = 1
    #    triggerBoxLayout.addWidget(self.triggerManualRadioButton)
    #    self.triggerGroup.addButton(self.triggerManualRadioButton)
    #    self.triggerManualRadioButton.connect("clicked(bool)", self.onTriggerChanged)
    #  
    #  if self.trigger['distance']:
    #    self.triggerDistanceRadioButton = qt.QRadioButton("Distance")
    #    triggerBoxLayout.addWidget(self.triggerDistanceRadioButton)
    #    self.triggerGroup.addButton(self.triggerDistanceRadioButton)
    #    self.triggerDistanceRadioButton.connect("clicked(bool)", self.onTriggerChanged)
    #  
    #  if self.trigger['timer']:
    #    self.triggerTimerRadioButton = qt.QRadioButton("Timer")    
    #    triggerBoxLayout.addWidget(self.triggerTimerRadioButton)
    #    self.triggerGroup.addButton(self.triggerTimerRadioButton)
    #    self.triggerTimerRadioButton.connect("clicked(bool)", self.onTriggerChanged)
    #
    #pointLayout.addRow("Trigger: ", triggerBoxLayout)


    # Distance-based collection
        # Minimum interval between two consective points
    self.pointRecordingDistanceSliderWidget = ctk.ctkSliderWidget()
    self.pointRecordingDistanceSliderWidget.singleStep = 0.1
    self.pointRecordingDistanceSliderWidget.minimum = 0.0
    self.pointRecordingDistanceSliderWidget.maximum = 20.0
    self.pointRecordingDistanceSliderWidget.value = 0.0
    self.pointRecordingDistanceSliderWidget.setToolTip("Minimum distance between the two consecutive points to trigger recording. If multiple points are being recorded, the RMS distance is used.")

    pointLayout.addRow("Min. Distance: ",  self.pointRecordingDistanceSliderWidget)

    activeBoxLayout = qt.QHBoxLayout()
    self.activeGroup = qt.QButtonGroup()
    self.activeOnRadioButton = qt.QRadioButton("ON")
    self.activeOffRadioButton = qt.QRadioButton("Off")
    self.activeOffRadioButton.checked = 1
    activeBoxLayout.addWidget(self.activeOnRadioButton)
    self.activeGroup.addButton(self.activeOnRadioButton)
    activeBoxLayout.addWidget(self.activeOffRadioButton)
    self.activeGroup.addButton(self.activeOffRadioButton)

    pointLayout.addRow("Active: ", activeBoxLayout)

    self.pointRecordingDistanceSliderWidget.connect("valueChanged(double)", self.pointRecordingDistanceChanged)
    self.activeOnRadioButton.connect('clicked(bool)', self.onActive)
    self.activeOffRadioButton.connect('clicked(bool)', self.onActive)

    # Manual collection
    buttonBoxLayout = qt.QHBoxLayout()    

    self.collectButton = qt.QPushButton()
    self.collectButton.setCheckable(False)
    self.collectButton.text = 'Collect'
    self.collectButton.setToolTip("Collect points from the catheters.")
    buttonBoxLayout.addWidget(self.collectButton)
    
    self.clearButton = qt.QPushButton()
    self.clearButton.setCheckable(False)
    self.clearButton.text = 'Clear'
    self.clearButton.setToolTip("Clear the collected points from the list.")
    buttonBoxLayout.addWidget(self.clearButton)

    self.numPointsLabel = qt.QLabel()
    self.numPointsLabel.setText(' Number of Fiducials: 0')
    buttonBoxLayout.addWidget(self.numPointsLabel)
    
    #self.numPointsLineEdit = qt.QLineEdit()
    #self.numPointsLineEdit.setReadOnly(True)
    #buttonBoxLayout.addWidget(self.numPointsLineEdit)
    
    pointLayout.addRow("", buttonBoxLayout)

    self.collectButton.connect(qt.SIGNAL("clicked()"), self.onCollectPoints)
    self.clearButton.connect(qt.SIGNAL("clicked()"), self.onClearPoints)

  def onActive(self):
    td = self.catheter = self.catheterComboBox.getCurrentCatheter()
    #td = self.currentCatheter
    if td == None:
      return
    if self.activeOnRadioButton.checked:
      # Add observer
      #fnode = td.pointRecordingMarkupsNode
      #if fnode:
        # Two observers are registered. The PointModifiedEvent is used to handle new points, whereas
        # the ModifiedEvent is used to capture the change of Egram parameter list (in the attribute)
        #tag = fnode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.controlPointsNodeUpdated, 2)
        #fnode.SetAttribute('SurfaceMapping.ObserverTag.Modified', str(tag))

      self.enableCoilSelection(False)
      td.pointRecordingMask = numpy.array(self.activeCoils)
      td.pointRecording = True
      
    else:
      td.pointRecording = False
      self.enableCoilSelection(True)
      #fnode = td.pointRecordingMarkupsNode
      #if fnode:
        #tag = fnode.GetAttribute('SurfaceMapping.ObserverTag.Modified')
        #if tag != None:
        #  fnode.RemoveObserver(int(tag))
        #  fnode.SetAttribute('SurfaceMapping.ObserverTag.Modified', None)

      

  def enableCoilSelection(self, switch):
    #
    # Disable widgets under "Source/Coil Selection" while tracking is active.
    #
    
    if switch:
      for ch in range(self.nChannel):
        self.coilCheckBox[ch].enabled = 1
      #self.trackingDataSelector.enabled = 1
    else:
      for ch in range(self.nChannel):
        self.coilCheckBox[ch].enabled = 0
      #self.trackingDataSelector.enabled = 0

      
  def onCoilChecked(self):

    print("onCoilChecked(self):")
    #self.activeCoils = [0] * self.nChannel
    for ch in range(self.nChannel):
      self.activeCoils[ch] = self.coilCheckBox[ch].checked

      
  def onCatheterSelected(self):

    if self.catheterComboBox == None:
      return

    self.catheter = self.catheterComboBox.getCurrentCatheter()
    
    if self.catheter == None:
      self.enableCoilSelection(False)
    else:
      self.enableCoilSelection(True)
    

  #def onTriggerChanged(self):
  #  
  #  if self.triggerManualRadioButton.checked:
  #    self.enableManualTrigger(True)
  #    self.enableDistanceTrigger(False)
  #    self.enableTimerTrigger(False)
  #  if self.triggerDistanceRadioButton.checked:
  #    self.enableManualTrigger(False)
  #    self.enableDistanceTrigger(True)
  #    self.enableTimerTrigger(True)
  #  if self.triggerTimerRadioButton.checked:
  #    self.enableManualTrigger(False)
  #    self.enableDistanceTrigger(False)
  #    self.enableTimerTrigger(True)
  #
  #    
  #def enableManualTrigger(self, s):
  #  if s:
  #    self.collectButton.enabled = 1
  #    self.clearButton.enabled = 1
  #  else:
  #    self.collectButton.enabled = 0
  #    self.clearButton.enabled = 1
  #
  #    
  #def enableDistanceTrigger(self, s):
  #  pass
  #
  #def enableTimerTrigger(self, s):
  #  pass
  #
    
  def onCollectPoints(self):

    if self.catheterComboBox == None:
      return
      
    fNode = self.recordPointsSelector.currentNode()
    catheter = self.catheterComboBox.getCurrentCatheter()
    
    if fNode == None or catheter == None:
      msgBox = QMessageBox()
      msgBox.setIcon(QMessageBox.Information)
      msgBox.setText("Fiducial node / catheter is not specified.")
      msgBox.setWindowTitle("Error")
      msgBox.setStandardButtons(QMessageBox.Ok)
      msgBox.buttonClicked.connect(msgButtonClick)
      returnValue = msgBox.exec()
      return

    positions = catheter.getActiveCoilPositions(activeCoils=self.activeCoils)

    for pos in positions:
      fNode.AddFiducial(pos[0], pos[1], pos[2])
    

  def onClearPoints(self):
    fNode = self.recordPointsSelector.currentNode()
    
    if fNode:
      fNode.RemoveAllMarkups()
      # Note: RemoveAllMarkups() does not invoke a PointModifiedEvent
      fNode.InvokeEvent(slicer.vtkMRMLMarkupsNode.PointModifiedEvent)
      

      
  def onVisibilityChanged(self):

    if self.visibilityOnRadioButton.checked == True:
      self.fiducialsVisible = True
    else:
      self.fiducialsVisible = False

    fNode = self.recordPointsSelector.currentNode()
    
    if fNode:
      dnode = fNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)

    # TODO: Update the radio button, when the recordpointselector is updated.

    
  def onRecordPointsSelected(self):
    
    # Check if there is any node previously selected; if there is, remove the observer
    if self.recordPointsNodeID:
      fNode = slicer.mrmlScene.GetNodeByID(self.recordPointsNodeID)
      if fNode:
        fNode.RemoveObserver(int(self.recordPointsTag))
          
      self.printNumPoints(-1)
      self.recordPointsNodeID = None
      self.recordPointsTag = None


    fNode = self.recordPointsSelector.currentNode()

    if fNode:
      self.recordPointsNodeID = fNode.GetID()
      self.recordPointsTag = fNode.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.recordPointsUpdated, 2)
      fNode.Modified()
      
      # For Egram recording
      td = self.catheterComboBox.getCurrentCatheter()
      if td:
        td.pointRecordingMarkupsNode = fNode
        fdnode = fNode.GetDisplayNode()
        if fdnode == None:
          fdnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialDisplayNode')
          slicer.mrmlScene.AddNode(fdnode)
          fNode.SetAndObserveDisplayNodeID(fdnode.GetID())
        if fNode:
          fdnode.SetTextScale(0.0)  # Hide the label
      
      
  def recordPointsUpdated(self,caller,event):
    if self.recordPointsNodeID:
      fNode = slicer.mrmlScene.GetNodeByID(self.recordPointsNodeID)
      nPoints = fNode.GetNumberOfFiducials()
      self.printNumPoints(nPoints)

      
  def printNumPoints(self, n):
    if n < 0:
      self.numPointsLabel.setText(' Number of Fiducials: --')
    else:
      self.numPointsLabel.setText(' Number of Fiducials: %d' % n)

      
  def pointRecordingDistanceChanged(self):
    d = self.pointRecordingDistanceSliderWidget.value
    catheter = self.catheterComboBox.getCurrentCatheter()
    if catheter == None:
      return
    catheter.pointRecordingDistance = d

    
  def controlPointsNodeUpdated(self,caller,event):
    td = self.catheterComboBox.getCurrentCatheter()
    #td = self.currentCatheter
    fnode = td.pointRecordingMarkupsNode
    paramListStr = fnode.GetAttribute('MRTracking.' + str(td.catheterID) + '.EgramParamList')
    if paramListStr:
      print(paramListStr)
      paramList = paramListStr.split(',')
      print(paramList)
      if len(paramList) != self.paramSelector.count - 1: # Note: The QComboBox has 'None' has the first item.
        self.paramSelector.clear()
        self.paramSelector.addItem('None')
        for p in paramList:
          self.paramSelector.addItem(p)
      else:
        i = 1
        for p in paramList:
          self.paramSelector.setItemText(i, p)
          i = i + 1
