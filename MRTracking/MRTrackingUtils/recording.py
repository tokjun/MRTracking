import ctk
import qt
import slicer
import vtk
from os.path import exists
from MRTrackingUtils.panelbase import *

#------------------------------------------------------------
#
# MRTrackingRecording
#

#
# This recording class records received catheter tracking and Egram data and save them in an output file.
# The class detects every MRML node that are used to receive data from catheter tracking systems
# (e.g., EnSite, MR scanner) based on their node types. Those types include:
#
#    - 'vtkMRMLIGTLTrackingDataBundleNode'
#    - 'vtkMRMLTextNode'
#
# Each frame of tracking and Egram data is stored as a line in the output file with the following format:
#
#    TYPE NAME TIMESTAMP DATA
#
# where
#
#    TYPE:      Data type, either 'TDATA' or 'STRING'.
#    NAME:      The message name, which is also used as a node name when the message is imported in 3D Slicer.     
#    TIMESTAMP: Time stamp (floating point converted to a string)
#    DATA:      Tracking or string data.
#
# The fields are separated by a single tab '\n'. The DATA fields ends at the end of line (EOL). 
# When the line contains a TDATA frame, the DATA field is formatted as:
#
#    X_0 Y_0 Z_0 X_1 Y_1 Z_1 ... X_(N-1) Y_(N-1) Z_(N-1)
#
# When a line contains a STRING frame, the DATA field simply contains a ASCII string with EOLs replaced with tabs.
#
# The recorded data can later be used to replay the tracking using MRCatheterTrackingSim, which is available at:
#
#    https://github.com/tokjun/MRCatheterTrackingSim
#

class MRTrackingRecording(MRTrackingPanelBase):

  def __init__(self, label="Recording"):
    super(MRTrackingRecording, self).__init__(label)

    self.nChannel = 8
    
    self.recfile = None
    self.eventTags = {}
    self.lastMTime = {}
    self.activeCoils = [0] * self.nChannel

    self.recordPointsNodeID = None
    self.recordPointsTag = None
    
    
  def buildMainPanel(self, frame):

    layout = qt.QVBoxLayout(frame)

    #--------------------------------------------------
    # File recording
    #
    fileGroupBox = ctk.ctkCollapsibleGroupBox()
    fileGroupBox.title = "File Recording"
    fileGroupBox.collapsed = False
    
    layout.addWidget(fileGroupBox)
    fileLayout = qt.QFormLayout(fileGroupBox)
    fileBoxLayout = qt.QHBoxLayout()

    self.fileLineEdit = qt.QLineEdit()
    self.fileDialogBoxButton = qt.QPushButton()
    self.fileDialogBoxButton.setCheckable(False)
    self.fileDialogBoxButton.text = '...'
    self.fileDialogBoxButton.setToolTip("Open file dialog box.")
    
    fileBoxLayout.addWidget(self.fileLineEdit)
    fileBoxLayout.addWidget(self.fileDialogBoxButton)
    fileLayout.addRow("File Path:", fileBoxLayout)
    
    self.activeCheckBox = qt.QCheckBox()
    self.activeCheckBox.checked = 0
    self.activeCheckBox.enabled = 1
    self.activeCheckBox.setToolTip("Activate recording")
    fileLayout.addRow("Recording:", self.activeCheckBox)

    self.fileDialogBoxButton.connect('clicked(bool)', self.openDialogBox)
    self.fileLineEdit.editingFinished.connect(self.onFilePathEntered)
    self.activeCheckBox.connect('clicked(bool)', self.onActive)
    
    #--------------------------------------------------
    # Point recording
    #
    pointGroupBox = ctk.ctkCollapsibleGroupBox()
    pointGroupBox.title = "Point Recording"
    pointGroupBox.collapsed = False
    
    layout.addWidget(pointGroupBox)
    pointLayout = qt.QFormLayout(pointGroupBox)

    self.catheterComboBox = QComboBoxCatheter()
    self.catheterComboBox.setCatheterCollection(self.catheters)
    self.catheterComboBox.currentIndexChanged.connect(self.onCatheterSelected)
    pointLayout.addRow("Catheter: ", self.catheterComboBox)

    #
    # Coil seleciton check boxes
    #
    self.nChannel = 8
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
    self.addSceneObservers()
    
    
  #--------------------------------------------------
  # GUI Slots

  def openDialogBox(self):
    
    dlg = qt.QFileDialog()
    dlg.setFileMode(qt.QFileDialog.AnyFile)
    dlg.setNameFilter("TSV files (*.tsv)")
    dlg.setAcceptMode(qt.QFileDialog.AcceptOpen)
    
    if dlg.exec_():
      filename = dlg.selectedFiles()[0]
      print(filename)

      self.fileLineEdit.text = filename

      
  def onFilePathEntered(self):
    pass

  
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

    self.catheter = self.catheterComboBox.getCurrentCatheter()
    
    if self.catheter == None:
      self.enableCoilSelection(False)
    else:
      self.enableCoilSelection(True)
    

    
  def onCollectPoints(self):

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
    
    
  #--------------------------------------------------
  # Start/stop recording

  def startRecording(self):

    if self.recfile and not self.recfile.closed:
      self.recfile.close()

    filepath =  self.fileLineEdit.text
    #if filepath == None or exists(filepath) == False:
    if filepath == None:
      
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Warning)
      msg.setText("Invalid file path.")
      #msg.setInformativeText("This is additional information")
      msg.setWindowTitle("Error")
      msg.setStandardButtons(QMessageBox.Ok)
      msg.exec_()
      
      return False

    self.findAndObserveNodes()
    
    try:
      self.recfile = open(filepath, 'w')
    except IOError:
      print("Could not open file: " + filepath)

    # Update GUI
    self.activeCheckBox.checked = 1
      

  def stopRecording(self):

    if self.recfile and not self.recfile.closed:
      self.recfile.close()

    self.removeNodeObservers()
    
    # Update GUI
    self.activeCheckBox.checked = 0

    
  #--------------------------------------------------
  # Find existing tracking/Egram nodes and setup observers

  def findAndObserveNodes(self):

    classList = ['vtkMRMLIGTLTrackingDataBundleNode', 'vtkMRMLTextNode']

    for c in classList:
    
      nodes = slicer.util.getNodesByClass(c)
      for node in nodes:
        self.observeNode(node)

        
  def removeNodeObservers(self):
    
    classList = ['vtkMRMLIGTLTrackingDataBundleNode', 'vtkMRMLTextNode']

    for c in classList:
    
      nodes = slicer.util.getNodesByClass(c)
      for node in nodes:
        self.removeNodeObserver(node)

        
  def observeNode(self, node):

    if node == None:
      return False
    
    if node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode': # Tracking data
      tdnode = node

      print('Recording: Adding transform nodes..')
        
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        
        # Get the first node
        firstNode = tdnode.GetTransformNode(0)
        self.eventTags[tdnode.GetID()] = firstNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onTrackingNodeModifiedEvent)
        firstNode.SetAttribute('MRTracking.recording.parent', tdnode.GetID())
          
    elif node.GetClassName() == 'vtkMRMLTextNode': # Egram data
      textnode = node
      
      print('Recording: Adding egram node..')
      self.eventTags[textnode.GetID()] = textnode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onEgramNodeModifiedEvent)

    return True

  
  def removeNodeObserver(self, node):
    
    if node == None:
      return False
    
    nodeID = node.GetID()

    if node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode': # Tracking data
      
      if node.GetNumberOfTransformNodes() > 0:
        
        # Get the first node
        firstNode = tdnode.GetTransformNode(0)
        tag = self.eventTags[nodeID]
        if tag:
          firstNode.RemoveObserver(tag)
          
        del self.eventTags[nodeID]
          
      elif node.GetClassName() == 'vtkMRMLTextNode': # Egram data
       
        tag = self.eventTags[nodeID]
        if tag:
          node.RemoveObserver(tag)
          
        del self.eventTags[nodeID]


  #--------------------------------------------------
  # Observers

  def addSceneObservers(self):
    slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAddedEvent)
    slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAboutToBeRemovedEvent, self.onNodeRemovedEvent)    
    slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndImportEvent, self.onSceneImportedEvent)
    slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.onSceneClosedEvent)


  @vtk.calldata_type(vtk.VTK_OBJECT)    
  def onNodeAddedEvent(self, caller, eventId, callData):

    if self.recfile == None:
      return

    self.observeNode(callData)
        

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeRemovedEvent(self, caller, event, obj=None):
    
    #self.removeNodeObserver(caller)
    pass
    

  
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onSceneImportedEvent(self, caller, eventId, callData):
    pass

  
  @vtk.calldata_type(vtk.VTK_OBJECT)  
  def onSceneClosedEvent(self, caller, eventId, callData):
    
    self.stopRecording()


  @vtk.calldata_type(vtk.VTK_OBJECT)  
  def onTrackingNodeModifiedEvent(self, caller, event):

    #
    # Format:
    #    TYPE NAME TIMESTAMP X_0 Y_0 Z_0 X_1 Y_1 Z_1 ... X_(N-1) Y_(N-1) Z_(N-1)
    #    

    parentID = str(caller.GetAttribute('MRTracking.recording.parent'))
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)
    
    if tdnode == None:
      return

    if tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      
      nTrans = tdnode.GetNumberOfTransformNodes()
      currentTime = time.time()
      outStr = 'TDATA\t'
      
      if nTrans > 0:
        # Check if the node has been updated
        tnode = tdnode.GetTransformNode(0)
        mTime = tnode.GetTransformToWorldMTime()

        nodeID = tnode.GetID()
        if not(nodeID in self.lastMTime):
          self.lastMTime[nodeID] = 0
          
        if mTime > self.lastMTime[nodeID]:
          self.lastMTime[nodeID] = mTime
          outStr = outStr + tdnode.GetName() + '\t' + str(currentTime) + '\t'
          
          for i in range(nTrans):
            tnode = tdnode.GetTransformNode(i)
            trans = tnode.GetTransformToParent()
            v = trans.GetPosition()
            outStr = outStr + '\t' + str(v[0]) + '\t' + str(v[1]) + '\t' + str(v[2])

          outStr = outStr + '\n'
          self.recfile.write(outStr)

      
          
  @vtk.calldata_type(vtk.VTK_OBJECT)  
  def onEgramNodeModifiedEvent(self, caller, event):

    #
    # Format:
    #    TYPE NAME TIMESTAMP STRING
    #    

    if caller.GetClassName() != 'vtkMRMLTextNode':
      return

    node = caller
    currentTime = time.time()    
    mTime = node.GetMTime()

    nodeID = node.GetID()
    if not(nodeID in self.lastMTime):
      self.lastMTime[nodeID] = 0

    if mTime > self.lastMTime[nodeID]:
      self.lastMTime[nodeID] = mTime
      string = caller.GetText()
      string = string.replace('\n', '\t')
      outStr = 'STRING\t' + node.GetName() + '\t' + str(currentTime) + '\t' + string + '\n'
      self.recfile.write(outStr)
    


    
