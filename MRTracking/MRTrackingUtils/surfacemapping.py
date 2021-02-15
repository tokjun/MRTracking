import ctk
import qt
import slicer

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingSurfaceMapping():

  def __init__(self, label="SurfaceMapping"):

    self.label = label
    self.mrTrackingLogic = None
    self.nCath = 2
    self.cath = 0
    self.currentTrackingDataNode = None

  def buildGUI(self, parent):

    mappingLayout = qt.QFormLayout(parent)
    
    # Tracking node selector
    self.mappingTrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.mappingTrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.mappingTrackingDataSelector.selectNodeUponCreation = True
    self.mappingTrackingDataSelector.addEnabled = True
    self.mappingTrackingDataSelector.removeEnabled = False
    self.mappingTrackingDataSelector.noneEnabled = False
    self.mappingTrackingDataSelector.showHidden = True
    self.mappingTrackingDataSelector.showChildNodeTypes = False
    self.mappingTrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.mappingTrackingDataSelector.setToolTip( "Tracking Data for Reslicing" )
    mappingLayout.addRow("Tracking Data: ", self.mappingTrackingDataSelector)

    self.cathRadioButton = [None] * self.nCath
    self.cathBoxLayout = qt.QHBoxLayout()
    self.cathGroup = qt.QButtonGroup()
    for cath in range(self.nCath):
      self.cathRadioButton[cath] = qt.QRadioButton("Cath %d" % cath)
      if cath == self.cath:
        self.cathRadioButton[cath].checked = 0
      self.cathBoxLayout.addWidget(self.cathRadioButton[cath])
      self.cathGroup.addButton(self.cathRadioButton[cath])

    self.egramRecordPointsSelector = slicer.qMRMLNodeComboBox()
    self.egramRecordPointsSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.egramRecordPointsSelector.selectNodeUponCreation = True
    self.egramRecordPointsSelector.addEnabled = True
    self.egramRecordPointsSelector.removeEnabled = False
    self.egramRecordPointsSelector.noneEnabled = True
    self.egramRecordPointsSelector.showHidden = True
    self.egramRecordPointsSelector.showChildNodeTypes = False
    self.egramRecordPointsSelector.setMRMLScene( slicer.mrmlScene )
    self.egramRecordPointsSelector.setToolTip( "Fiducials for recording Egram data" )
    mappingLayout.addRow("Points: ", self.egramRecordPointsSelector)

    self.modelSelector = slicer.qMRMLNodeComboBox()
    self.modelSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.modelSelector.selectNodeUponCreation = True
    self.modelSelector.addEnabled = True
    self.modelSelector.removeEnabled = True
    self.modelSelector.noneEnabled = True
    self.modelSelector.showHidden = True
    self.modelSelector.showChildNodeTypes = False
    self.modelSelector.setMRMLScene( slicer.mrmlScene )
    self.modelSelector.setToolTip( "Surface model node" )
    mappingLayout.addRow("Model: ", self.modelSelector)

    # Minimum interval between two consective points
    self.pointRecordingDistanceSliderWidget = ctk.ctkSliderWidget()
    self.pointRecordingDistanceSliderWidget.singleStep = 0.1
    self.pointRecordingDistanceSliderWidget.minimum = 0.0
    self.pointRecordingDistanceSliderWidget.maximum = 20.0
    self.pointRecordingDistanceSliderWidget.value = 0.0
    #self.minIntervalSliderWidget.setToolTip("")

    mappingLayout.addRow("Min. Distance: ",  self.pointRecordingDistanceSliderWidget)

    activeBoxLayout = qt.QHBoxLayout()
    self.activeGroup = qt.QButtonGroup()
    self.activeOnRadioButton = qt.QRadioButton("ON")
    self.activeOffRadioButton = qt.QRadioButton("Off")
    self.activeOffRadioButton.checked = 1
    activeBoxLayout.addWidget(self.activeOnRadioButton)
    self.activeGroup.addButton(self.activeOnRadioButton)
    activeBoxLayout.addWidget(self.activeOffRadioButton)
    self.activeGroup.addButton(self.activeOffRadioButton)

    mappingLayout.addRow("Active: ", activeBoxLayout)

    self.resetPointButton = qt.QPushButton()
    self.resetPointButton.setCheckable(False)
    self.resetPointButton.text = 'Erase Points'
    self.resetPointButton.setToolTip("Erase all the points recorded for surface mapping.")

    mappingLayout.addRow(" ",  self.resetPointButton)

    self.mappingTrackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onMappingTrackingDataSelected)
    self.egramRecordPointsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onEgramRecordPointsSelected)
    self.modelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onModelSelected)
    self.pointRecordingDistanceSliderWidget.connect("valueChanged(double)", self.pointRecordingDistanceChanged)
    self.resetPointButton.connect('clicked(bool)', self.onResetPointRecording)
    
    for cath in range(self.nCath):    
      self.cathRadioButton[cath].connect('clicked(bool)', self.onSelectCath)

    self.activeOnRadioButton.connect('clicked(bool)', self.onActive)
    self.activeOffRadioButton.connect('clicked(bool)', self.onActive)

  def setMRTrackingLogic(self, t):
    self.mrTrackingLogic = t

    
  #--------------------------------------------------
  # GUI Slots

  def getTrackingData(self):
    print("getTrackingData()")
    if self.mrTrackingLogic == None:
      return None
    tdnode = self.currentTrackingDataNode
    if tdnode == None:
      return None
    td = self.mrTrackingLogic.TrackingData[tdnode.GetID()]
    return td

  def onMappingTrackingDataSelected(self):
    td = self.getTrackingData()
    if td:
      td.pointRecording[self.cath] = False      
      self.activeOffRadioButton.checked = 1
    self.currentTrackingDataNode = self.mappingTrackingDataSelector.currentNode()
  
  def onEgramRecordPointsSelected(self):
    td = self.getTrackingData()
    if td == None:
      return
    fnode = self.egramRecordPointsSelector.currentNode()
    if fnode:
      td.pointRecordingMarkupsNode[self.cath] = fnode
      fdnode = fnode.GetDisplayNode()
      if fdnode == None:
        fdnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialDisplayNode')
        slicer.mrmlScene.AddNode(fdnode)
        fnode.SetAndObserveDisplayNodeID(fdnode.GetID())
      if fnode:
        fdnode.SetTextScale(0.0)  # Hide the label

  def onModelSelected(self):
    mnode = self.modelSelector.currentNode()
    if mnode:
      dnode = mnode.GetDisplayNode()
      if dnode == None:
        dnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelDisplayNode')
        slicer.mrmlScene.AddNode(dnode)
        mnode.SetAndObserveDisplayNodeID(dnode.GetID())
      if dnode:
        dnode.SetVisibility(1)
        dnode.SetOpacity(0.5)
        
  def pointRecordingDistanceChanged(self):
    d = self.pointRecordingDistanceSliderWidget.value
    td = self.getTrackingData()    
    if td == None:
      return
    td.pointRecordingDistance[self.cath] = d

  def onResetPointRecording(self):
    td = self.getTrackingData()
    markupsNode = td.pointRecordingMarkupsNode[self.cath]
    if markupsNode:
      markupsNode.RemoveAllControlPoints()
  
  def onSelectCath(self):
    for cath in range(self.nCath):
      if self.cathRadioButton[cath].checked:
        self.cath = cath

  def onActive(self):
    td = self.getTrackingData()
    if td == None:
      return
    if self.activeOnRadioButton.checked:
      # Add observer
      fnode = td.pointRecordingMarkupsNode[self.cath]
      if fnode:
        tag = fnode.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.controlPointsUpdated, 2)
        fnode.SetAttribute('SurfaceMapping.ObserverTag', str(tag))
      td.pointRecording[self.cath] = True
      
    else:
      td.pointRecording[self.cath] = False
      fnode = td.pointRecordingMarkupsNode[self.cath]
      if fnode:
        tag = fnode.GetAttribute('SurfaceMapping.ObserverTag')
        if tag != None:
          fnode.RemoveObserver(int(tag))
          fnode.SetAttribute('SurfaceMapping.ObserverTag', None)

  def controlPointsUpdated(self,caller,event):
    td = self.getTrackingData()
    # Update the surface model
    fnode = td.pointRecordingMarkupsNode[self.cath]
    mnode = self.modelSelector.currentNode()
    mtmlogic = slicer.modules.markupstomodel.logic()
    
    if (fnode != None) and (mnode != None) and (mtmlogic != None):
      mtmlogic.UpdateClosedSurfaceModel(fnode, mnode)
        
