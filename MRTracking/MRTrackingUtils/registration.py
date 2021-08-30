import ctk
import qt
import slicer
import vtk
import functools
import time
import numpy
from MRTrackingUtils.qcomboboxcatheter import *

#------------------------------------------------------------
#
# MRTrackingFiducialRegistration class
#

class MRTrackingFiducialRegistration():

  def __init__(self, label="Registration"):

    self.label = label
    self.fiducialsVisible = False
    #self.trackingData = None

    # Circular buffers for registration poitns
    self.fromFiducialsTimeStamp = []  ## TODO: Should it be managed by the catheter node?
    self.toFiducialsTimeStamp = []

    # Transformation
    self.registrationTransformNode = None
    self.registrationTransform = None
    self.applyTransform = None # Specifiy the data node under the transform -- TODO: Will be obsolete. Use 'transformedCatheter'
    self.transformedCatheter = None # Specifiy a Catheter class instance to which the registration transform is applied. (Replaces self.applyTransform)
    
    self.sizeCircularBuffer = 24 # 8 time points x 3 (x, y, z) = 24
    self.pCircularBuffer = 0

    ## For automatic registration update
    self.autoUpdate = False
    self.prevNCoilsTo = 0
    self.prevNCoilsFrom = 0
    self.prevCollectionTime = 0.0

    self.minNumFiducials = 10
    self.maxNumFiducials = 100

    self.catheters = None            # CatheterCollection

    self.fromCatheter = None
    self.toCatheter = None

    self.minInterval = 1.0           # seconds
    self.maxTimeDifference = 0.1     # seconds
    self.pointExpiration = 30.0      # seconds

    
  def setCatheterCollection(self, cath):

    self.catheters = cath

    
  def buildGUI(self, parent):

    registrationLayout = qt.QFormLayout(parent)

    self.fromCatheterComboBox = QComboBoxCatheter()
    self.fromCatheterComboBox.setCatheterCollection(self.catheters)
    self.fromCatheterComboBox.currentIndexChanged.connect(self.onFromCatheterSelected)
    
    registrationLayout.addRow("Catheter (From): ", self.fromCatheterComboBox)

    self.toCatheterComboBox = QComboBoxCatheter()
    self.toCatheterComboBox.setCatheterCollection(self.catheters)
    self.toCatheterComboBox.currentIndexChanged.connect(self.onToCatheterSelected)
    
    registrationLayout.addRow("Catheter (To): ", self.toCatheterComboBox)

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
    # Overwrite Transform
    #
    
    overwriteTransformBoxLayout = qt.QHBoxLayout()
    self.overwriteTransformGroup = qt.QButtonGroup()
    self.overwriteTransformOnRadioButton = qt.QRadioButton("ON")
    self.overwriteTransformOffRadioButton = qt.QRadioButton("OFF")
    self.overwriteTransformOffRadioButton.checked = 1
    overwriteTransformBoxLayout.addWidget(self.overwriteTransformOnRadioButton)
    self.overwriteTransformGroup.addButton(self.overwriteTransformOnRadioButton)
    overwriteTransformBoxLayout.addWidget(self.overwriteTransformOffRadioButton)
    self.overwriteTransformGroup.addButton(self.overwriteTransformOffRadioButton)

    registrationLayout.addRow("Overwrite Transform: ", overwriteTransformBoxLayout)
    
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
    self.pointExpirationSliderWidget.singleStep = 5.0
    self.pointExpirationSliderWidget.minimum = 0.0
    self.pointExpirationSliderWidget.maximum = 1000.0
    self.pointExpirationSliderWidget.value = self.pointExpiration
    #self.minIntervalSliderWidget.setToolTip("")
    registrationLayout.addRow("Point Exp. (s): ",  self.pointExpirationSliderWidget)
    
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


  def onFromCatheterSelected(self):

    self.fromCatheter = self.fromCatheterComboBox.getCurrentCatheter()
    
    if self.fromCatheter == None:
      return

    self.fromCatheter.registration = self
    
    fiducialsNode = self.fromCatheter.getRegistrationFiducialNode()
    if fiducialsNode == None:
      fiducialsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
      fiducialsNode.SetName('RegistrationPoints-' + str(self.fromCatheter.catheterID))
      self.fromCatheter.setRegistrationFiducialNode(fiducialsNode.GetID())
      
    dnode = fiducialsNode.GetDisplayNode()
    dnode.SetVisibility(self.fiducialsVisible)

    
  def onToCatheterSelected(self):

    self.toCatheter = self.toCatheterComboBox.getCurrentCatheter()
    
    if self.toCatheter == None:
      return

    self.toCatheter.registration = self
    
    fiducialsNode = self.toCatheter.getRegistrationFiducialNode()
    if fiducialsNode == None:
      fiducialsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
      fiducialsNode.SetName('RegistrationPoints-' + str(self.toCatheter.catheterID))
      self.toCatheter.setRegistrationFiducialNode(fiducialsNode.GetID())
      
    dnode = fiducialsNode.GetDisplayNode()
    dnode.SetVisibility(self.fiducialsVisible)


  def onCollectPoints(self, auto=False):

    # Returns True if registration needs to be updated.
    fCollect = True # Flag to collect points
    
    # Check the current time 
    currentTime = time.time()
    
    if auto:
      fCollect = False # If auto=True, this function won't collect the points in default.

    fromCurveNodeID =  self.fromCatheter.curveNodeID
    toCurveNodeID = self.toCatheter.curveNodeID

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
    
    fromFiducialsNode = self.fromCatheter.getRegistrationFiducialNode()
    
    if fromFiducialsNode:
      dnode = fromFiducialsNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)
    else:
      print("Error: Fiducials Node for 'From' is not available.")
      return

    toFiducialsNode = self.toCatheter.getRegistrationFiducialNode()
    
    
    if toFiducialsNode:
      dnode = toFiducialsNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)
    else:
      print("Error: Fiducials Node for 'To' is not available.")
      return

    ## Get TrackingData 
    coilPosFrom = self.fromCatheter.coilPositions
    coilPosTo = self.toCatheter.coilPositions

    #
    # Obtain the corresponding points on both catheters. 
    # We use the tracking coils on the 'from' catheter as fiducial points for registration.
    # The corresponding points on the 'to' catheters are estimated by intepolation (by calling
    # getInterpolatedFiducialPoints())
    #
    pointListFrom = self.fromCatheter.getFiducialPoints()
    [pointListTo, pointMask] = self.toCatheter.getInterpolatedFiducialPoints(coilPosFrom)

    if pointListTo == None:
      print("Error: Could not estimate the fiducial points.")
      return
    
    # TODO: Previously, we check the coil positions and determine which coils (i.e., coils on the 'from'
    # catheter or the 'to' catheter) are used as registration fidicuals. We skip this process and use
    # the 'from' catheter's coils as fiducials.
    
    # s = None
    # t = None
    # curve0Node = None
    # curve1Node = None
    # curve0FiducialsNode = None
    # curve1FiducialsNode = None
    # 
    # if coilPosFrom[0] < coilPosTo[0]:
    #   s = coilPosFrom
    #   t = coilPosTo
    #   curve0Node = fromCurveNode
    #   curve1Node = toCurveNode
    #   curve0FiducialsNode = fromFiducialsNode
    #   curve1FiducialsNode = toFiducialsNode
    # else:
    #   s = coilPosTo
    #   t = coilPosFrom
    #   curve0Node = toCurveNode
    #   curve1Node = fromCurveNode
    #   curve0FiducialsNode = toFiducialsNode
    #   curve1FiducialsNode = fromFiducialsNode

    # Assign the 'from' and 'to' catheters to 0 and 1
    curve0Node = fromCurveNode
    curve1Node = toCurveNode
    pointList0 = pointListFrom
    pointList1 = pointListTo
    curve0FiducialsNode = fromFiducialsNode
    curve1FiducialsNode = toFiducialsNode

    # Check time stamp
    curve0Time = float(curve0Node.GetAttribute('MRTracking.lastTS'))
    curve1Time = float(curve1Node.GetAttribute('MRTracking.lastTS'))

    # Check if it is too early to perform new registration
    if ((curve0Time - self.prevCollectionTime) < self.minInterval) and ((curve1Time - self.prevCollectionTime) < self.minInterval):
      return False

    # Check if the acquisition time difference between the two curves are small enough
    if abs(curve0Time - curve1Time) > self.maxTimeDifference:
      return False
            
    self.prevCollectionTime = currentTime
                                                
    k = 0
    trans = vtk.vtkMatrix4x4()
    pos0 = [0.0] * 3
    pos1 = [0.0] * 3

    invTransform = None
    if self.applyTransform and self.registrationTransform:
      invTransform = self.registrationTransform.GetInverse()
      
    nCoils = len(pointList0)
      
    for j in range(nCoils):

      if pointMask[j] == False:
        # Skip if the point is not valid.
        continue
      
      pos0 = pointList0[j]
      pos1 = pointList1[j]

      if self.applyTransform and invTransform:
        v = invTransform.TransformPoint(pos0)
        pos0[0] = v[0]
        pos0[1] = v[1]
        pos0[2] = v[2]
      
      # Record the coordinates
      nCurve0 = curve0FiducialsNode.GetNumberOfFiducials()
      
      if nCurve0 > self.sizeCircularBuffer: # Overwrite a previous point.
        # Note: Time stamp is recorded as a label.
        curve0FiducialsNode.SetNthFiducialPosition(self.pCircularBuffer, pos0[0], pos0[1], pos0[2])
        curve1FiducialsNode.SetNthFiducialPosition(self.pCircularBuffer, pos1[0], pos1[1], pos1[2])
        curve0FiducialsNode.SetNthFiducialLabel(self.pCircularBuffer, str(curve0Time))
        curve1FiducialsNode.SetNthFiducialLabel(self.pCircularBuffer, str(curve1Time))
        self.pCircularBuffer = (self.pCircularBuffer + 1) % self.sizeCircularBuffer
      else: # Add a new point
        curve0FiducialsNode.AddFiducial(pos0[0], pos0[1], pos0[2], str(curve0Time))
        curve1FiducialsNode.AddFiducial(pos1[0], pos1[1], pos1[2], str(curve1Time))

      print('Add From (%f, %f, %f)' % (pos0[0], pos0[1], pos0[2]))
      print('Add To (%f, %f, %f)' % (pos1[0], pos1[1], pos1[2]))


    # Discard expired points
    self.discardExpiredPoints(curve0FiducialsNode, curve1FiducialsNode, currentTime)
      
    # Check if it is ready for new registration
    # TODO: Should we also check the number of fiducials for toFiducialsNode?
    if fromFiducialsNode.GetNumberOfFiducials() >  self.minNumFiducials:
      return True
    else:
      return False
    
    
  def discardExpiredPoints(self, fidNode0, fidNode1, currentTime):
    
    nCurve0 = fidNode0.GetNumberOfFiducials()
    nCurve1 = fidNode1.GetNumberOfFiducials()

    if nCurve0 != nCurve1:
      print('Error: the numbers of the fiducials for registration do not match')
      return 0

    i = 0
    while i < fidNode0.GetNumberOfFiducials():
      ts0 = float(fidNode0.GetNthFiducialLabel(i))
      ts1 = float(fidNode1.GetNthFiducialLabel(i))
      if (currentTime - ts0 > self.pointExpiration) or (currentTime - ts1 > self.pointExpiration):
        print('Point has been expired. ')
        fidNode0.RemoveNthControlPoint(i)
        fidNode1.RemoveNthControlPoint(i)
      else:
        i += 1

    
  def onClearPoints(self):

    fromFiducialsNode = self.fromCatheter.getRegistrationFiducialNode()
    toFiducialsNode = self.toCatheter.getRegistrationFiducialNode()
    
    if fromFiducialsNode:
      fromFiducialsNode.RemoveAllMarkups()

    if toFiducialsNode:
      toFiducialsNode.RemoveAllMarkups()

      
  def onRunRegistration(self):

    fromFiducialsNode = self.fromCatheter.getRegistrationFiducialNode()
    toFiducialsNode = self.toCatheter.getRegistrationFiducialNode()
    
    if fromFiducialsNode == None or toFiducialsNode == None:
      print('Error: no fiducial point is available.')

    ## Copy fiducials to vtkPoint
    fromPoints = vtk.vtkPoints()
    toPoints = vtk.vtkPoints()

    nFrom = fromFiducialsNode.GetNumberOfFiducials()
    nTo = toFiducialsNode.GetNumberOfFiducials()

    if nFrom != nTo:
      print("ERROR: The numbers of fixed and moving landmarks do not match.")
      return

    fromPoints.SetNumberOfPoints(nFrom)
    toPoints.SetNumberOfPoints(nFrom)

    for i in range(nFrom):
      pos = [0.0]*3
      fromFiducialsNode.GetNthFiducialPosition(i, pos)
      fromPoints.SetPoint(i, pos)
      toFiducialsNode.GetNthFiducialPosition(i, pos)
      toPoints.SetPoint(i, pos)

    # Check if we keep previous transform or overwrite
    overwriteTransform = self.overwriteTransformOnRadioButton.checked
    classType = None
    nodeName = None
    if self.registrationTransformNode:
      classType = self.registrationTransformNode.GetClassName()
      nodeName = self.registrationTransformNode.GetName()
      
    # Rigid registration
    if self.rigidTypeRadioButton.checked == 1:

      if overwriteTransform == 1:
        if classType != 'vtkMRMLLinearTransformNode' and nodeName != 'RegistrationTransform-Rigid':
          try:
            self.registrationTransformNode = slicer.util.getNode('RegistrationTransform-Rigid')
          except slicer.util.MRMLNodeNotFoundException:
            self.registrationTransformNode = None
      else:
        self.registrationTransformNode = None
      
      if self.registrationTransformNode == None:
        # Create linear transform node to store the registration result
        self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
        self.registrationTransformNode.SetName('RegistrationTransform-Rigid')

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
      
      if overwriteTransform == 1:
        if classType != 'vtkMRMLLinearTransformNode' and nodeName != 'RegistrationTransform-Affine':
          try:
            self.registrationTransformNode = slicer.util.getNode('RegistrationTransform-Affine')
          except slicer.util.MRMLNodeNotFoundException:
            self.registrationTransformNode = None
      else:
        self.registrationTransformNode = None
      
      if self.registrationTransformNode == None:
        # Create linear transform node to store the registration result
        self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
        self.registrationTransformNode.SetName('RegistrationTransform-Affine')

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

      if overwriteTransform == 1:
        if classType != 'vtkMRMLTransformNode' and nodeName != 'RegistrationTransform-Spline':
          try:
            self.registrationTransformNode = slicer.util.getNode('RegistrationTransform-Spline')
          except slicer.util.MRMLNodeNotFoundException:
            self.registrationTransformNode = None
      else:
        self.registrationTransformNode = None

      if self.registrationTransformNode == None:
        self.registrationTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        self.registrationTransformNode.SetName('RegistrationTransform-Spline')
      
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

    fromFiducialsNode = self.fromCatheter.getRegistrationFiducialNode()
    toFiducialsNode = self.toCatheter.getRegistrationFiducialNode()
    
    if fromFiducialsNode:
      dnode = fromFiducialsNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)
        
    if toFiducialsNode:
      dnode = toFiducialsNode.GetDisplayNode()
      dnode.SetVisibility(self.fiducialsVisible)


  def onApplyTransformChanged(self):

    # TODO: Use self.transformedCatheter instead of self.applyTransform
    
    tdnode = None

    if self.applyTransformOnRadioButton.checked == True:
      self.applyTransform = self.fromCatheter
      tdnode = self.applyTransform
    else:
      tdnode = self.applyTransform
      self.applyTransform = None

    self.fromCatheter.updateCatheterNode()

    
  def onAutoUpdateChanged(self):
    
    if self.autoUpdateOnRadioButton.checked:
      self.autoUpdate = True
    else:
      self.autoUpdate = False

      
  def onPointSelectionParametersChanged(self):

    # Make sure to convert from millisecond to second
    self.maxTimeDifference = self.maxTimeDifferenceSliderWidget.value / 1000.0
    self.minInterval = self.minIntervalSliderWidget.value / 1000.0
    self.pointExpiration = self.pointExpirationSliderWidget.value
    
      
  def updatePoints(self):

    if self.autoUpdate:
      r = self.onCollectPoints(True)
      if r:
        self.onRunRegistration()
        print("updatePoints(self): Running registration")
      else:
        #print("updatePoints(self): Skipping")
        pass
      
    
