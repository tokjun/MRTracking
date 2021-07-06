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

    self.minInterval = 1.0           # seconds
    self.maxTimeDifference = 0.1     # seconds

    self.catheters = None            # CatheterCollection

    self.fromCatheter = None
    self.toCatheter = None

    
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
    
    registrationLayout.addRow("Catheter (From): ", self.toCatheterComboBox)

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

    ## TODO: Assuming to use the first curve. 
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
    tdFrom = self.fromCatheter
    tdTo   = self.toCatheter
    coilPosFrom = tdFrom.coilPositions
    coilPosTo = tdTo.coilPositions
    
    #
    # Assuming that the catheter is tracked by Tracking 0 and Tracking 1 systems, the sensors for
    # each tracking system are located on the catheter as:
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
    # To register the coordinate systems for Tracking 0 and 1, we need to find the locations of
    # corresponding points in both coordinate frames. One approach to finding the corresponding
    # points is to map the sensors for Tracking 1 onto Tracking 0, or vice versa, based on
    # the known spacings between the sensors for both tracking systems, or vice versa.
    # If one of the tracking system is not as reliable as the other one, its tracking sensors
    # should be mapped to the other tracking coordinate frame. In this code, we assume that
    # the sensors for Tracking 1 are mapped onto the Tracking 0 coordinate frame.
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
    # nCoilsFrom = fromTrackingNode.GetNumberOfTransformNodes()
    # nCoilsTo = toTrackingNode.GetNumberOfTransformNodes()
    nCoilsFrom = self.fromCatheter.getNumberOfActiveCoils()
    nCoilsTo = self.toCatheter.getNumberOfActiveCoils()

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

    #
    # We check which tracking system has the first sensor closer to the tip and assigned Tracking 0
    # (i.e., s[]; see the figure above).
    #
    
    s = None
    t = None
    curve0Node = None
    curve1Node = None
    curve0FiducialsNode = None
    curve1FiducialsNode = None
    
    if coilPosFrom[0] < coilPosTo[0]:
      s = coilPosFrom
      t = coilPosTo
      curve0Node = fromCurveNode
      curve1Node = toCurveNode
      curve0FiducialsNode = fromFiducialsNode
      curve1FiducialsNode = toFiducialsNode
    else:
      s = coilPosTo
      t = coilPosFrom
      curve0Node = toCurveNode
      curve1Node = fromCurveNode
      curve0FiducialsNode = toFiducialsNode
      curve1FiducialsNode = fromFiducialsNode

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
    pos0 = [0.0] * 3
    pos1 = [0.0] * 3

    invTransform = None
    if self.applyTransform and self.registrationTransform:
      invTransform = self.registrationTransform.GetInverse()
    
    for j in range(nCoils):

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

      if b == 0.0:
        print('MRTrackingFiducialRegistration(): Invalid catheter configuration.')
        return
      
      pindexm =  curve0Node.GetCurvePointIndexAlongCurveWorld(pindex0, clen * a / b)

      curve0Node.GetCurvePointToWorldTransformAtPointIndex(pindexm, trans)
      pos0[0] = trans.GetElement(0, 3)
      pos0[1] = trans.GetElement(1, 3)
      pos0[2] = trans.GetElement(2, 3)
      if self.applyTransform and invTransform:
        v = invTransform.TransformPoint(pos0)
        pos0[0] = v[0]
        pos0[1] = v[1]
        pos0[2] = v[2]
        
      
      # 3. Obtain the coordinates for t[j]
      pindex = curve1Node.GetCurvePointIndexFromControlPointIndex(j)
      curve1Node.GetCurvePointToWorldTransformAtPointIndex(pindex, trans)
      pos1[0] = trans.GetElement(0, 3)
      pos1[1] = trans.GetElement(1, 3)
      pos1[2] = trans.GetElement(2, 3)


      # 5. Record the coordinates
      nCurve0 = curve0FiducialsNode.GetNumberOfFiducials()
      
      if nCurve0 > self.sizeCircularBuffer: # Overwrite a previous point.
        curve0FiducialsNode.SetNthFiducialPosition(self.pCircularBuffer, pos0[0], pos0[1], pos0[2])
        curve1FiducialsNode.SetNthFiducialPosition(self.pCircularBuffer, pos1[0], pos1[1], pos1[2])
        #self.fromFiducialsTimeStamp[self.pCircularBuffer] = curve0Time
        #self.toFiducialsTimeStamp[self.pCircularBuffer] = curve1Time
        self.pCircularBuffer = (self.pCircularBuffer + 1) % self.sizeCircularBuffer
      else: # Add a new point
        curve0FiducialsNode.AddFiducial(pos0[0], pos0[1], pos0[2])
        curve1FiducialsNode.AddFiducial(pos1[0], pos1[1], pos1[2])
        #self.fromFiducialsTimeStamp.append(curve0Time)
        #self.toFiducialsTimeStamp.append(curve1Time)
        
      print('Add From (%f, %f, %f)' % (pos0[0], pos0[1], pos0[2]))
      print('Add To (%f, %f, %f)' % (pos1[0], pos1[1], pos1[2]))


    # Check if it is ready for new registration
    # TODO: Should we also check the number of fiducials for toFiducialsNode?
    if fromFiducialsNode.GetNumberOfFiducials() >  self.minNumFiducials:
      return True
    else:
      return False
    
      
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
    self.pointExpiration = self.pointExpirationSliderWidget.value / 1000.0
    
      
  def updatePoints(self):

    if self.autoUpdate:
      r = self.onCollectPoints(True)
      if r:
        self.onRunRegistration()
        print("updatePoints(self): Running registration")
      else:
        print("updatePoints(self): Skipping")
      
    
