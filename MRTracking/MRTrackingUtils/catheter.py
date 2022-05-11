#------------------------------------------------------------
#
# Catheter Class
#

#
# The Catheter class is designed to replace the TrackingData class, which manages data
# and parameters to visualize catheters. The major difference between the Catheter and
# Tracking classes is the number of catheters they manage; the Catheter class only
# manages one catheter whereas the TrackingData class manages two.
#
# Ideally, the Catheter class should be implemented as an MRML node; however, this approach
# is not possible, because the Python-wrapped VTK does not allow to override the methods defined
# in the parent classes, making it difficult to create an MRML node that works with some of
# convenient features in Slicer, such as qMRMLNodeComboBox.
# Instead, the Catheter class instance creates one parent vtkMRMLMarkupsCurveNode to keep
# all the tracking transforms under one linear transform, and save all the parameters as
# attributes.

from qt import QObject, Signal, Slot
import slicer
import numpy
import vtk
import time


class CatheterCollection(QObject):
  
  # CatheterCollection class manages Catheter class instances. The primary purpose of this
  # class is to update GUI elements (e.g., QComboBoxCatheter) when any of the Catheter class
  # instances is updated. This is achieved by the following signals:
  
  cleared = Signal()    # Emitted when the list is cleared.
  added = Signal(int)   # Emitted when a catheter is added.
  removed = Signal(int) # Emitted when a catheter is removed.

  # The following slots are defined in QComboBoxCatheter and connected to the above signals
  # from QComboBoxCatheter.setCatheterCollection():
  #
  #   @Slot()
  #   def onCatheterCleared(self)
  #
  #   @Slot(int)
  #   def onCatheterAdded(self, index)
  #
  #   @Slot(int)
  #   def onCatheterRemoved(self, index)

  def __init__(self):

    super(CatheterCollection, self).__init__(None)

    self.catheterList = []
    self.lastID = 0;

    
  def add(self, cath):

    self.catheterList.append(cath)
    cath.catheterID = self.lastID
    self.lastID = self.lastID + 1
    self.added.emit(len(self.catheterList)-1)

    
  def remove(self, cath):

    obj = None
    index = -1
    if isinstance(cath, Catheter):     # If a class instance is given
      obj = cath
      index = self.catheterList.index(cath)
    elif isinstance(cath, int):        # If an index is given
      if cath >= 0 and cath < len(self.catheterList):
        obj = self.catheterList[cath]
        index = cath

    if obj:
      try:
        self.catheterList.remove(obj)
        self.removed.emit(index)
      except ValueError:
        print('Could not remove the object: %s' % cath.name)
      
  def clear(self):
    self.catheterList.clear()
    self.cleared.emit()

        
  def getIndex(self, cath):

    index = 0
    for c in self.catheterList:
      if cath == c:
        return index
      index = index + 1

    # Couldn't find
    return -1

  
  def getNumberOfCatheters(self):

    return len(self.catheterList)
  
  
  def getCatheter(self, index):

    if index >= 0 and index < self.getNumberOfCatheters():
      return self.catheterList[index]

    return None

  
class Catheter:

  def __init__(self, name='Cath', curveNodeID=None):

    self.MAX_COILS = 8

    # Primary curve node
    # Each Catheter class is tied with a dedicated vtkMRMLMarkupsCurveNode.
    # (Ideally, this should be done by implementing the Catheter class as a child class of vtkMRMLMarkupsCurveNode,
    # but this is not possible because of the limitations for Python-wrapped vtk.
    curveNode = None
    if curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
      
    if curveNode == None:
      curveNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')

    if curveNode == None:
      print('Catheter.__init__(): Error - Could not create a curveNode.')
      return
    
    self.curveNodeID = curveNode.GetID()

    #slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.name = name
    self.catheterID = None
    self.trackingDataNodeID = ''           # Tracking node ID associated with this catheter.
    self.logic = None
    self.widget = None
    self.eventTag = ''

    self.numberOfCoils = 0
    self.childTransformNodeIDList = [None] * self.MAX_COILS
    
    self.lastMTime = 0

    # Coil model
    self.coilPointsNP = numpy.array([])
    self.coilPoints = vtk.vtkPoints()
    self.coilModelNodeID = ''
    self.coilPolyArray = []
    self.coilAppendPolyData = None
    self.coilTransformArray = []
    self.coilTransformFilterArray = []
    self.coilLength = 3.0

    # Sheath model
    self.sheathModelNode = None 
    self.sheathPoly = None

    self.tipTransformNode = None

    # Coil configuration
    self.coilPositions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.activeCoils = [True, True, True, True, False, False, False, False]
    self.showCoilLabel = False
    self.coilOrder = True         # 'Distal first' = True; 'Proximal first' = False
    self.sheathRange = [-1, -1]

    # Egram data
    self.egramDataNodeID = None

    # Point Recording
    self.pointRecording = False
    # Recording poitns are determined by (self.activeCoils and self.pointRecordingMask)
    self.pointRecordingMask = numpy.array([True, True, True, True, True, True, True, True])
    self.pointRecordingMarkupsNode = None
    self.pointRecordingDistance = 0.0
    self.prevRecordedPoints = numpy.array([[0.0, 0.0, 0.0]])
    
    # Coordinate system
    self.axisDirections = numpy.array([1.0, 1.0, 1.0])
    
    # Visual settings
    self.opacity = 1.0
    self.radius = 0.5
    self.modelColor = [0.0, 0.0, 1.0]

    # Filtering
    # Temporal filtering is used to stabilize the tracking data.
    self.cutOffFrequency = 7.50 # Hz
    self.transformProcessorNodes = [None] * self.MAX_COILS
    self.filteredTransformNodes = [None] * self.MAX_COILS

    # Acquisition trigger
    #
    # The user can trigger data acquisition with another catheter object. This acquisition trigger mechanism
    # may be helpful when the user wants to activate/deactivate one tracking system to avoid interference
    # between two or more tracking systems used at the same time. For example, consider two tracking systems
    # that are acquiring the device independenly with the following timings:
    #
    #
    #   Tracking A |----------xxxxxxxxxx----------xxxxxxxxxx----------xxxxxxxxxx----------xxxxxxxxxx--------..
    #
    #   Tracking B |--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x--x-..
    #
    #     ( '-'... idling, 'x'... acquisition)                                                    ----> Time
    #
    #     
    # Suppose Tracking A introduces noise into tracking data from Tracking B when it is active. In this case,
    # the user wants to acquire tracking data only when Tracking B is idle by setting an acquisition window
    # period:
    #
    #     
    #   Tracking B |----------xxxxxxxxxx----------xxxxxxxxxx----------xxxxxxxxxx----------xxxxxxxxxx--------..
    #
    #   Acq. window                     |--------|          |--------|          |--------|          |-------
    #
    #   Tracking A |--------------------x--x--x--x-----------x--x--x--------------x--x--x-----------x--x--x-..
    #
    # 
    # In the Catheter class, the acquisition window can be configured by specifying a catheter that serves
    # as a trigger, and two delay time parameters that define the start and the end of the acquisition window.
    # 
    #
    #   Tracking B |----------xxxxxxxxxx----------xxxxxxxxxx----------xxxxxxxxxx----------xxxxxxxxxx--------..
    #
    #   Acq. window                     |--------|          |--------|          |--------|          |-------
    #                
    #                         ^         ^        ^
    #                         |---------|        |
    #                         |  delay0          |
    #                         |------------------|
    #                      trigger     delay1 
    #                        
    #   Tracking A |--------------------x--x--x--x-----------x--x--x--------------x--x--x-----------x--x--x-..
    #
    #
    
    self.acquisitionTrigger = None             # The catheter object that triggers data acquisition
    self.acquisitionTriggerNodeID = None
    self.acquisitionWindowDelay = [0.0, 0.0]   # Data acquisition window, delay from the trigger (millisecond)
    self.acquisitionWindowCurrent = [0.0, 0.0] # Current data acquisition window (system clock - seconds)
    self.acquisitionTriggerTag = None

    # Registration
    self.registration = None

    # Distortion correction
    self.distortionTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLGridTransformNode')
    
    ## Default values for self.coilPositions:
    self.defaultCoilPositions = {}
    self.defaultCoilPositions['"NavX-Ch0"'] = [0,20,40,60]
    self.defaultCoilPositions['"NavX-Ch1"'] = [0,20,40,60]
    self.defaultCoilPositions['"WWTracker"'] = [10,30,50,70]

    self.registrationFiducialNodeID = None     # MarkupsFiducialNode for poitn-based registration
    
    

  def __del__(self):
    print("Catheter.__del__() is called.")

    
  def setName(self, name):
    self.name = name
    
    if self.curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
      if curveNode:
        curveNode.SetName(self.name + '_curve')

    # TODO: Change the filtered transform names?

    
  # Will be obsolete
  def setID(self, id):
    self.trackingDataNodeID = id

    
  def setTrackingDataNodeID(self, id):
    self.trackingDataNodeID = id

    
  def setEgramDataNodeID(self, id):
    self.egramDataNodeID = id
    

  def setLogic(self, logic):
    self.logic = logic

    
  def isActive(self):
    if self.eventTag == '':
      return False
    else:
      return True


  def activateTracking(self):
    
    #
    # The following section adds an observer invoked by an NodeModifiedEvent
    # NOTE on 09/10/2020: This mechanism does not work well for the tracker stabilizer. 
    #
    tdnode = slicer.mrmlScene.GetNodeByID(self.trackingDataNodeID)
    
    if tdnode:
      print('activateTracking(): Adding transforms..')
      
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        # Create transform nodes for filtered tracking data
        self.setFilteredTransforms(tdnode)

        ## TODO: Using the first node to trigger the event may cause a timing issue.
        ## TODO: Using the filtered transform node will invoke the event handler every 15 ms as fixed in
        ##       TrackerStabilizer module. It is not guaranteed that every tracking data is used when
        ##       the tracking frame rate is higher than 66.66 fps (=1000ms/15ms). 
        childNode = self.filteredTransformNodes[0]
        
        childNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.parent', tdnode.GetID())
        self.eventTag = childNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        print("Observer for TrackingDataBundleNode added.")
        
        return True
      else:
        return False  # Could not add observer.


  def deactivateTracking(self):
    
    if self.eventTag != '':
      childNode = self.filteredTransformNodes[0]
      childNode.RemoveObserver(self.eventTag)
      self.eventTag = ''
      return True
    else:
      return False


  def getNumberOfActiveCoils(self):
    
    nActiveCoils = sum(self.activeCoils)    
    return nActiveCoils

  
  def getFirstActiveCoilTransformNode(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.trackingDataNodeID)
    if tdnode:
      tnode = tdnode.GetTransformNode(0)
      return tnode
    else:
      return None

    
  def setFilteredTransforms(self, tdnode, createNew=True):
    #
    # To fileter the transforms under the TrackingDataBundleNode, prepare transform nodes
    # to store the filtered transforms.
    #
    nTransforms =  tdnode.GetNumberOfTransformNodes()
    
    for i in range(nTransforms):

      inputNode = tdnode.GetTransformNode(i)

      # TODO: The following code does not work if two Catheter instances use the same coil channels
      # on the same TrackingData node. Needs to include the Catheter instance name or the unique catheterID
      # in the attribute key.
      if self.filteredTransformNodes[i] == None:
        filteredNodeID = str(inputNode.GetAttribute('MRTracking.' + str(self.catheterID) + '.filteredNode'))
        if filteredNodeID != '':
          self.filteredTransformNodes[i] = slicer.mrmlScene.GetNodeByID(filteredNodeID)
          
        if self.filteredTransformNodes[i] == None and createNew:
          print('setFilteredTransforms(): Adding linear transform node.')
          self.filteredTransformNodes[i] = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
          inputNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.filteredNode', self.filteredTransformNodes[i].GetID())
          
      if self.transformProcessorNodes[i] == None:
        processorNodeID = str(inputNode.GetAttribute('MRTracking.' + str(self.catheterID) + '.processorNode'))
        if processorNodeID != '':
          self.transformProcessorNodes[i] = slicer.mrmlScene.GetNodeByID(processorNodeID)
        if self.transformProcessorNodes[i] == None and createNew:
          print('setFilteredTransforms(): Adding transform processor node.')
          self.transformProcessorNodes[i] = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformProcessorNode')
          inputNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.processorNode', self.transformProcessorNodes[i].GetID())

      if self.filteredTransformNodes[i]:
        self.filteredTransformNodes[i].SetName(inputNode.GetName() + '_filtered')
        
      if self.transformProcessorNodes[i]:
        self.transformProcessorNodes[i].SetName(inputNode.GetName() + '_processor')
        tpnode = self.transformProcessorNodes[i]
        tpnode.SetProcessingMode(slicer.vtkMRMLTransformProcessorNode.PROCESSING_MODE_STABILIZE)
        tpnode.SetStabilizationCutOffFrequency(self.cutOffFrequency)
        tpnode.SetStabilizationEnabled(1)
        tpnode.SetUpdateModeToAuto()
        tpnode.SetAndObserveInputUnstabilizedTransformNode(inputNode)
        tpnode.SetAndObserveOutputTransformNode(self.filteredTransformNodes[i])


  def onIncomingNodeModifiedEvent(self, caller, event):

    parentID = str(caller.GetAttribute('MRTracking.' + str(self.catheterID) + '.parent'))
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)

    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      # Update coordinates in the fiducial node.
      nCoils = tdnode.GetNumberOfTransformNodes()
      fUpdate = False
      currentTime = time.time()
      if nCoils > 0:
        # Update timestamp
        # TODO: Should we check all time stamps under the tracking node?
        tnode = tdnode.GetTransformNode(0)
        mTime = tnode.GetTransformToWorldMTime()
        if mTime > self.lastMTime:
          self.lastMTime = mTime
          self.lastTS = currentTime
          fUpdate = True

      # Acquisition Trigger
      if self.acquisitionTrigger:
        # Check if the current time is outside the acquisition window
        if currentTime < self.acquisitionWindowCurrent[0] or currentTime > self.acquisitionWindowCurrent[1]:
          return

      # Update catheter/registration
      self.updateCatheterNode()
      
      if fUpdate and self.registration:
        self.registration.updatePoints()

        
  def onAcquisitionTriggerEvent(self, caller, event):
    #parentID = str(caller.GetAttribute('MRTracking.' + str(self.catheterID) + '.parent'))
    currentTime = time.time()
    
    if currentTime > self.acquisitionWindowCurrent[1]: # Current window has been expired
      self.acquisitionWindowCurrent[0] = currentTime + self.acquisitionWindowDelay[0] / 1000.0
      self.acquisitionWindowCurrent[1] = currentTime + self.acquisitionWindowDelay[1] / 1000.0


  def pointsToNumpyArray(self, points, pointsNP):
    nPoints = points.GetNumberOfPoints()
    numpy.resize(pointsNP, (nPoints,3))
    
    for i in range(nPoints):
      v = points.GetPoint(i)
      pointsNP[i] = numpy.array(v)


  def getActiveCoilPositions(self, posArray=None, activeCoils=None, egramTable=None):
    # Get a list of coil positions orderd from distal to proximal.
    # This function takes account of self.coilOrder parameter.
    # If posArray is not specified, it creates a new array and returns it.

    fReturn = (posArray==None)

    if activeCoils == None:
      activeCoils = self.activeCoils
    
    nActiveCoils = sum(activeCoils)
    nCoils = len(activeCoils)

    # Create or resize posArray
    if posArray == None:
      posArray = numpy.zeros((nActiveCoils,3))
    else:
      #numpy.resize(posArray, (nActiveCoils,3))
      posArray.resize((nActiveCoils,3), refcheck=False)

    # If the coil order is 'Proximal First', set a flag to flip the coil order.
    fFlip = (not self.coilOrder)
    
    j = 0
    for i in range(nCoils):
      if activeCoils[i]:
        tnode = self.filteredTransformNodes[i]
        trans = tnode.GetTransformToParent()
        v = trans.GetPosition()

        idx = j
        if fFlip:
          idx = -1-j
          
        posArray[idx] = v
        j = j + 1
        
    # Adjust axis directions
    posArray = posArray*self.axisDirections

    if fReturn:
      return posArray

    
  def getActiveCoilEgram(self, recordingMask):
    # returns a tuple (header, arrayNP), where 'header' is an array of strings and 'arrayNP'
    # a numpy.array of egram parameters.
    
    (egramHeader, egramTable) = self.getEgramData()
    egramTableNP = numpy.array(egramTable)
    nrows = egramTableNP.shape[0]

    # If the coil order is 'Proximal First', set a flag to flip the coil order.
    fFlip = (not self.coilOrder)

    mask = recordingMask
    
    # Copy egram data
    if fFlip:
      mask = mask[::-1]

    mask = mask[:nrows]

    #print(egramTableNP)
    #print(recordingMask)
    egramTableNPMasked = egramTableNP[mask]

    return (egramHeader, egramTableNPMasked)


      

  def getActiveCoilPositionsFromTip(self):
    # Get a list of coil positions from the tip orderd from distal to proximal.
    # The tip positions are the distances along the catheter from the tip.
    # This function takes account of self.coilOrder parameter.
    # If posArray is not specified, it creates a new array and returns it.

    nActiveCoils = sum(self.activeCoils)
    nCoils = len(self.activeCoils)

    posArray = numpy.array(self.coilPositions)
    posArray = posArray[self.activeCoils[:len(self.coilPositions)]]
    
    # If the coil order is 'Proximal First', set a flag to flip the coil order.
    if (not self.coilOrder):
      posArray = posArray[::-1]

    return posArray



  
  #def createDistortionTransform(self):
  #
  #  rasBounds = [0,]*6
  #  rasBounds = [-20,20,-20,20,-20,20]
  #  
  #  from math import floor, ceil
  #
  #  trans = vtk.vtkTransform()
  #  trans.Translate(10,20,30)
  #  trans.rotateZ(20)
  #  
  #  origin = map(int,map(floor,rasBounds[::2]))
  #  maxes = map(int,map(ceil,rasBounds[1::2]))
  #  boundSize = [m - o for m,o in zip(maxes,origin) ]
  #  spacing = [1.0, 1.0, 1.0]
  #  samples = [ceil(b / s) for b,s in zip(boundSize,spacing)]
  #  extent = [0,]*6
  #  extent[::2] = [0,]*3
  #  extent[1::2] = samples
  #  extent = map(int,extent)
  #  
  #  toGrid = vtk.vtkTransformToGrid()
  #  toGrid.SetGridOrigin(origin)
  #  toGrid.SetGridSpacing(spacing)
  #  toGrid.SetGridExtent(extent)
  #  toGrid.SetInput(trans)
  #  toGrid.Update()
  #  gridTransform = vtk.vtkGridTransform()
  #  gridTransform.SetDisplacementGridData(toGrid.GetOutput())
  #
  #  if self.distortionTransformNode == None:
  #    gridNode = slicer.vtkMRMLGridTransformNode()
  #    gridNode.SetName(state.transform.GetName()+"-grid")
  #    slicer.mrmlScene.AddNode(gridNode)
  #    
  #  gridNode.SetAndObserveTransformFromParent(gridTransform)
    
    
  def updateCatheterNode(self):

    curveNode = None
    
    if self.curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)

    if curveNode == None:
      curveNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      self.curveNodeID = curveNode.GetID()
      curveNode.SetName(self.name + '_curve')
    
    prevState = curveNode.StartModify()
    #curveNode.SetCurveTypeToPolynomial()
    
    nActiveCoils = sum(self.activeCoils)

    #TODO: getActiveCoilPositions() currently returns numpy.array. Should it be a VTK point?
    self.coilPointsNP = self.getActiveCoilPositions()
    #print(self.coilPointsNP)

    # Update time stamp
    ## TODO: Ideally, the time stamp should come from the data source rather than 3D Slicer.
    curveNode.SetAttribute('MRTracking.lastTS', '%f' % self.lastTS)
    
    # Point resampling for better curve interpolation
    if self.coilPoints == None:
      self.coilPoints = vtk.vtkPoints()
    self.coilPoints.SetNumberOfPoints(nActiveCoils)

    # Convert to vtkPoints. 
    i = 0
    for v in self.coilPointsNP:
      self.coilPoints.SetPoint(i, v)
      i = i + 1

    ## ------------------------
    ## TODO: Interpolation should be performed in the transformed space
    transformedCoilPoints = None
    
    if self.registration and \
        self.registration.applyTransform and \
        self.registration.applyTransform.catheterID == self.catheterID and \
        self.registration.registrationTransform:
      
      #egramPoint = self.registration.registrationTransform.TransformPoint(egramPoint)
      transformedCoilPoints = vtk.vtkPoints()  # TODO: Make it a class member to avoid creating a new objects in each iteration?
      self.registration.registrationTransform.TransformPoints(self.coilPoints, transformedCoilPoints)
    else:
      curveNode.SetAndObserveTransformNodeID('')
      transformedCoilPoints = self.coilPoints
      
    nTransformedPoints = transformedCoilPoints.GetNumberOfPoints()
    transformedCoilPointsNP = numpy.zeros((nTransformedPoints,3))
    self.pointsToNumpyArray(transformedCoilPoints, transformedCoilPointsNP)
      
    length = 0.0
    prevPoint = numpy.array(transformedCoilPoints.GetPoint(0))
    pPrev = transformedCoilPointsNP[0]
    for p in transformedCoilPointsNP[1:]:
      length = length + numpy.linalg.norm(p-pPrev)
      pPrev = p
    

    # Determin the resampling interval. Aim to divide the catheter into 10 segments.
    resamplingIntv = length / 10.0
    if resamplingIntv < 0.01: # The minimum value for resamplingIntv is 0.01.
      resamplingIntv = 0.01

    interpolatedPoints = vtk.vtkPoints()
    #slicer.vtkMRMLMarkupsCurveNode.ResamplePoints(self.coilPoints, interpolatedPoints, resamplingIntv, False)
    slicer.vtkMRMLMarkupsCurveNode.ResamplePoints(transformedCoilPoints, interpolatedPoints, resamplingIntv, False)
    nInterpolatedPoints = interpolatedPoints.GetNumberOfPoints()
    #curveNode.SetControlPointPositionsWorld(interpolatedPoints)
    # Set pre-registration coordinates
    nControlPoints = curveNode.GetNumberOfControlPoints()
    if nControlPoints > nInterpolatedPoints:
      i = 0
      for i in range(nInterpolatedPoints):
        p = interpolatedPoints.GetPoint(i)
        curveNode.SetNthControlPointPosition(i, p[0], p[1], p[2])
      for i in range(nInterpolatedPoints, nControlPoints):
        curveNode.RemoveNthControlPoint(nInterpolatedPoints)
    else:
      i = 0
      for i in range(nControlPoints):
        p = interpolatedPoints.GetPoint(i)
        curveNode.SetNthControlPointPosition(i, p[0], p[1], p[2])
      for i in range(nControlPoints,nInterpolatedPoints):
        p = interpolatedPoints.GetPoint(i)
        v = vtk.vtkVector3d(p)
        curveNode.InsertControlPoint(i, v)

    coilPosFromTip = self.getActiveCoilPositionsFromTip()
    tipLength = coilPosFromTip[0]

    (f, p) = self.computeExtendedTipPosition(curveNode, tipLength)
    if f:
      v = vtk.vtkVector3d(p)
      curveNode.InsertControlPoint(0,v)

    ## ------------------------
    
    curveNode.EndModify(prevState)

    ## Apply registration transform to the curve node and Egram poit
    ## NOTE: This must be done before calling self.updateCatheter() because the drawing of
    ##  the sheath and the coils relies on the transforms to the world obtained from the curve node.
    #
    ## Distortion correction
    ##egramPoint = self.coilPointsNP[0]
    #recordingPoints = None
    #
    #if self.registration and \
    #    self.registration.applyTransform and \
    #    self.registration.applyTransform.catheterID == self.catheterID and \
    #    self.registration.registrationTransform:
    #  
    #  #egramPoint = self.registration.registrationTransform.TransformPoint(egramPoint)
    #  recordingPoints = vtk.vtkPoints()  # TODO: Make it a class member to avoid creating a new objects in each iteration?
    #  self.registration.registrationTransform.TransformPoints(self.coilPoints, recordingPoints)
    #  curveNode.SetAndObserveTransformNodeID(self.registration.registrationTransformNode.GetID())
    #else:
    #  # Remove the transform, if it has already been applyed to the curve node.
    #  curveNode.SetAndObserveTransformNodeID('')
    #  recordingPoints = self.coilPoints
    
    self.transformCoilPositions(curveNode, transformedCoilPoints)  # TODO: Is transformCoilPositions() needed?
    self.updateCatheter()

    #recordingPoints = self.transformedCoilPionts

    # Get Egram data
    emask = numpy.logical_and(self.pointRecordingMask, self.activeCoils)    
    egram = self.getActiveCoilEgram(emask)

    nrow = transformedCoilPointsNP.shape[0]
    pmask = self.pointRecordingMask[self.activeCoils]
    #print(transformedCoilPointsNP)
    #print(pmask)
    recordingPoints = transformedCoilPointsNP[pmask]
    
    if self.pointRecording == True:
      if self.prevRecordedPoints.shape[0] == recordingPoints.shape[0]:
        # Calculate the RMS between the current and previous recording points.
        # If the RMS is greater than the threshold, record the current points.
        v = self.prevRecordedPoints - recordingPoints
        rms = numpy.sqrt(numpy.mean(numpy.sum(numpy.square(v), axis=1)))
        if rms > self.pointRecordingDistance:
          self.recordPoints(recordingPoints, egram)
          self.prevRecordedPoints = recordingPoints
      else:
        self.recordPoints(recordingPoints, egram)
        self.prevRecordedPoints = recordingPoints
      

  def computeExtendedTipPosition(self, curveNode, tipLength):

    # Add a extended tip
    # make sure that there is more than one points
    if curveNode.GetNumberOfControlPoints() < 2:
      return (False, None)
    
    lastPoint = curveNode.GetNumberOfControlPoints()-1

    if lastPoint < 2:
      # Not possible to compute an extended tip position.
      return (False, None)

    ## The 'curve end point matrix' (normal vectors + the curve end position)
    matrix = vtk.vtkMatrix4x4()

    curvePoints = curveNode.GetCurvePoints()
    p0 = numpy.array(curvePoints.GetPoint(0))
    p1 = numpy.array(curvePoints.GetPoint(1))

    n10 = p0 - p1
    n10 = n10 / numpy.linalg.norm(n10)

    # Tip location
    # The sign for the normal vector is '-' because the normal vector point toward points
    # with larger indecies.
    pe = p0 + n10 * tipLength

    # Update Tip transform (for volume reslicing)
    # Note Tip transform must be further transformed with the registration transform.
    if self.tipTransformNode == None:
      self.tipTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
      self.tipTransformNode.SetName(curveNode.GetName() + '-TipTransform')
      
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    self.tipTransformNode.SetMatrixTransformToParent(matrix)
    
    return (True, pe)


  def transformCoilPositions(self, curveNode, coilPoints):
    # Calculate the transformed coil positions and orientations.
    # Takes self.coilPoints as an input, and store the results in self.coilTransformArray.
    # This function takes account of both registration transform and the interpolated catheter path.
    # It applies the registration transform, and then find the closest point on the interpolated catheter path.
    
    nCoils = coilPoints.GetNumberOfPoints()
    
    if len(self.coilTransformArray) != nCoils:
      self.coilTransformArray = []
      for i in range(nCoils):
        trans = vtk.vtkTransform()
        self.coilTransformArray.append(trans)

    p = [0.0]*3
    for i in range(0, nCoils):
      coilPoints.GetPoint(i, p)
      cpi = curveNode.GetClosestCurvePointIndexToPositionWorld(p)
      if cpi >= 0:
        matrix = vtk.vtkMatrix4x4()
        curveNode.GetCurvePointToWorldTransformAtPointIndex(cpi, matrix)
        self.coilTransformArray[i].SetMatrix(matrix)


  def updateCatheter(self):

    curveNode = None
    
    if self.curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)

    if curveNode == None:
      print('Catheter.updateCatheter(): No cathterNode is found.')
      return
      
    curveDisplayNode = curveNode.GetDisplayNode()
    if curveDisplayNode:
      prevState = curveDisplayNode.StartModify()
      curveDisplayNode.SetSelectedColor(self.modelColor)
      curveDisplayNode.SetColor(self.modelColor)
      curveDisplayNode.SetOpacity(self.opacity)
      #curveDisplayNode.SliceIntersectionVisibilityOn()
      curveDisplayNode.Visibility2DOn()
      # Show/hide labels for coils
      curveDisplayNode.SetPointLabelsVisibility(self.showCoilLabel);
      curveDisplayNode.SetUseGlyphScale(False)
      curveDisplayNode.SetGlyphSize(self.radius)
      curveDisplayNode.SetTextScale(self.radius*5)
      curveDisplayNode.SetLineThickness(2.0)  # Thickness is defined as a scale from the glyph size.
      #curveDisplayNode.SetLineThickness(0.5)  # Thickness is defined as a scale from the glyph size.
      curveDisplayNode.SetHandlesInteractive(False)
      curveDisplayNode.OccludedVisibilityOff()
      curveDisplayNode.SetOccludedOpacity(0.0)
      curveDisplayNode.OutlineVisibilityOff()
      curveDisplayNode.EndModify(prevState)

    self.updateCoilModel(self.coilTransformArray, self.radius*1.5, [0.7, 0.7, 0.7], self.opacity)

    # Draw Sheath
    sheathIndex0 = -1
    sheathIndex1 = -1
    if (self.sheathRange[0] >= 0) and (self.sheathRange[1] >= 0) and (self.sheathRange[0] <= self.sheathRange[1]) and (self.sheathRange[1] < nCoils):
      p0 = [0.0]*3
      p1 = [0.0]*3
      self.coilPoints.GetPoint(self.sheathRange[0], p0)
      self.coilPoints.GetPoint(self.sheathRange[1], p1)
      sheathIndex0 = curveNode.GetClosestCurvePointIndexToPositionWorld(p0)
      sheathIndex1 = curveNode.GetClosestCurvePointIndexToPositionWorld(p1)

    if (sheathIndex0 >= 0):
      curvePoints = vtk.vtkPoints()
      curvePoints.SetNumberOfPoints(sheathIndex1-sheathIndex0+1)
      p = [0.0]*3
      idx = 0
      for i in range(sheathIndex0, sheathIndex1+1):
        curveNode.GetCurvePointToWorldTransformAtPointIndex(i, matrix)
        p[0] = matrix.GetElement(0, 3)
        p[1] = matrix.GetElement(1, 3)
        p[2] = matrix.GetElement(2, 3)
        curvePoints.SetPoint(idx, p)
        idx = idx+1
      
      self.updateSheathModelNode(curvePoints, self.radius*1.3, [0.4, 0.4, 0.4], self.opacity)


  def updateCoilModel(self, transArray, radius, color, opacity):

    curveNode = None
    if self.curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)

    if curveNode == None:
      print('Catheter.updateCoilModel(): No cathterNode is found.')
      return

    coilModelNode = None
    if self.coilModelNodeID == '':
      coilModelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
      coilModelNode.SetName(curveNode.GetName() + '-Coil')
      self.coilModelNodeID = coilModelNode.GetID()
    else:
      coilModelNode = slicer.mrmlScene.GetNodeByID(self.coilModelNodeID)

    if coilModelNode == None:
      print('Catheter.updateCoilModel(): No model node is found.')
      return

    nPoints = len(transArray)

    if len(self.coilPolyArray) != nPoints:
      self.coilPolyArray = []
      self.coilAppendPolyData = vtk.vtkAppendPolyData()
      #self.coilTransformArray = []
      self.coilTransformFilterArray = []      

      for trans in transArray:
        cylinder = vtk.vtkCylinderSource()
        cylinder.SetRadius(radius)
        cylinder.SetHeight(self.coilLength)
        cylinder.SetCenter(0.0, 0.0, 0.0)
        cylinder.CappingOn()
        cylinder.SetResolution(20)
        cylinder.Update()
        
        tfilter0 = vtk.vtkTransformPolyDataFilter()
        trans0 = vtk.vtkTransform()
        trans0.RotateX(90.0)
        trans0.Update()
        tfilter0.SetInputConnection(cylinder.GetOutputPort())
        tfilter0.SetTransform(trans0)
        tfilter0.Update()
        
        tfilter = vtk.vtkTransformPolyDataFilter()
        tfilter.SetInputConnection(tfilter0.GetOutputPort())
        tfilter.SetTransform(trans)
        tfilter.Update()
        self.coilTransformFilterArray.append(tfilter)
                
        self.coilAppendPolyData.AddInputConnection(tfilter.GetOutputPort())
        
      self.coilAppendPolyData.Update()
      coilModelNode.SetAndObservePolyData(self.coilAppendPolyData.GetOutput())
        
    else:
      # If the number of coils does not change, just update the transforms
      i = 0
      for trans in transArray:
        self.coilTransformFilterArray[i].SetTransform(trans)
        self.coilTransformFilterArray[i].Update()

      if self.coilAppendPolyData:
        self.coilAppendPolyData.Update()
      
    coilModelNode.Modified()

    coilDispID = coilModelNode.GetDisplayNodeID()
    if coilDispID == None:
      coilDispNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
      coilDispNode.SetScene(slicer.mrmlScene)
      coilModelNode.SetAndObserveDisplayNodeID(coilDispNode.GetID());
      coilDispID = coilModelNode.GetDisplayNodeID()
      
    coilDispNode = slicer.mrmlScene.GetNodeByID(coilDispID)

    prevState = coilDispNode.StartModify()
    coilDispNode.SetColor(color)
    coilDispNode.SetOpacity(opacity)
    coilDispNode.Visibility2DOn()
    coilDispNode.SetSliceDisplayModeToIntersection()
    coilDispNode.EndModify(prevState)
      
    
  def updateSheathModelNode(self, points, radius, color, opacity):

    curveNode = None
    if self.curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)

    if curveNode == None:
      print('Catheter.updateCoilModel(): No cathterNode is found.')
      return

    if self.sheathPoly==None:
      self.sheathPoly = vtk.vtkPolyData()
    
    if self.sheathModelNode == None:
      self.sheathModelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
      self.sheathModelNode.SetName('Sheath')
      curveNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.sheathModel', self.sheathModelNode.GetID())
      
    npoints = points.GetNumberOfPoints()
    
    cellArray = vtk.vtkCellArray()
    cellArray.InsertNextCell(npoints)

    for i in range(npoints):
      cellArray.InsertCellPoint(i)

    self.sheathPoly.Initialize()
    self.sheathPoly.SetPoints(points)
    self.sheathPoly.SetLines(cellArray)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetInputData(self.sheathPoly)
    tubeFilter.SetRadius(radius)
    tubeFilter.SetNumberOfSides(20)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    apd = vtk.vtkAppendPolyData()

    apd.AddInputConnection(tubeFilter.GetOutputPort())
    apd.Update()
    
    self.sheathModelNode.SetAndObservePolyData(apd.GetOutput())
    self.sheathModelNode.Modified()

    sheathDispID = self.sheathModelNode.GetDisplayNodeID()
    if sheathDispID == None:
      sheathDispNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
      sheathDispNode.SetScene(slicer.mrmlScene)
      self.sheathModelNode.SetAndObserveDisplayNodeID(sheathDispNode.GetID());
      sheathDispID = self.sheathModelNode.GetDisplayNodeID()
      
    sheathDispNode = slicer.mrmlScene.GetNodeByID(sheathDispID)

    prevState = sheathDispNode.StartModify()
    sheathDispNode.SetColor(color)
    sheathDispNode.SetOpacity(opacity)
    sheathDispNode.Visibility2DOn()
    sheathDispNode.SetSliceDisplayModeToIntersection()
    sheathDispNode.EndModify(prevState)
    

  def recordPoints(self, recordingPoints, egram=None):
    # returns a tuple (header, arrayNP), where 'header' is an array of strings and 'arrayNP'
    # a numpy.array of egram parameters.
    
    prMarkupsNode = self.pointRecordingMarkupsNode
    if prMarkupsNode == None:
      return

    egramHeader = egram[0]
    egramTableNP = egram[1]
    
    nPoints = len(recordingPoints)
    for i in range(nPoints):
      egramValues = egramTableNP[i]
      point = recordingPoints[i]
      #id = prMarkupsNode.AddFiducial(egramPoint[0], egramPoint[1], egramPoint[2])
      id = prMarkupsNode.AddFiducial(point[0], point[1], point[2])

      # Concatinate the values in egramTablesNP[i] as a string
      # See https://stackoverflow.com/questions/2721521/fastest-way-to-generate-delimited-string-from-1d-numpy-array
      desc = ','.join(numpy.char.mod('%f', egramValues))
      prMarkupsNode.SetNthControlPointDescription(id, desc)

    # If the header is not registered to the markup node, do it now.
    ev = prMarkupsNode.GetAttribute('MRTracking.' + str(self.catheterID) + '.EgramParamList')
    if ev == None:
      attr= None
      for eh in egramHeader:
        if attr:
          attr = attr + ',' + str(eh)
        else:
          attr = str(eh)
      prMarkupsNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.EgramParamList', attr)
      prMarkupsNode.Modified();


    
  #--------------------------------------------------
  # Parameter access
  #
      
  def setCurveNodeID(self, id):
    
    self.curveNodeID = id
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.curveNodeID" % self.name, id)
      return 1
    return 0


  def setOpacity(self, opacity):
    
    self.opacity = opacity

    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.opacity.0" % self.name, str(self.opacity))
      return 1
    return 0
    
  
  def setRadius(self, r):

    self.radius = r
    
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.radius.0" % self.name, str(self.radius))
      return 1
    return 0


  def setModelColor(self, color):
    
    self.modelColor = color
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.modelColor.0" % self.name, str(self.modelColor))
      return 1
    return 0

  
  def setCoilPosition(self, position):

    self.coilPositions = position
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.coilPosition.%s" % self.name, str(self.coilPositions))
      return 1
    return 0


  def setShowCoilLabel(self, s):
    
    self.showCoilLabel = s
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.showCoilLabel" % self.name, str(self.showCoilLabel))
      return 1
    return 0

  
  def setActiveCoils(self, coils):
    
    self.activeCoils = coils
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.activeCoils.%s" % (self.name), str(self.activeCoils))
      return 1
    return 0

  
  def setCoilOrder(self, s):
    # Coil order (True if Distal -> Proximal)
    
    self.coilOrder = s
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.coilOrder.%s" % (self.name), str(self.coilOrder))
      return 1
    return 0

  
  def setAxisDirection(self, dir, sign):
    # dir: 0 = x, 1 = y, 2 = z

    self.axisDirections[dir] = sign
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.axisDirection.%s" % (self.name, dir), str(self.axisDirections[dir]))
      return 1
    return 0


  def setSheathRange(self, ch0, ch1):

    print("setSheathRange(%d, %d)" % (ch0, ch1))
    # Make sure that 0 <= ch0 <= ch1 < <number of coils>
    #if ch0 > ch1:
    #  return 0
    #if ch0 < 0 or ch0 >= len(self.activeCoils):
    #  return 0
    #if ch1 < 0 or ch1 >= len(self.activeCoils):
    #  return 0

    self.sheathRange = [ch0, ch1]
    return 1
      

  def setCutOffFrequency(self, freq):

    self.cutOffFrequency = freq
    for tpnode in self.transformProcessorNodes:
      if tpnode:
        tpnode.SetStabilizationCutOffFrequency(self.cutOffFrequency)


  def setAcquisitionTrigger(self, trigger, startDelay, endDelay):

    if trigger == None:
      return

    # The catheter object that triggers data acquisition
    self.acquisitionTrigger = trigger

    triggerNode = trigger.getFirstActiveCoilTransformNode()

    if triggerNode == None:
      print("Cathter.setAcquisitionTrigger(): No trigger node is available.")
      return

    self.acquisitionTriggerNodeID = triggerNode.GetID()
    
    self.acquisitionTriggerTag = triggerNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onAcquisitionTriggerEvent)
    
    # Data acquisition window, delay from the trigger (milliseconds)
    self.setAcquisitionWindow(startDelay, endDelay)
    
    # Current data acquisition window (system clock - millisecond)
    self.acquisitionWindowCurrent = [0.0, 0.0]

    
  def setAcquisitionWindow(self, start, end):
    self.acquisitionWindowDelay[0] = start
    self.acquisitionWindowDelay[1] = end
    
    
  def removeAcquisitionTrigger(self):

    if self.acquisitionTriggerTag and self.acquisitionTriggerNodeID:

      triggerNode = slicer.mrmlScene.GetNodeByID(self.acquisitionTriggerNodeID)
      if triggerNode:
        triggerNode.RemoveObserver(self.acquisitionTriggerTag)

    self.acquisitionTriggerTag = None
    self.acquisitionTriggerNodeID = None
    
  
  def getEgramData(self):
    #
    # Get Egram data in a table. The function returns 'header' and 'table as
    # 1-D and 2-D lists respectively. For example, the values are organized as:
    #
    #     ['Max (mV)',  'Min (mV)',  'LAT (ms)']    <- variable names (header)
    #  ------------------------------------------
    #    [[ 16.002,      -15.334,     75.002   ]    <- values for the 1st channel (table[0])  
    #     [ 15.058,      -16.026,     830.019  ]    <- values for the 2nd channel (table[1])
    #     [ 17.252,      -18.490,     765.018  ]    <- values for the 3rd channel (table[2])
    #     [ 15.413,      -16.287,     695.016  ]]   <- values for the 4th channel (table[3])
    
    table = []
    header = None
    if self.egramDataNodeID:
      enode = slicer.mrmlScene.GetNodeByID(self.egramDataNodeID)
      if enode:
        text = enode.GetText()
        for line in text.splitlines():
          cols = line.split(',')
          if header == None:
            header = cols
          else:
            values = [float(s) for s in cols]
            table.append(values)
        
    return (header, table)


  def setRegistrationFiducialNode(self, nodeID):
    
    self.registrationFiducialNodeID = nodeID
    # TODO: Save as attribute. 'MRTracking.RegistrationPoints', self.fromFiducialsNode.GetID())
    
  
  def getRegistrationFiducialNode(self):

    if self.registrationFiducialNodeID == None:
      return None

    node = slicer.mrmlScene.GetNodeByID(self.registrationFiducialNodeID)

    return node


  def getFiducialPoints(self):
    
    if self.curveNodeID == None:
      return None
    
    curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
    if curveNode == None:
      return None

    nPoints = curveNode.GetNumberOfControlPoints()
    posList = []
    
    for i in range(nPoints):
      pos = [0, 0, 0]
      curveNode.GetNthControlPointPosition(i, pos)
      posList.append(pos)

    return posList

  
  def getCoilPointsAlongCurve(self):

    r = []

    if self.curveNodeID == None:
      return r
    
    curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
    if curveNode == None:
      return r
    
    curvePoly = curveNode.GetCurve()
    locator = vtk.vtkPointLocator()
    locator.SetDataSet(curvePoly)
    locator.BuildLocator()
    
    nPoints = len(self.coilPointsNP)
    curvePointsWorld = curveNode.GetCurvePointsWorld()
    
    for s in range(nPoints):
      pos = [0.0]*3
      cp = self.coilPointsNP[s]
      pid = locator.FindClosestPoint(cp)
      curvePointsWorld.GetPoint(pid, pos)
      r.append(pos)

    return r
      
  

  def getInterpolatedFiducialPoints(self, distFromTip, world=False):
    #
    #   (posList, mask) = getInterpolatedFiducialPoints(distFromTip)
    #
    # Input:
    #   distFromTip : An array of distances between the catheter tip and points on the catheter.
    #
    # Output:
    #   posList    : An array of positions
    #   mask        : A list of booleans representing whether the positions in the array are valid.
    #
    # Estimate the coordinates of the given point on the catheter by interpolation.
    # Unlike getFiducialPoints(), getInterpolatedFiducialPoints() can be used to
    # calculate intermediate points between the tracking sensors.
    # The reason to have the mask is that the coordinates of the points cannot be computed by interpolation,
    # if, for example, the point given by 'distFromTip' is not in between two coils.
    # When 'world'=True, the posList are in the world coordinate system
    #

    if self.curveNodeID == None:
      return (None, None)
    
    curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
    if curveNode == None:
      return (None, None)
    
    numpy.array([0.0, 0.0, 0.0])
    cpos = numpy.array(self.coilPositions)
    cpos.resize(8)
    cpos = cpos[self.activeCoils]   # Remove inactive coils
    
    interval = cpos[1:] - cpos[:-1]
    trans = vtk.vtkMatrix4x4()

    mask = []
    posList = []
    #upperIndexLimit = curveNode.GetNumberOfControlPoints() - 2
    upperIndexLimit = len(self.coilPointsNP) - 2

    # TODO: The curve length is measured in the transformed space - this may cause an issue when
    #   the registration transform is not rigid.

    curvePoly = curveNode.GetCurve()
    curvePoints = None
    if world:
      curvePoints = curveNode.GetCurvePointsWorld()
    else:
      curvePoints = curveNode.GetCurvePoints()
    
    locator = vtk.vtkPointLocator()
    locator.SetDataSet(curvePoly)
    locator.BuildLocator()
    
    for d in distFromTip:
      pos = [0.0]*3

      # The following gives the index of the lower end of the segment that includes 'd':
      #
      #  Example: If cpos and d have the following values:
      #       cpos = [10.0, 15.0, 20.0, 25.0, 30.0]
      #       d = 23.0
      #  The segment that includes 'd' is [20.0, 25.0], and the lower end is 20.0 (cpos[2]).
      #  's' can be computed as sum([True, True, True, False, False]) - 1 = 2.
      #

      s = numpy.sum(d >= cpos) - 1

      # Out of range
      if s < 0 or s > upperIndexLimit:
        posList.append(pos)
        mask.append(False)
        continue

      # Find the coil point on the curve
      cp = self.coilPointsNP[s]
      p0 = locator.FindClosestPoint(cp)
      cp = self.coilPointsNP[s+1]
      p1 = locator.FindClosestPoint(cp)
      #p0 = curveNode.GetCurvePointIndexFromControlPointIndex(s)
      #p1 = curveNode.GetCurvePointIndexFromControlPointIndex(s+1)
      clen = curveNode.GetCurveLengthBetweenStartEndPointsWorld(p0, p1)
      a = d - cpos[s]

      # In the following code, make sure that 'd' is less than the last element of 'cpos' to perform
      # interpolation.
      # TODO: if 'd' is greater than the last element of 'cpos', extrapolate the curve.
      if s < len(interval):
        b = interval[s]
        pindexm =  curveNode.GetCurvePointIndexAlongCurveWorld(p0, clen * a / b)
        if pindexm >= 0:
          #curveNode.GetCurvePointToWorldTransformAtPointIndex(pindexm, trans)
          curvePoints.GetPoint(pindexm, pos)
          #pos[0] = trans.GetElement(0, 3)
          #pos[1] = trans.GetElement(1, 3)
          #pos[2] = trans.GetElement(2, 3)
          posList.append(pos)
          mask.append(True)
        else:
          posList.append(pos)
          mask.append(False)

    return (posList, mask)
  
    
  #--------------------------------------------------
  # Configuration I/O
  #

  #
  # TODO: The following code is not actively used.
  #
  
    
  def loadDefaultConfig(self):
    self.loadDefaultCoilConfiguration()
    self.loadDefaultAxisDirections()
    self.loadDefaultVisualSettings()
    

  def loadDefaultCoilConfiguration(self):

    ## Load config
    settings = qt.QSettings()
    setting = []
    #name = tdnode.GetName()

    # Coil positions
    setting = settings.value(self.logic.widget.moduleName + '/' + 'CoilPositions.' + str(self.name) + '.0')
    array = []
    if setting != None:
      print('Found ' + str(self.name) + '.0' + ' in Setting')
      array = [float(f) for f in setting]
    else:
      if self.name in self.defaultCoilPositions:
        print('Found ' + str(self.name) + '.0' + ' in Default Config List')
        array = self.defaultCoilPositions[self.name]
        
    if len(array) > 0:
      try:
        if len(array) <= len(self.coilPositions):
          self.coilPositions = array
      except ValueError:
        print('Format error in coilConfig string.')

    # Active coils
    setting = settings.value(self.logic.widget.moduleName + '/' + 'ActiveCoils.' + str(name) + '.0')
    if setting != None:
      array = [bool(int(i)) for i in setting]
      
      if len(array) > 0:
        try:
          if len(array) <= len(self.activeCoils):
            self.activeCoils = array
        except ValueError:
          print('Format error in activeCoils string.')
          
          
  def loadDefaultAxisDirections(self):
    
    ## Load config
    settings = qt.QSettings()
    setting = []
    #name = tdnode.GetName()

    setting = settings.value(self.logic.widget.moduleName + '/' + 'AxisDirections.' + str(self.name))
    if setting != None:
      self.axisDirections = [float(s) for s in setting]

    
  def loadDefaultVisualSettings(self):
    
    ## Load config
    settings = qt.QSettings()
    setting = []
    #name = tdnode.GetName()

    setting = settings.value(self.logic.widget.moduleName + '/' + 'Opacity.' + str(self.name) + '.0')
    if setting != None:
      self.opacity = float(setting)
      
    setting = settings.value(self.logic.widget.moduleName + '/' + 'Radius.' + str(self.name) + '.0')
    if setting != None:
      self.radius = float(setting)

    setting = settings.value(self.logic.widget.moduleName + '/' + 'ModelColor.' + str(self.name) + '.0')
    if setting != None:
      self.modelColor = [float(s) for s in setting]
      
          
  class ParamError(Exception):
    """
    Exception raised for errors in obtaining value from the parameter node.

    Attributes:
        key -- the key used to obtain the value
        message -- explanation of the error
    """   
    def __init__(self, key, message='The value cannot be obtained.'):
      self.key  = key
      self.message = message
      super().__init__(self.message + 'Parameter: ' + key)
    
      
  def getParamFloat(self, tag, defaultValue=None):
    paramNode = self.logic.getParameterNode()
    if paramNode == None:
      raise self.ParamError(tag)

    paramStr = paramNode.GetParameter(tag)
    if paramStr != '':
      return float(paramStr)
    else:
      return defaultValue

    
  def getParamBool(self, tag, defaultValue=None):
    paramNode = self.logic.getParameterNode()
    if paramNode == None:
      raise self.ParamError(tag)
    
    paramStr = paramNode.GetParameter(tag)
    if paramStr != '':
      return bool(int(paramStr))
    else:
      return defaultValue
    
    
  def getParamStr(self, tag, defaultValue=None):
    paramNode = self.logic.getParameterNode()
    if paramNode == None:
      raise self.ParamError(tag)

    paramStr = paramNode.GetParameter(tag)
    if paramStr != '':
      return str(paramStr)
    else:
      return defaultValue

    
  def getParamFloatArray(self, tag, defaultValue=None):
    paramNode = self.logic.getParameterNode()
    if paramNode == None:
      raise self.ParamError(tag)

    paramStr = paramNode.GetParameter(tag)
    if paramStr != '':
      return [float(f) for f in paramStr]
    else:
      return defaultValue

    
  def getParamBoolArray(self, tag, defaultValue=None):
    paramNode = self.logic.getParameterNode()
    if paramNode == None:
      raise self.ParamError(tag)

    paramStr = paramNode.GetParameter(tag)
    if paramStr != '':
      return [bool(int(i)) for i in paramStr]
    else:
      return defaultValue

      
  def loadConfigFromParameterNode(self):
    """
    Load configuration from the parameter node.
    If the parameter is not available, the default value is used.

    """   

    print('Loading config from the parameter node')

    # Load default configuration first.
    self.loadDefaultConfig()
    
    try:
      self.curveNodeID = self.getParamStr("TD.%s.curveNodeID" % self.name, self.curveNodeID)
      self.showCoilLabel = self.getParamBool("TD.%s.showCoilLabel" % self.name, self.showCoilLabel)
      
      self.opacity = self.getParamFloat("TD.%s.opacity.0" % self.name, self.opacity)
      self.radius = self.getParamFloat("TD.%s.radius.0" % self.name, self.radius)
      
      self.modelColor = self.getParamFloatArray("TD.%s.modelColor.0" % self.name, self.modelColor)
      
      self.coilPositions = self.getParamFloatArray("TD.%s.coilPosition.0" % self.name, self.coilPositions)
      
      self.activeCoils = self.getParamBoolArray("TD.%s.activeCoils.0" % self.name, self.activeCoils)
      
      self.coilOrder = self.getParamBool("TD.%s.coilOrder.0" % self.name, self.coilOrder)
        
      for dir in range(3):
        self.axisDirections[dir] = self.getParamFloat("TD.%s.axisDirection.%s" % (self.name, dir), self.axisDirections[dir])

    except self.ParamError as pe:
      
      print('Error in loading configuration from the parameter node: ' + pe.key)


  def saveParameters(self, trackingDataName, parameterNode):

    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius))
    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius))
    self.parameterNode.SetParameter("TD.%s.modelColor" % (trackingDataName), str(self.modelColor))
    

  def loadParameters(self, parameterNode):
    pass


  
