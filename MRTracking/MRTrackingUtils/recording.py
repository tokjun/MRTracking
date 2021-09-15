import ctk
import qt
import slicer
import vtk
from os.path import exists
from MRTrackingUtils.panelbase import *

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingRecording(MRTrackingPanelBase):

  def __init__(self, label="Recording"):
    super(MRTrackingRecording, self).__init__(label)

    self.recfile = None
    
    self.reslice = [False, False, False]
    self.resliceDriverLogic= slicer.modules.volumereslicedriver.logic()

    self.resliceCath = 0

    
  def buildMainPanel(self, frame):
    
    layout = qt.QFormLayout(frame)
    fileBoxLayout = qt.QHBoxLayout()

    self.fileLineEdit = qt.QLineEdit()
    self.fileDialogBoxButton = qt.QPushButton()
    self.fileDialogBoxButton.setCheckable(False)
    self.fileDialogBoxButton.text = '...'
    self.fileDialogBoxButton.setToolTip("Open file dialog box.")
    
    fileBoxLayout.addWidget(self.fileLineEdit)
    fileBoxLayout.addWidget(self.fileDialogBoxButton)
    layout.addRow("File Path:", fileBoxLayout)
    
    self.activeCheckBox = qt.QCheckBox()
    self.activeCheckBox.checked = 0
    self.activeCheckBox.enabled = 0
    self.activeCheckBox.setToolTip("Activate recording")
    layout.addRow("Recording:", activeBoxLayout)

    self.fileDialogBoxButton.connect('clicked(bool)', self.openDialogBox)
    self.fileLineEdit.editingFinished.connect(self.onFilePathEntered)
    self.activeCheckBox.connect('clicked(bool)', self.onActive)
    
    ## TODO: Should it be called from the module class, either Widget or Logic?
    self.addObservers()
    
    
  #--------------------------------------------------
  # GUI Slots

  def openDialogBox(self):
    
    dlg = qt.QFileDialog()
    dlg.setFileMode(qt.QFileDialog.AnyFile)
    dlg.setNameFilter("CSV files (*.csv)")
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
    
    #try:
    #  self.recfile = open(filepath, 'w')
      

      
  #--------------------------------------------------
  # Find existing tracking/Egram nodes and setup observers

  def findAndObserveNodes(self):

    classList = ['vtkMRMLIGTLTrackingDataBundleNode', 'vtkMRMLTextNode']

    for c in classList:
    
      nodes = slicer.util.getNodesByClass(c)
      for node in nodes:
        self.observeNode(node)
    
  def observeNode(self, node):

    if node == None:
      return False
    
    if node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode': # Tracking data
      tdnode = caller

      if tdnode:
        print('Recording: Adding transform nodes..')
        
        # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
        if tdnode.GetNumberOfTransformNodes() > 0:

          # Get the first node
          firstNode = tdnode.GetTransformNode(0)
          self.eventTags[tdnode.GetID()] = firstNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onTrackingNodeModifiedEvent)
          firstNode.SetAttribute('MRTracking.recording.parent', tdnode.GetID())
          
    elif node.GetClassName() == 'vtkMRMLTextNode': # Egram data
      textnode = caller
      
      if textnode:
        print('Recording: Adding egram node..')
        self.eventTags[textnode.GetID()] = textnode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onEgramNodeModifiedEvent)

    return True
  
  
  #--------------------------------------------------
  # Observers

  def addObservers(self):
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAddedEvent)
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeAboutToBeRemovedEvent, self.onNodeRemovedEvent)    
    self.scene.AddObserver(slicer.vtkMRMLScene.EndImportEvent, self.onSceneImportedEvent)
    self.scene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.onSceneClosedEvent)


  @vtk.calldata_type(vtk.VTK_OBJECT)    
  def onNodeAddedEvent(self, caller, eventId, callData):

    if self.recfile == None:
      return

    self.observeNode(callData)
        

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeRemovedEvent(self, caller, event, obj=None):
    pass

  
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onSceneImportedEvent(self, caller, eventId, callData):
    pass

  @vtk.calldata_type(vtk.VTK_OBJECT)  
  def onSceneClosedEvent(self, caller, eventId, callData):
    pass


  @vtk.calldata_type(vtk.VTK_OBJECT)  
  def onIncomingNodeModifiedEvent(self, caller, event):
    pass


  @vtk.calldata_type(vtk.VTK_OBJECT)  
  def onTrackingNodeModifiedEvent(self, caller, event):

    #
    # Format: 
    #    TimeStamp,BundleName,NumberOfCoils,X_0,Y_0,Z_0,X_1,Y_1,Z_1, ..., X_(N-1),Y_(N-1),Z_(N-1)
    #    

    parentID = str(caller.GetAttribute('MRTracking.recording.parent'))
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)

    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      
      nTrans = tdnode.GetNumberOfTransformNodes()
      currentTime = time.time()
      outStr = ''
      
      if nCoils > 0:
        # Check if the node has been updated
        tnode = tdnode.GetTransformNode(0)
        mTime = tnode.GetTransformToWorldMTime()
        
        if mTime > self.lastMTime[tnode.GetID()]:
          self.lastMTime[tnode.GetID()] = mTime
          outStr = outStr + str(currentTime) + ',' + tnode.GetName() + ',' + 'nCoils'
          
          for i in range(nCoils):
            tnode = tdnode.GetTransformNode(i)
            trans = tnode.GetTransformToParent()
            v = trans.GetPosition()
            outStr = outStr + ',' + str(v[0]) + ',' + str(v[1]) + ',' + str(v[2])
        
          self.fout
