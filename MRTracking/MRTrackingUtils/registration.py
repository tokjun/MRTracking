import ctk
import qt
import slicer
import vtk
import functools
import time
import numpy

#------------------------------------------------------------
#
# MRTrackingFiducialRegistration class
#

class MRTrackingFiducialRegistration():

  def __init__(self, label="Registration"):

    self.label = label
    self.fiducialsVisible = False
    self.trackingData = None

    # Circular buffers for registration poitns
    self.fromFiducialsNode = None
    self.toFiducialsNode = None
    self.fromFiducialsTimeStamp = []
    self.toFiducialsTimeStamp = []

    # Transformation
    self.registrationTransformNode = None
    self.registrationTransform = None
    self.applyTransform = None # Specifiy the data node under the transform -- TODO: Will be obsolete. Use 'transformedCatheter'
    self.transformedCatheter = None # Specifiy a Catheter class instance to which the registration transform is applied. (Replaces self.applyTransform)
    
    self.mrTrackingLogic = None
    self.sizeCircularBuffer = 24 # 8 time points x 3 (x, y, z) = 24
    self.pCircularBuffer = 0

    ## For automatic registration update
    self.autoUpdate = False
    self.prevNCoilsTo = 0
    self.prevNCoilsFrom = 0
    self.prevCollectionTime = 0.0

    self.minNumFiducials = 10
    self.maxNumFiducials = 100

    self.minInterval = 1.0           # seconds
    self.maxTimeDifference = 0.1     # seconds
    
    
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

    # #
    # # Fiducial points used (either "tip only" or "all"
    # #
    # 
    # pointBoxLayout = qt.QHBoxLayout()
    # self.pointGroup = qt.QButtonGroup()
    # 
    # self.useTipRadioButton = qt.QRadioButton("Tip")
    # self.useAllRadioButton = qt.QRadioButton("All ")
    # self.useAllRadioButton.checked = 1
    # pointBoxLayout.addWidget(self.useTipRadioButton)
    # self.pointGroup.addButton(self.useTipRadioButton)
    # pointBoxLayout.addWidget(self.useAllRadioButton)
    # self.pointGroup.addButton(self.useAllRadioButton)
    # 
    # registrationLayout.addRow("Points: ", pointBoxLayout)
    #
    
    #
    # Fiducial points visibility
    #
    
    visibilityBoxLayout = qt.QHBoxLayout()
    self.visibilityGroup = qt.QButtonGroup()
    self.visibilityOnRadioButton = qt.QRadioButton("ON")
    self.visibilityOffRadioButton = qt.QRadioButton("Off")
    self.visibilityOffRadioButton.checked = 1
    visibilityBoxLayout.addWidget(self.visibilityOnRadioButton)
    self.visibilityGroup.addButton(self.visibilityOnRadioButton)
    visibilityBoxLayout.addWidget(self.visibilityOffRadioButton)
    self.visibilityGroup.addButton(self.visibilityOffRadioButton)

    registrationLayout.addRow("Visibility: ", visibilityBoxLayout)

    #
    # Transform Type
    #
    
    transTypeBoxLayout = qt.QHBoxLayout()
    self.transTypeGroup = qt.QButtonGroup()
    self.rigidTypeRadioButton = qt.QRadioButton("Rigid")
    self.affineTypeRadioButton = qt.QRadioButton("Affine")
    self.splineTypeRadioButton = qt.QRadioButton("Thin Plate Spline")
    self.rigidTypeRadioButton.checked = 1
    transTypeBoxLayout.addWidget(self.rigidTypeRadioButton)
    self.transTypeGroup.addButton(self.rigidTypeRadioButton)
    transTypeBoxLayout.addWidget(self.affineTypeRadioButton)
    self.transTypeGroup.addButton(self.affineTypeRadioButton)
    transTypeBoxLayout.addWidget(self.splineTypeRadioButton)
    self.transTypeGroup.addButton(self.splineTypeRadioButton)

    registrationLayout.addRow("Transform Type: ", transTypeBoxLayout)

    #
    # Automatic Update
    #
    
    autoUpdateBoxLayout = qt.QHBoxLayout()
    self.autoUpdateGroup = qt.QButtonGroup()
    self.autoUpdateOnRadioButton = qt.QRadioButton("ON")
    self.autoUpdateOffRadioButton = qt.QRadioButton("OFF")
    self.autoUpdateOffRadioButton.checked = 1
    autoUpdateBoxLayout.addWidget(self.autoUpdateOnRadioButton)
    self.autoUpdateGroup.addButton(self.autoUpdateOnRadioButton)
    autoUpdateBoxLayout.addWidget(self.autoUpdateOffRadioButton)
    self.autoUpdateGroup.addButton(self.autoUpdateOffRadioButton)

    registrationLayout.addRow("Automatic Update: ", autoUpdateBoxLayout)

    #
    # Parameters for point selections
    #

    # Maximum time difference between the corresponding points from the two trackers.
    
    self.maxTimeDifferenceSliderWidget = ctk.ctkSliderWidget()
    self.maxTimeDifferenceSliderWidget.singleStep = 10.0
    self.maxTimeDifferenceSliderWidget.minimum = 0.0
    self.maxTimeDifferenceSliderWidget.maximum = 10000.0
    self.maxTimeDifferenceSliderWidget.value = self.maxTimeDifference * 1000.0
    #self.maxTimeDifferenceSliderWidget.setToolTip("")
    registrationLayout.addRow("Max. Time Diff (ms): ",  self.maxTimeDifferenceSliderWidget)

    # Minimum interval between two consecutive registrations
    self.minIntervalSliderWidget = ctk.ctkSliderWidget()
    self.minIntervalSliderWidget.singleStep = 10.0
    self.minIntervalSliderWidget.minimum = 0.0
    self.minIntervalSliderWidget.maximum = 10000.0
    self.minIntervalSliderWidget.value = self.minInterval * 1000.0
    #self.minIntervalSliderWidget.setToolTip("")
    registrationLayout.addRow("Min. Registration Interval (ms): ",  self.minIntervalSliderWidget)

    # Minimum interval between two consecutive registrations
    self.pointExpirationSliderWidget = ctk.ctkSliderWidget()
    self.pointExpirationSliderWidget.singleStep = 10.0
    self.pointExpirationSliderWidget.minimum = 0.0
    self.pointExpirationSliderWidget.maximum = 10000.0
    self.pointExpirationSliderWidget.value = self.minInterval
    #self.minIntervalSliderWidget.setToolTip("")
    registrationLayout.addRow("Point Exp. (ms): ",  self.pointExpirationSliderWidget)

    
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
    # Apply transform
    #
    
    applyTransformBoxLayout = qt.QHBoxLayout()
    self.applyTransformGroup = qt.QButtonGroup()
    self.applyTransformOnRadioButton = qt.QRadioButton("ON")
    self.applyTransformOffRadioButton = qt.QRadioButton("Off")
    self.applyTransformOffRadioButton.checked = 1
    applyTransformBoxLayout.addWidget(self.applyTransformOnRadioButton)
    self.applyTransformGroup.addButton(self.applyTransformOnRadioButton)
    applyTransformBoxLayout.addWidget(self.applyTransformOffRadioButton)
    self.applyTransformGroup.addButton(self.applyTransformOffRadioButton)

    registrationLayout.addRow("Apply Transform: ", applyTransformBoxLayout)

    #
    # Fiducial Registration Error
    #
    self.freLineEdit = qt.QLineEdit()
    self.freLineEdit.text = '--'
    self.freLineEdit.readOnly = True
    self.freLineEdit.frame = True
    self.freLineEdit.styleSheet = "QLineEdit { background:transparent; }"
    
    registrationLayout.addRow("FRE (mm): ", self.freLineEdit)
    
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
    self.applyTransformOnRadioButton.connect("clicked(bool)", self.onApplyTransformChanged)
    self.applyTransformOffRadioButton.connect("clicked(bool)", self.onApplyTransformChanged)
    self.autoUpdateOnRadioButton.connect("clicked(bool)", self.onAutoUpdateChanged)
    self.autoUpdateOffRadioButton.connect("clicked(bool)", self.onAutoUpdateChanged)
    self.maxTimeDifferenceSliderWidget.connect("valueChanged(double)", self.onPointSelectionParametersChanged)
    self.minIntervalSliderWidget.connect("valueChanged(double)", self.onPointSelectionParametersChanged)
    self.pointExpirationSliderWidget.connect("valueChanged(double)", self.onPointSelectionParametersChanged)
    
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

    
  def onCollectPoints(self, auto=False):
    # Returns True if registration needs to be updated.

    fCollect = True # Flag to collect points
    
    # Check the current time 
    currentTime = time.time()
    
    if auto:
      fCollect = False # If auto=True, this function won't collect the points in default.

    #print ("onCollectPoints(self)")
    fromTrackingNode = self.fromTrackingDataSelector.currentNode()
    toTrackingNode = self.toTrackingDataSelector.currentNode()

    ## TODO: Assuming to use the first curve. 
    fromCurveNodeID = fromTrackingNode.GetAttribute('MRTracking.CurveNode0')
    toCurveNodeID = toTrackingNode.GetAttribute('MRTracking.CurveNode0')

    fromCurveNode = slicer.mrmlScene.GetNodeByID(fromCurveNodeID)
    toCurveNode = slicer.mrmlScene.GetNodeByID(toCurveNodeID)

    # If either tracking node is not specified, show an error message and exist this function.
    #if fromTrackingNode == None or toTrackingNode == None:
    if fromCurveNode == None or toCurveNode == None:
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

    ## Get TrackingData 
    tdFrom = self.trackingData[fromTrackingNode.GetID()]
    tdTo   = self.trackingData[toTrackingNode.GetID()]
    coilPosFrom = tdFrom.coilPositions[0]
    coilPosTo = tdTo.coilPositions[0]
    
    #
    #              Tip     s[0]     s[1]       s[2]       s[3] ...
    #   Tracking 0 *-------x--------x----------x----------x------------------
    #
    #              Tip        t[0]      t[1]         t[2]       t[3] ...
    #   Tracking 1 *----------x---------x------------x----------x------------
    #
    #
    # where 's[]' and 't[]' are distance from the tip to each coil along the catheter.
    #
    # 1. Find the two closest coils for Tracking 0 (s[k] and s[k+1]) from each coil for Tracking 1 t[j]
    # 2. Calculate the distance ratio a/b = distance(s[k], t[j]) / distance(s[k], s[k+1])
    #
    #                     s[k]         s[k+1]    
    #   Tracking 0 ... ---x----------x----- ...
    #                     |          |
    #                     |   t[j]   |
    #   Tracking 1 ... -------x------------ ...
    #                     |   |      |
    #                     |<->|      |
    #                     | a        |
    #                     |          |
    #                     |<-------->|
    #                           b
    
    # 3. Calculate the location of t[j] in the Tracking 0 space by interpolation.
    #
    
    # Match the number of coils
    nCoilsFrom = fromTrackingNode.GetNumberOfTransformNodes()
    nCoilsTo = toTrackingNode.GetNumberOfTransformNodes()

    # Check if the number of coils has changed
    if self.prevNCoilsFrom != nCoilsFrom:
      fCollect = True
      self.prevNCoilsFrom = nCoilsFrom
      
    if self.prevNCoilsTo != nCoilsTo:
      fCollect = True
      self.prevNCoilsTo = nCoilsTo

    nCoils = 0
    if nCoilsFrom > nCoilsTo:
      nCoils = nCoilsTo
    else:
      nCoils = nCoilsFrom

    # If there is no coil, skip the following process.
    if nCoils == 0:
      return False

    #
    # TODO: Check if the numbers are orderd correctly in the coilPosFrom and coilPosTo arrays
    #

    s = None
    t = None
    curve0Node = None
    curve1Node = None
    if coilPosFrom[0] < coilPosTo[0]:
      s = coilPosFrom
      t = coilPosTo
      curve0Node = fromCurveNode
      curve1Node = toCurveNode
    else:
      s = coilPosTo
      t = coilPosFrom
      curve0Node = toCurveNode
      curve1Node = fromCurveNode

    # Check time stamp
    curve0Time = float(curve0Node.GetAttribute('MRTracking.lastTS'))
    curve1Time = float(curve1Node.GetAttribute('MRTracking.lastTS'))


    # Check if it is too early to perform new registration
    print('curve 0, curve 1, prevCollectionTime, interval = %f, %f, %f, %f' % (curve0Time, curve1Time, self.prevCollectionTime, self.minInterval))
    
    if ((curve0Time - self.prevCollectionTime) < self.minInterval) and ((curve1Time - self.prevCollectionTime) < self.minInterval):
      return False

    # Check if the acquisition time difference between the two curves are small enough
    if abs(curve0Time - curve1Time) > self.maxTimeDifference:
      return False
            
    self.prevCollectionTime = currentTime
                                                
    #adjPointIndex = [-1] * nCoils ## TODO: Should it have fixed length for speed?
    k = 0
    trans = vtk.vtkMatrix4x4()
    posFrom = [0.0] * 3
    posTo = [0.0] * 3

    invTransform = None
    if self.applyTransform and self.registrationTransform:
      invTransform = self.registrationTransform.GetInverse()
    
    for j in range(nCoils):

      print ("t[%d] = %f" % (j, t[j]))
      
      # 1. Find the two closest coils for Tracking 0 (s[k] and s[k+1]) from each coil for Tracking 1 t[j]
      
      while k < nCoils-1 and s[k+1] < t[j]:
        k = k + 1

      if k == nCoils-1:
        break

      # 2. Calculate the distance ratio a/(a+b) = distance(s[k], t[j]) / distance(s[k], s[k+1])
      a = t[j]-s[k]
      b = s[k+1]-s[k]

      # Get the point indices for s[k] and s[k+1] (control points)
      pindex0 = curve0Node.GetCurvePointIndexFromControlPointIndex(k)
      pindex1 = curve0Node.GetCurvePointIndexFromControlPointIndex(k+1)

      ## TODO: Make sure that pindex0 < pindex1

      # 3. Calculate the location of t[j] in the Tracking 0 space by interpolation.      
      # Calculate the curve length between the point s[k] and point s[k+1]
      clen = curve0Node.GetCurveLengthBetweenStartEndPointsWorld(pindex0, pindex1)
      
      pindexm =  curve0Node.GetCurvePointIndexAlongCurveWorld(pindex0, clen * a / b)

      curve0Node.GetCurvePointToWorldTransformAtPointIndex(pindexm, trans)
      posFrom[0] = trans.GetElement(0, 3)
      posFrom[1] = trans.GetElement(1, 3)
      posFrom[2] = trans.GetElement(2, 3)
      if self.applyTransform and invTransform:
        v = invTransform.TransformPoint(posFrom)
        posFrom[0] = v[0]
        posFrom[1] = v[1]
        posFrom[2] = v[2]
        
      
      # 3. Obtain the coordinates for t[j]
      pindex = curve1Node.GetCurvePointIndexFromControlPointIndex(j)
      curve1Node.GetCurvePointToWorldTransformAtPointIndex(pindex, trans)
      posTo[0] = trans.GetElement(0, 3)
      posTo[1] = trans.GetElement(1, 3)
      posTo[2] = trans.GetElement(2, 3)


      # 5. Record the coordinates
      nFrom = self.fromFiducialsNode.GetNumberOfFiducials()
      
      if nFrom > self.sizeCircularBuffer: # Overwrite a previous point.
        self.fromFiducialsNode.SetNthFiducialPosition(self.pCircularBuffer, posFrom[0], posFrom[1], posFrom[2])
        self.toFiducialsNode.SetNthFiducialPosition(self.pCircularBuffer, posTo[0], posTo[1], posTo[2])
        self.fromFiducialsTimeStamp[self.pCircularBuffer] = curve0Time
        self.toFiducialsTimeStamp[self.pCircularBuffer] = curve1Time
        self.pCircularBuffer = (self.pCircularBuffer + 1) % self.sizeCircularBuffer
      else: # Add a new point
        self.fromFiducialsNode.AddFiducial(posFrom[0], posFrom[1], posFrom[2])
        self.toFiducialsNode.AddFiducial(posTo[0], posTo[1], posTo[2])
        self.fromFiducialsTimeStamp.append(curve0Time)
        self.toFiducialsTimeStamp.append(curve1Time)

        
      print('Add From (%f, %f, %f)' % (posFrom[0], posFrom[1], posFrom[2]))
      print('Add To (%f, %f, %f)' % (posTo[0], posTo[1], posTo[2]))


    # Check if it is ready for new registration
    if self.fromFiducialsNode.GetNumberOfFiducials() >  self.minNumFiducials:
      return True
    
      
  def onClearPoints(self):
    
    if self.fromFiducialsNode:
      self.fromFiducialsNode.RemoveAllMarkups()
      
    if self.toFiducialsNode:
      self.toFiducialsNode.RemoveAllMarkups()

      
  def onRunRegistration(self):

    if self.fromFiducialsNode == None or self.toFiducialsNode == None:
      print('Error: no fiducial point is available.')

    ## Copy fiducials to vtkPoint
    fromPoints = vtk.vtkPoints()
    toPoints = vtk.vtkPoints()

    nFrom = self.fromFiducialsNode.GetNumberOfFiducials()
    nTo = self.toFiducialsNode.GetNumberOfFiducials()

    if nFrom != nTo:
      print("ERROR: The numbers of fixed and moving landmarks do not match.")
      return

    fromPoints.SetNumberOfPoints(nFrom)
    toPoints.SetNumberOfPoints(nFrom)

    for i in range(nFrom):
      pos = [0.0]*3
      self.fromFiducialsNode.GetNthFiducialPosition(i, pos)
      fromPoints.SetPoint(i, pos)
      self.toFiducialsNode.GetNthFiducialPosition(i, pos)
      toPoints.SetPoint(i, pos)

    # Rigid registration
    if self.rigidTypeRadioButton.checked == 1:
      
      # Create linear transform node to store the registration result
      self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode")
      self.registrationTransformNode.SetName("RegistrationTransform-Rigid")

      landmarkTransform = vtk.vtkLandmarkTransform()
      landmarkTransform.SetSourceLandmarks(fromPoints)
      landmarkTransform.SetTargetLandmarks(toPoints)
      landmarkTransform.SetModeToRigidBody()
      landmarkTransform.Update()

      calculatedTransform = vtk.vtkMatrix4x4()
      landmarkTransform.GetMatrix(calculatedTransform)
      
      self.registrationTransformNode.SetMatrixTransformToParent(calculatedTransform)
      self.registrationTransform = landmarkTransform

    # Affine registration
    if self.affineTypeRadioButton.checked == 1:
      
      # Create linear transform node to store the registration result
      self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode")
      self.registrationTransformNode.SetName("RegistrationTransform-Affine")

      landmarkTransform = vtk.vtkLandmarkTransform()
      landmarkTransform.SetSourceLandmarks(fromPoints)
      landmarkTransform.SetTargetLandmarks(toPoints)
      landmarkTransform.SetModeToAffine()
      landmarkTransform.Update()
    
      calculatedTransform = vtk.vtkMatrix4x4()
      landmarkTransform.GetMatrix(calculatedTransform)
      self.registrationTransformNode.SetMatrixTransformToParent(calculatedTransform)
      self.registrationTransform = landmarkTransform
      
    # Thin plate spline
    if self.splineTypeRadioButton.checked == 1:
      self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode")
      self.registrationTransformNode.SetName("RegistrationTransform-Spline")
      
      tpsTransform = vtk.vtkThinPlateSplineTransform()
      tpsTransform.SetBasisToR()
      
      tpsTransform.SetSourceLandmarks(fromPoints)
      tpsTransform.SetTargetLandmarks(toPoints)
      tpsTransform.Update()

      self.registrationTransformNode.SetAndObserveTransformFromParent(tpsTransform)
      self.registrationTransform = tpsTransform
    #
    # TODO: The function create a new transform node instance (either vtkMRMLLinearTransformNode or
    # vtkMRMLTransformNode) everytime called for the debugging purpose. It should clean up the old
    # transform node after creating a new one.
    #
          
    #
    # Check registration error
    #
    fre = self.CalculateRegistrationError(fromPoints, toPoints, self.registrationTransform)
    print ("FRE: %.6f mm" % fre)
    self.freLineEdit.text = "%.6f" % fre
    
    
  def CalculateRegistrationError(self, fromPoints, toPoints, transform):

    # Transform the from points
    transformedFromPoints = vtk.vtkPoints()
    transform.TransformPoints(fromPoints, transformedFromPoints)

    # Calculate the RMS distance between the to points and the transformed from points
    sumSquaredError = 0
    for i in range(toPoints.GetNumberOfPoints()):
      currentToPoint = [0, 0, 0]
      toPoints.GetPoint(i, currentToPoint)
      currentTransformedFromPoint = [0, 0, 0];
      transformedFromPoints.GetPoint(i, currentTransformedFromPoint)
      sumSquaredError = sumSquaredError + vtk.vtkMath.Distance2BetweenPoints(currentToPoint, currentTransformedFromPoint)

    return numpy.sqrt(sumSquaredError / toPoints.GetNumberOfPoints())

    
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


  def onApplyTransformChanged(self):

    # TODO: Use self.transformedCatheter instead of self.applyTransform
    
    tdnode = None

    if self.applyTransformOnRadioButton.checked == True:
      self.applyTransform = self.fromTrackingDataSelector.currentNode()
      tdnode = self.applyTransform
    else:
      tdnode = self.applyTransform
      self.applyTransform = None

    self.mrTrackingLogic.updateCatheterNode(tdnode, 0)
    self.mrTrackingLogic.updateCatheterNode(tdnode, 1)

    
  def onAutoUpdateChanged(self):
    
    if self.autoUpdateOnRadioButton.checked:
      self.autoUpdate = True
    else:
      self.autoUpdate = False

      
  def onPointSelectionParametersChanged(self):

    # Make sure to convert from millisecond to second
    self.maxTimeDifference = self.maxTimeDifferenceSliderWidget.value / 1000.0
    self.minInterval = self.minIntervalSliderWidget.value / 1000.0
    self.pointExpiration = self.pointExpirationSliderWidget.value / 1000.0
    
      
  def setMRTrackingLogic(self, t):
    
    self.mrTrackingLogic = t

    
  def updatePoints(self):

    if self.autoUpdate:
      r = self.onCollectPoints(True)
      if r:
        self.onRunRegistration()
        print("updatePoints(self): Running registration")
      else:
        print("updatePoints(self): Skipping")
      
    
