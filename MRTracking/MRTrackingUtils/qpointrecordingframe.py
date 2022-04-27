import qt
from MRTrackingUtils.catheter import *
from MRTrackingUtils.qcomboboxcatheter import *
from qt import QFrame

class QPointRecordingFrame(QFrame):

  # Signals
    
  def __init__(self, catheterComboBox=None, catheters=None):

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

    self.buildGUI(catheterComboBoxOn)

    if catheters:
      self.catheterComboBox.setCatheterCollection(catheters)
      
    self.catheterComboBox.currentIndexChanged.connect(self.onCatheterSelected)
    

  #def setCatheterComboBox(self, catheterComboBox, catheters):
  #  # Must be called when catheterComboBoxOn is False
  #  self.catheterComboBox = catheterComboBox
  #  self.catheterComboBox.setCatheterCollection(catheters)
  #  self.catheterComboBox.currentIndexChanged.connect(self.onCatheterSelected)    
  #
  #  
  #def setCatheters(self, catheters):
  #  # Must be called when catheterComboBoxOn is True
  #  if self.catheterComboBox:
  #    self.catheterComboBox.setCatheterCollection(catheters)
    

  def getCurrentFiducials(self):
      return self.recordPointsSelector.currentNode()

    
  def buildGUI(self, catheterComboBoxOn):

    pointLayout = qt.QFormLayout(self)

    if catheterComboBoxOn:
      self.catheterComboBox = QComboBoxCatheter()
      pointLayout.addRow("Catheter: ", self.catheterComboBox)

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
    
    ## TODO: Should it be called from the module class, either Widget or Logic?
    #self.addSceneObservers()
    
  def onActive(self):
    
    if self.activeCheckBox.checked == 1:
      self.startRecording()
    else:
      self.stopRecording()


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

      
  def recordPointsUpdated(self,caller,event):
    print('recordPointsUpdated(self,caller,event)')
    if self.recordPointsNodeID:
      fNode = slicer.mrmlScene.GetNodeByID(self.recordPointsNodeID)
      nPoints = fNode.GetNumberOfFiducials()
      self.printNumPoints(nPoints)

      
  def printNumPoints(self, n):
    if n < 0:
      self.numPointsLabel.setText(' Number of Fiducials: --')
    else:
      self.numPointsLabel.setText(' Number of Fiducials: %d' % n)
      
