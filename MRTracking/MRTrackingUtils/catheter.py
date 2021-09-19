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

    # Coil models
    self.coilModelNodes = []
    self.coilTransformNodes = []
    self.coilPolyObjs = []
    
    # Tip model
    self.tipModelNode = None      # TODO: The node ID is saved in Tracking Data Node
    self.tipTransformNode = None  # TODO: The node ID is saved in Tracking Data Node
    self.tipPoly = None
    self.coilLength = 3.0

    # Coil configuration
    self.tipLength = 10.0
    self.coilPositions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.activeCoils = [True, True, True, True, False, False, False, False]
    self.showCoilLabel = False
    self.coilOrder = True

    # Egram data
    self.egramDataNodeID = None

    # Point Recording
    self.pointRecording = False
    self.pointRecordingMarkupsNode = None
    self.pointRecordingDistance = 0.0
    self.prevRecordedPoint = numpy.array([0.0, 0.0, 0.0])
    
    # Coordinate system
    self.axisDirections = [1.0, 1.0, 1.0]
    
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
        self.setFilteredTransforms(tdnode, self.activeCoils)

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


    
  def setFilteredTransforms(self, tdnode, activeCoils, createNew=True):
    #
    # To fileter the transforms under the TrackingDataBundleNode, prepare transform nodes
    # to store the filtered transforms.
    #
    nTransforms =  tdnode.GetNumberOfTransformNodes()
    
    for i in range(nTransforms):

      ## Skip if the coil is not active
      #if self.activeCoils[i] == False:
      #  continue
      
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
      
        
  def updateCatheterNode(self):

    #tdnode = slicer.mrmlScene.GetNodeByID(self.trackingDataNodeID)
    #if tdnode == None:
    #  print('updateCatheter(): Error - no TrackingDataNode.')
    #  return

    curveNode = None
    
    if self.curveNodeID:
      curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
      
    if curveNode == None:
      curveNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      self.curveNodeID = curveNode.GetID()
      #
      # TODO: Save curveNode information
      #

    if curveNode == None:
      print('updateCatheter(): Error - Could not create a curve node')
      return
    
    prevState = curveNode.StartModify()

    nCoils = len(self.activeCoils)
    
    # Update time stamp
    ## TODO: Ideally, the time stamp should come from the data source rather than 3D Slicer.
    curveNode.SetAttribute('MRTracking.lastTS', '%f' % self.lastTS)
    
    nActiveCoils = sum(self.activeCoils)
    
    if curveNode.GetNumberOfControlPoints() != nActiveCoils:
      curveNode.RemoveAllControlPoints()
      for i in range(nActiveCoils):
        p = vtk.vtkVector3d()
        p.SetX(0.0)
        p.SetY(0.0)
        p.SetZ(0.0)
        curveNode.AddControlPoint(p, "P_%d" % i)

    lastCoil = nCoils - 1
    fFlip = (not self.coilOrder)
    egramPoint = None;
      
    j = 0
    for i in range(nCoils):
      if self.activeCoils[i]:
        tnode = self.filteredTransformNodes[i]
        trans = tnode.GetTransformToParent()
        v = trans.GetPosition()
        
        # Apply the registration transform, if activated. (GUI is defined in registration.py)
        if self.registration and self.registration.applyTransform and (self.registration.applyTransform.catheterID == self.catheterID):
          if self.registration.registrationTransform:
            v = self.registration.registrationTransform.TransformPoint(v)

        coilID = j
        if fFlip:
          coilID = nActiveCoils - j - 1
        curveNode.SetNthControlPointPosition(coilID, v[0] * self.axisDirections[0], v[1] * self.axisDirections[1], v[2] * self.axisDirections[2])
        if coilID == 0:
          egramPoint = v;
          
        j += 1

    curveNode.EndModify(prevState)
    
    self.updateCatheter()

    # Egram data
    if (egramPoint != None) and (self.pointRecording == True):
      p = numpy.array(egramPoint)
      d = numpy.linalg.norm(p-self.prevRecordedPoint)
      if d > self.pointRecordingDistance:
        self.prevRecordedPoint = p
        #egram = self.getEgramData(index)
        (egramHeader, egramTable) = self.getEgramData()
        # TODO: Make sure if the following 'flip' is correctly working
        if fFlip:
          egramTable.reverse()

        prMarkupsNode = self.pointRecordingMarkupsNode
        if prMarkupsNode:
          id = prMarkupsNode.AddFiducial(egramPoint[0] * self.axisDirections[0], egramPoint[1] * self.axisDirections[1], egramPoint[2] * self.axisDirections[2])
          #prMarkupsNode.SetNthControlPointDescription(id, '%f' % egram[0])
          mask = self.activeCoils
          if fFlip:
            mask.reverse()
          # Find the first active coil
          # TODO: Make sure that this is correct
          ch = 0
          for a in mask:
            if a:
              break
            ch = ch + 1
          if ch >= len(mask) or ch >= len(egramTable):
            print('Error: no active channel. ch = ' + str(ch))
          egramValues = egramTable[ch]
          desc = None
          for v in egramValues:
            if desc:
              desc = desc + ',' + str(v)
            else:
              desc = str(v)
          prMarkupsNode.SetNthControlPointDescription(id, desc)

          # If the header is not registered to the markup node, do it now
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
      curveDisplayNode.SetHandlesInteractive(False)
      #curveDisplayNode.OccludedVisibilityOff()
      #curveDisplayNode.OutlineVisibilityOff()
      curveDisplayNode.EndModify(prevState)

    # Update models for the coils
    # Coil models
    nCoils =  curveNode.GetNumberOfControlPoints()
    nNodes = len(self.coilModelNodes)
    
    if nNodes != nCoils:
      
      # Remove nodes
      for i in range(0, nNodes):
        slicer.mrmlScene.RemoveNode(self.coilModelNodes[i])
        slicer.mrmlScene.RemoveNode(self.coilTransformNodes[i])
        slicer.mrmlScene.RemoveNode(self.coilPolyObjs[i])
        
      self.coilModelNodes = []
      self.coilTransformNodes = []
      self.coilPolyObjs = []

      for i in range(0, nCoils):
        n = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
        n.SetName(curveNode.GetName() + '-Coil-' + str(i))
        self.coilModelNodes.append(n)
        
        t = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
        t.SetName(curveNode.GetName() + '-Coil-' + str(i) + 'Trans')
        self.coilTransformNodes.append(t)
        
        self.coilPolyObjs.append(vtk.vtkPolyData())

        
    for i in range(0, nCoils):
      matrix = vtk.vtkMatrix4x4()

      n10 = [0.0, 0.0, 0.0]
      p0  = [0.0, 0.0, 0.0]
      cpi = curveNode.GetCurvePointIndexFromControlPointIndex(i)
      
      curveNode.GetNthControlPointPosition(i, p0)
      curveNode.GetCurvePointToWorldTransformAtPointIndex(cpi, matrix)
      n10[0] = matrix.GetElement(0, 2)
      n10[1] = matrix.GetElement(1, 2)
      n10[2] = matrix.GetElement(2, 2)
      
      # The sign for the normal vector is '-' because the normal vector point toward points
      # with larger indecies.
      ps = numpy.array(p0) - numpy.array(n10) * self.coilLength/2.0
      pe = numpy.array(p0) + numpy.array(n10) * self.coilLength/2.0

      self.updateCoilModelNode(self.coilModelNodes[i], self.coilPolyObjs[i], ps, pe, self.radius*1.5, [0.7, 0.7, 0.7], self.opacity)
      
    
    # Add a extended tip
    # make sure that there is more than one points
    if curveNode.GetNumberOfControlPoints() < 2:
      return

    #
    # TODO: the tip model should be managed in a seprate class. 
    #
    if self.tipPoly==None:
      self.tipPoly = vtk.vtkPolyData()
    
    if self.tipModelNode == None:
      self.tipModelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
      self.tipModelNode.SetName('Tip')
      curveNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.tipModel', self.tipModelNode.GetID())
      
        
    if self.tipTransformNode == None:
      self.tipTransformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
      self.tipTransformNode.SetName('TipTransform')
      curveNode.SetAttribute('MRTracking.' + str(self.catheterID) + '.tipTransform', self.tipTransformNode.GetID())

    ## The 'curve end point matrix' (normal vectors + the curve end position)
    matrix = vtk.vtkMatrix4x4()
    
    ## Assuming that the tip is at index=0 
    n10 = [0.0, 0.0, 0.0]
    p0  = [0.0, 0.0, 0.0]
    cpi = curveNode.GetCurvePointIndexFromControlPointIndex(0)

    curveNode.GetNthControlPointPosition(0, p0)
    curveNode.GetCurvePointToWorldTransformAtPointIndex(cpi, matrix)
    n10[0] = matrix.GetElement(0, 2)
    n10[1] = matrix.GetElement(1, 2)
    n10[2] = matrix.GetElement(2, 2)

    # Tip location
    # The sign for the normal vector is '-' because the normal vector point toward points
    # with larger indecies.
    pe = numpy.array(p0) - numpy.array(n10) * self.tipLength
  
    self.updateTipModelNode(self.tipModelNode, self.tipPoly, p0, pe, self.radius, self.modelColor, self.opacity)

    ## Update the 'catheter tip matrix' (normal vectors + the catheter tip position)
    ## Note that the catheter tip matrix is different from the curve end matrix
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    self.tipTransformNode.SetMatrixTransformToParent(matrix)
    
    #matrix = vtk.vtkMatrix4x4()
    #matrix.DeepCopy((t[0], s[0], n10[0], pe[0],
    #                 t[1], s[1], n10[1], pe[1],
    #                 t[2], s[2], n10[2], pe[2],
    #                 0, 0, 0, 1))


  def updateCoilModelNode(self, coilModelNode, poly, ps, pe, radius, color,  opacity):
    
    #coilModelNodes[i], selfcoilPolyObjs[i], ps, pe, self.radius*1.2, [0.2, 0.2, 0.2], self.opacity)
    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    points.SetNumberOfPoints(2)
    cellArray.InsertNextCell(2)
    
    points.SetPoint(0, ps)
    cellArray.InsertCellPoint(0)
    points.SetPoint(1, pe)
    cellArray.InsertCellPoint(1)

    poly.Initialize()
    poly.SetPoints(points)
    poly.SetLines(cellArray)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetInputData(poly)
    tubeFilter.SetRadius(radius)
    tubeFilter.SetNumberOfSides(20)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(tubeFilter.GetOutput())
    else:
      apd.AddInputConnection(tubeFilter.GetOutputPort())
    apd.Update()
    
    coilModelNode.SetAndObservePolyData(apd.GetOutput())
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

    
  def updateTipModelNode(self, tipModelNode, poly, p0, pe, radius, color, opacity):
    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    points.SetNumberOfPoints(2)
    cellArray.InsertNextCell(2)
    
    points.SetPoint(0, p0)
    cellArray.InsertCellPoint(0)
    points.SetPoint(1, pe)
    cellArray.InsertCellPoint(1)

    poly.Initialize()
    poly.SetPoints(points)
    poly.SetLines(cellArray)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetInputData(poly)
    tubeFilter.SetRadius(radius)
    tubeFilter.SetNumberOfSides(20)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius)
    sphere.SetCenter(pe)
    sphere.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tubeFilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tubeFilter.GetOutputPort())
    apd.Update()
    
    tipModelNode.SetAndObservePolyData(apd.GetOutput())
    tipModelNode.Modified()

    tipDispID = tipModelNode.GetDisplayNodeID()
    if tipDispID == None:
      tipDispNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
      tipDispNode.SetScene(slicer.mrmlScene)
      tipModelNode.SetAndObserveDisplayNodeID(tipDispNode.GetID());
      tipDispID = tipModelNode.GetDisplayNodeID()
      
    tipDispNode = slicer.mrmlScene.GetNodeByID(tipDispID)

    prevState = tipDispNode.StartModify()
    tipDispNode.SetColor(color)
    tipDispNode.SetOpacity(opacity)
    #tipDispNode.SliceIntersectionVisibilityOn()
    tipDispNode.Visibility2DOn()
    tipDispNode.SetSliceDisplayModeToIntersection()
    tipDispNode.EndModify(prevState)

            
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

  
  def setTipLength(self, length):
    
    self.tipLength= length
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.tipLength.0" % self.name, str(self.tipLength))
      return 1
    return 0


  def setCoilPosition(self, position):

    self.coilPositions = position
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.coilPosition.%s" % self.name, str(self.coilPositions))
      return 1
    return 0


  def setTipModelNode(self, node):

    if node == None:
      return 0
    
    self.tipModelNode = node
    return 1
    #if self.logic:
    #  self.logic.getParameterNode().SetParameter("TD.%s.tipModelNode.%s" % (self.name), node.GetID())
    #  return 1
    #return 0

  
  def setTipTransformNode(self, node):
      
    if node == None:
      return 0
    
    self.tipTransformNode = node
    return 1
    #if self.logic:
    #  self.logic.getParameterNode().SetParameter("TD.%s.tipTransformNode.%s" % (self.name), node.GetID())
    #  return 1
    #return 0

  
  #self.tipPoly = [None, None]
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
  
  
  def getInterpolatedFiducialPoints(self, distFromTip):
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
    # Unlike getRegistrationFiducialNode(), getInterpolatedFiducialPoints() can be used to
    # calculate intermediate points between the tracking sensors.
    # The reason to have the mask is that the coordinates of the points cannot be computed by interpolation,
    # if, for example, the point given by 'distFromTip' is not in between two coils.
    #

    if self.curveNodeID == None:
      return (None, None)
    
    curveNode = slicer.mrmlScene.GetNodeByID(self.curveNodeID)
    if curveNode == None:
      return (None, None)
    
    numpy.array([0.0, 0.0, 0.0])
    cpos = numpy.array(self.coilPositions)
    interval = cpos[1:] - cpos[:-1]
    trans = vtk.vtkMatrix4x4()

    mask = []
    posList = []
    upperIndexLimit = curveNode.GetNumberOfControlPoints() - 2
    
    for d in distFromTip:
      pos = [0.0]*3

      # The following gives the index of the lower end of the segment that includes 'd':
      s = numpy.sum(d >= cpos) - 1

      # Out of range
      if s < 0 or s > upperIndexLimit:
        posList.append(pos)
        mask.append(False)
        continue
      
      p0 = curveNode.GetCurvePointIndexFromControlPointIndex(s)
      p1 = curveNode.GetCurvePointIndexFromControlPointIndex(s+1)
      clen = curveNode.GetCurveLengthBetweenStartEndPointsWorld(p0, p1)
      a = d - cpos[s]
      b = interval[s]
      pindexm =  curveNode.GetCurvePointIndexAlongCurveWorld(p0, clen * a / b)
      if pindexm >= 0:
        curveNode.GetCurvePointToWorldTransformAtPointIndex(pindexm, trans)
        pos[0] = trans.GetElement(0, 3)
        pos[1] = trans.GetElement(1, 3)
        pos[2] = trans.GetElement(2, 3)
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
      
      self.tipLength = self.getParamFloat("TD.%s.tipLength.0" % self.name, self.tipLength)
      
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
    self.parameterNode.SetParameter("TD.%s.tipLength" % (tipLength), str(self.tipLenngth))
    

  def loadParameters(self, parameterNode):
    pass


  
