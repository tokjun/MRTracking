import ctk
import qt
import slicer
import vtk
from os.path import exists
from MRTrackingUtils.panelbase import *
from MRTrackingUtils.qpointrecordingframe  import *

#------------------------------------------------------------
#
# MRTrackingRecording
#

#
# This recording class records received catheter tracking and Egram data and save them in an output file.
# The class detects every MRML node that are used to dreceive data from catheter tracking systems
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
    pointLayout = qt.QVBoxLayout(pointGroupBox)
    self.precording = QPointRecordingFrame(catheters=self.catheters)
    pointLayout.addWidget(self.precording)
    
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
    


    
