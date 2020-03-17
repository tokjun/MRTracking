import ctk
import qt
import slicer
import functools

#------------------------------------------------------------
#
# MRTrackingFiducialRegistration class
#

class MRTrackingFiducialRegistration():

  def __init__(self, label="Registration"):

    self.label = label
    self.fiducialsVisible = False
    self.fromFiducialsNode = None
    self.toFiducialsNode = None
    self.registrationTransformNode = None
    
  def buildGUI(self, parent):

    registrationLayout = qt.QFormLayout(parent)

    self.fromTrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.fromTrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.fromTrackingDataSelector.selectNodeUponCreation = True
    self.fromTrackingDataSelector.addEnabled = True
    self.fromTrackingDataSelector.removeEnabled = False
    self.fromTrackingDataSelector.noneEnabled = False
    self.fromTrackingDataSelector.showHidden = True
    self.fromTrackingDataSelector.showChildNodeTypes = False
    self.fromTrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.fromTrackingDataSelector.setToolTip( "Tracking Data (From)" )
    registrationLayout.addRow("TrackingData (From): ", self.fromTrackingDataSelector)

    self.toTrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.toTrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.toTrackingDataSelector.selectNodeUponCreation = True
    self.toTrackingDataSelector.addEnabled = True
    self.toTrackingDataSelector.removeEnabled = False
    self.toTrackingDataSelector.noneEnabled = False
    self.toTrackingDataSelector.showHidden = True
    self.toTrackingDataSelector.showChildNodeTypes = False
    self.toTrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.toTrackingDataSelector.setToolTip( "Tracking data (To)")
    registrationLayout.addRow("TrackingData (To): ", self.toTrackingDataSelector)

    pointBoxLayout = qt.QHBoxLayout()
    self.pointGroup = qt.QButtonGroup()

    self.useTipRadioButton = qt.QRadioButton("Tip")
    self.useAllRadioButton = qt.QRadioButton("All ")
    self.useTipRadioButton.checked = 1
    pointBoxLayout.addWidget(self.useTipRadioButton)
    self.pointGroup.addButton(self.useTipRadioButton)
    pointBoxLayout.addWidget(self.useAllRadioButton)
    self.pointGroup.addButton(self.useAllRadioButton)

    registrationLayout.addRow("Points: ", pointBoxLayout)

    #
    # Fiducial points visibility
    #
    
    visibilityBoxLayout = qt.QHBoxLayout()
    self.visibilityGroup = qt.QButtonGroup()
    self.visibilityOnRadioButton = qt.QRadioButton("ON")
    self.visibilityOffRadioButton = qt.QRadioButton("Off")
    self.visibilityOnRadioButton.checked = 1
    visibilityBoxLayout.addWidget(self.visibilityOnRadioButton)
    self.visibilityGroup.addButton(self.visibilityOnRadioButton)
    visibilityBoxLayout.addWidget(self.visibilityOffRadioButton)
    self.visibilityGroup.addButton(self.visibilityOffRadioButton)

    registrationLayout.addRow("Visibility: ", visibilityBoxLayout)

    #
    # Collect/Clear button
    #
    
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
    
    registrationLayout.addRow("", buttonBoxLayout)

    #
    # Registration button
    #
    
    #runBoxLayout = qt.QHBoxLayout()    
    self.runButton = qt.QPushButton()
    self.runButton.setCheckable(False)
    self.runButton.text = 'Run Registration'
    self.runButton.setToolTip("Run fiducial registration.")
    #buttonBoxLayout.addWidget(self.runButton)
    registrationLayout.addRow("", self.runButton)

    #
    # Connect signals and slots
    #
    self.fromTrackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataFromSelected)
    self.toTrackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataToSelected)
    self.collectButton.connect(qt.SIGNAL("clicked()"), self.onCollectPoints)
    self.clearButton.connect(qt.SIGNAL("clicked()"), self.onClearPoints)
    self.runButton.connect(qt.SIGNAL("clicked()"), self.onRunRegistration)
    self.visibilityOnRadioButton.connect("clicked(bool)", self.onVisibilityChanged)
    self.visibilityOffRadioButton.connect("clicked(bool)", self.onVisibilityChanged)


  def onTrackingDataFromSelected(self):

    fromTrackingNode = self.fromTrackingDataSelector.currentNode()

    if fromTrackingNode == None:
      self.fromFiducialsNode = None
      return
    
    # Get/create fiducials node for "To" points
    fromFiducialsNodeID = fromTrackingNode.GetAttribute('MRTracking.RegistrationPointsFrom')
    if fromFiducialsNodeID:
      self.fromFiducialsNode = slicer.mrmlScene.GetNodeByID(fromFiducialsNodeID)
    else:
      self.fromFiducialsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
      self.fromFiducialsNode.SetName('RegistrationPointsFrom')
      fromTrackingNode.SetAttribute('MRTracking.RegistrationPointsFrom', self.fromFiducialsNode.GetID())

    dnode = self.fromFiducialsNode.GetDisplayNode()
    dnode.SetVisibility(self.fiducialsVisible)
    
  def onTrackingDataToSelected(self):

    toTrackingNode = self.toTrackingDataSelector.currentNode()
    
    if toTrackingNode == None:
      self.toFiducialsNode = None
      return

    # Get/create fiducials node for "From" points
    toFiducialsNodeID = toTrackingNode.GetAttribute('MRTracking.RegistrationPointsTo')
    if toFiducialsNodeID:
      self.toFiducialsNode = slicer.mrmlScene.GetNodeByID(toFiducialsNodeID)
    else:
      self.toFiducialsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
      self.toFiducialsNode.SetName('RegistrationPointsTo')
      toTrackingNode.SetAttribute('MRTracking.RegistrationPointsTo', self.toFiducialsNode.GetID())
      
    dnode = self.toFiducialsNode.GetDisplayNode()
    dnode.SetVisibility(self.fiducialsVisible)

    
  def onCollectPoints(self):

    print ("onCollectPoints(self)")
    fromTrackingNode = self.fromTrackingDataSelector.currentNode()
    toTrackingNode = self.toTrackingDataSelector.currentNode()

    # If either tracking node is not specified, show an error message and exist this function.
    if fromTrackingNode == None or toTrackingNode == None:
      msgBox = QMessageBox()
      msgBox.setIcon(QMessageBox.Information)
      msgBox.setText("Tracking data are not spcified.")
      msgBox.setWindowTitle("Error")
      msgBox.setStandardButtons(QMessageBox.Ok)
      msgBox.buttonClicked.connect(msgButtonClick)
      returnValue = msgBox.exec()
      return

    if self.fromFiducialsNode:
      dnode = self.fromFiducialsNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)
    else:
      print("Error: Fiducials Node for 'From' is not available.")
      return
        
    if self.toFiducialsNode:
      dnode = self.toFiducialsNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)
    else:
      print("Error: Fiducials Node for 'To' is not available.")
      return
    
    #
    # In the following process, we assume that the two tracking data nodes (i.e. catheters) have
    # the coils at the corresponding points. We will revise it in the future so that registration
    # points can be between the actual coils.
    #
      
    nCoilsFrom = fromTrackingNode.GetNumberOfTransformNodes()
    nCoilsTo = toTrackingNode.GetNumberOfTransformNodes()

    nCoils = 0
    if nCoilsFrom > nCoilsTo:
      nCoils = nCoilsTo
    else:
      nCoils = nCoilsFrom
      
    for i in range(nCoils):
      transNodeFrom = fromTrackingNode.GetTransformNode(i)
      transFrom = transNodeFrom.GetTransformToParent()
      posFrom = transFrom.GetPosition()
      self.fromFiducialsNode.AddFiducial(posFrom[0], posFrom[1], posFrom[2])
      print('Add From (%d, %d, %d)' % (posFrom[0], posFrom[1], posFrom[2]))
      
      transNodeTo   = toTrackingNode.GetTransformNode(i)
      transTo   = transNodeTo.GetTransformToParent()
      posTo   = transTo.GetPosition()
      self.toFiducialsNode.AddFiducial(posTo[0], posTo[1], posTo[2])
      print('Add To (%d, %d, %d)' % (posTo[0], posTo[1], posTo[2]))

      
  def onClearPoints(self):
    
    if self.fromFiducialsNode:
      self.fromFiducialsNode.RemoveAllMarkups()
      
    if self.toFiducialsNode:
      self.toFiducialsNode.RemoveAllMarkups()

      
  def onRunRegistration(self):
    
    if self.fromFiducialsNode == None or self.toFiducialsNode == None:
      print('Error: no fiducial point is available.')

    # Create linear transform node to store the registration result
    if self.registrationTransformNode == None:
      self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode")
      self.registrationTransformNode.SetName("RegistrationTransform")

    frCLI = slicer.modules.fiducialregistration
    frParameters = {}
    frParameters["fixedLandmarks"]  = self.toFiducialsNode.GetID()
    frParameters["movingLandmarks"] = self.fromFiducialsNode.GetID()
    frParameters["saveTransform"]   = self.registrationTransformNode.GetID()
    
    frCLINode = slicer.cli.runSync(frCLI, None, frParameters)

    

  def onVisibilityChanged(self):

    if self.visibilityOnRadioButton.checked == True:
      self.fiducialsVisible = True
    else:
      self.fiducialsVisible = False

    if self.fromFiducialsNode:
        dnode = self.fromFiducialsNode.GetDisplayNode()
        dnode.SetVisibility(self.fiducialsVisible)
        
    if self.toFiducialsNode:
        dnode = self.toFiducialsNode.GetDisplayNode()
        dnode.SetVisibility(self.fiducialsVisible)

          
