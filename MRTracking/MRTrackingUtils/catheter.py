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
from qt import QObject, Signal, Slot
import slicer
import numpy
import vtk


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
    print('CatheterCollection is initiated.')

    
  def add(self, cath):

    self.catheterList.append(cath)
    self.catheterID = self.lastID
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

  def __init__(self, name='Cath'):

    self.MAX_CATHETERS = 2
    self.MAX_COILS = 8
    
    #slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.name = name
    self.catheterID = None
    self.trackingDataNodeID = ''           # Tracking node ID associated with this catheter.
    self.logic = None
    self.widget = None
    self.eventTag = ''

    self.curveNodeID = ''  # TODO: Is this needed?
    self.lastMTime = 0
    
    # Tip model
    self.tipModelNode = None      # TODO: The node ID is saved in Tracking Data Node
    self.tipTransformNode = None  # TODO: The node ID is saved in Tracking Data Node
    self.tipPoly = None

    # Coil configulation
    self.tipLength = 10.0
    self.coilPositions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.activeCoils = [True, True, True, True, False, False, False, False]
    self.showCoilLabel = False
    self.coilOrder = True

    # Egram data
    self.egramDataNode = None

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
    self.transformProcessorNodes = [None] * self.MAX_COILS
    self.filteredTransformNodes = [None] * self.MAX_COILS
    
    # Registration
    self.registration = None

    ## Default values for self.coilPositions:
    self.defaultCoilPositions = {}
    self.defaultCoilPositions['"NavX-Ch0"'] = [0,20,40,60]
    self.defaultCoilPositions['"NavX-Ch1"'] = [0,20,40,60]
    self.defaultCoilPositions['"WWTracker"'] = [10,30,50,70]


  def __del__(self):
    print("Catheter.__del__() is called.")

  def setName(self, name):
    self.name = name
    
  def setID(self, id):
    self.trackingDataNodeID = id

  def setTrackingDataNodeID(self, id):
    self.setID(id)

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
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        # Create transform nodes for filtered tracking data
        self.setFilteredTransforms(tdnode, self.activeCoils)

        ## TODO: Using the first node to trigger the event may cause a timing issue.
        ## TODO: Using the filtered transform node will invoke the event handler every 15 ms as fixed in
        ##       TrackerStabilizer module. It is not guaranteed that every tracking data is used when
        ##       the tracking frame rate is higher than 66.66 fps (=1000ms/15ms). 
        #childNode = tdnode.GetTransformNode(0)
        childNode = td.filteredTransformNodes[0]
        
        childNode.SetAttribute('MRTracking.' + self.catheterID + '.parent', tdnode.GetID())
        td.eventTag = childNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        print("Observer for TrackingDataBundleNode added.")
        return True
      else:
        return False  # Could not add observer.


  def deactivateTracking(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.trackingDataNodeID)
    
    if tdnode:
      if tdnode.GetNumberOfTransformNodes() > 0 and td.eventTag != '':
        childNode = tdnode.GetTransformNode(0)
        childNode.RemoveObserver(td.eventTag)
        td.eventTag = ''
        return True
      else:
        return False

      
      
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
        filteredNodeID = str(inputNode.GetAttribute('MRTracking.filteredNode'))
        if filteredNodeID != '':
          self.filteredTransformNodes[i] = slicer.mrmlScene.GetNodeByID(filteredNodeID)
          
        if self.filteredTransformNodes[i] == None and createNew:
          self.filteredTransformNodes[i] = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
          inputNode.SetAttribute('MRTracking.filteredNode', self.filteredTransformNodes[i].GetID())
          
      if self.transformProcessorNodes[i] == None:
        processorNodeID = str(inputNode.GetAttribute('MRTracking.processorNode'))
        if processorNodeID != '':
          self.transformProcessorNodes[i] = slicer.mrmlScene.GetNodeByID(processorNodeID)
        if self.transformProcessorNodes[i] == None and createNew:
          self.transformProcessorNodes[i] = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformProcessorNode')
          inputNode.SetAttribute('MRTracking.processorNode', self.transformProcessorNodes[i].GetID())

      if self.filteredTransformNodes[i]:
        self.filteredTransformNodes[i].SetName(inputNode.GetName() + '_filtered')
        
      if self.transformProcessorNodes[i]:
        self.transformProcessorNodes[i].SetName(inputNode.GetName() + '_processor')
        tpnode = self.transformProcessorNodes[i]
        tpnode.SetProcessingMode(slicer.vtkMRMLTransformProcessorNode.PROCESSING_MODE_STABILIZE)
        tpnode.SetStabilizationCutOffFrequency(7.50)
        tpnode.SetStabilizationEnabled(1)
        tpnode.SetUpdateModeToAuto()
        tpnode.SetAndObserveInputUnstabilizedTransformNode(inputNode)
        tpnode.SetAndObserveOutputTransformNode(self.filteredTransformNodes[i])

        
  def onIncomingNodeModifiedEvent(self, caller, event):

    parentID = str(caller.GetAttribute('MRTracking.' + self.catheterID + '.parent'))
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)

    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      # Update coordinates in the fiducial node.
      nCoils = tdnode.GetNumberOfTransformNodes()
      fUpdate = False
      if nCoils > 0:
        # Update timestamp
        # TODO: Should we check all time stamps under the tracking node?
        tnode = tdnode.GetTransformNode(0)
        mTime = tnode.GetTransformToWorldMTime()
        if mTime > td.lastMTime:
          currentTime = time.time()
          td.lastMTime = mTime
          td.lastTS = currentTime
          fUpdate = True
      
      self.updateCatheterNode()

      if fUpdate:
        self.registration.updatePoints()


  def updateCatheterNode(self):

    tdnode = slicer.mrmlScene.GetNodeByID(self.trackingDataNodeID)
    if tdnode == None:
      print('updateCatheter(): Error - no TrackingDataNode.')
      return
    
    curveNodeID = str(tdnode.GetAttribute('MRTracking.' + self.catheterID + '.CurveNode%d'))
    curveNode = None
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)

    if curveNode == None:
      curveNode = self.scene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
      tdnode.SetAttribute('MRTracking.' + self.catheterID + '.CurveNode', curveNode.GetID())
    
    prevState = curveNode.StartModify()

    # Update coordinates in the fiducial node.
    nCoils = tdnode.GetNumberOfTransformNodes()
  
    if nCoils > 8: # Max. number of coils is 8.
      nCoils = 8
      
    mask = self.activeCoils[0:nCoils]
    
    # Update time stamp
    ## TODO: Ideally, the time stamp should come from the data source rather than 3D Slicer.
    curveNode.SetAttribute('MRTracking.' + self.catheterID + '.lastTS', '%f' % td.lastTS)
    
    nActiveCoils = sum(mask)
    
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
      if mask[i]:
        tnode = self.filteredTransformNodes[i]
        trans = tnode.GetTransformToParent()
        v = trans.GetPosition()
        
        # Apply the registration transform, if activated. (GUI is defined in registration.py)
        if self.registration and self.registration.applyTransform and (self.registration.applyTransform.GetID() == tdnode.GetID()):
          if self.registration.registrationTransform:
            v = self.registration.registrationTransform.TransformPoint(v)

        coilID = j
        if fFlip:
          coilID = lastCoil - j
        curveNode.SetNthControlPointPosition(coilID, v[0] * td.axisDirections[0], v[1] * td.axisDirections[1], v[2] * td.axisDirections[2])
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
            print('Error: no active channel. ch = ' + ch)
          egramValues = egramTable[ch]
          desc = None
          for v in egramValues:
            if desc:
              desc = desc + ',' + str(v)
            else:
              desc = str(v)
          prMarkupsNode.SetNthControlPointDescription(id, desc)

          # If the header is not registered to the markup node, do it now
          ev = prMarkupsNode.GetAttribute('MRTracking.' + self.catheterID + '.EgramParamList')
          if ev == None:
            attr= None
            for eh in egramHeader:
              if attr:
                attr = attr + ',' + str(eh)
              else:
                attr = str(eh)
            prMarkupsNode.SetAttribute('MRTracking.' + self.catheterID + '.EgramParamList', attr)
            prMarkupsNode.Modified();


  def updateCatheter(self):

    tdnode = slicer.mrmlScene.GetNodeByID(self.trackingDataNodeID)
    if tdnode == None:
      print('updateCatheter(): Error - no TrackingDataNode.')
      return
    
    curveNode = None
    curveNodeID = str(tdnode.GetAttribute('MRTracking.' + self.catheterID + '.CurveNode%d'))
    if curveNodeID != None:
      curveNode = self.scene.GetNodeByID(curveNodeID)

    if curveNode == None:
      return

    curveDisplayNode = curveNode.GetDisplayNode()
    if curveDisplayNode:
      prevState = curveDisplayNode.StartModify()
      curveDisplayNode.SetSelectedColor(self.modelColor)
      curveDisplayNode.SetColor(self.modelColor)
      curveDisplayNode.SetOpacity(self.opacity)
      #curveDisplayNode.SliceIntersectionVisibilityOn()
      curveDisplayNode.Visibility2DOn()
      curveDisplayNode.EndModify(prevState)
      # Show/hide labels for coils
      curveDisplayNode.SetPointLabelsVisibility(self.showCoilLabel);
      curveDisplayNode.SetUseGlyphScale(False)
      curveDisplayNode.SetGlyphSize(self.radius*4.0)
      curveDisplayNode.SetLineThickness(0.5)  # Thickness is defined as a scale from the glyph size.
    
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
      self.tipModelNode = self.scene.AddNewNodeByClass('vtkMRMLModelNode')
      self.tipModelNode.SetName('Tip')
      tdnode.SetAttribute('MRTracking.' + self.catheterID + '.tipModel%d', self.tipModelNode.GetID())
        
    if self.tipTransformNode == None:
      self.tipTransformNode = self.scene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
      self.tipTransformNode.SetName('TipTransform')
      tdnode.SetAttribute('MRTracking.' + self.catheterID + '.tipTransform', self.tipTransformNode.GetID())

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
    sphere.SetRadius(radius*2.0)
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
      tipDispNode = self.scene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
      tipDispNode.SetScene(self.scene)
      tipModelNode.SetAndObserveDisplayNodeID(tipDispNode.GetID());
      tipDispID = tipModelNode.GetDisplayNodeID()
      
    tipDispNode = self.scene.GetNodeByID(tipDispID)

    prevState = tipDispNode.StartModify()
    tipDispNode.SetColor(color)
    tipDispNode.SetOpacity(opacity)
    #tipDispNode.SliceIntersectionVisibilityOn()
    tipDispNode.Visibility2DOn()
    tipDispNode.SetSliceDisplayModeToIntersection()
    tipDispNode.EndModify(prevState)

            
  #--------------------------------------------------
  # Data I/O
  #
    
  def loadDefaultConfig(self):
    self.loadDefaultCoilConfigulation()
    self.loadDefaultAxisDirections()
    self.loadDefaultVisualSettings()
    

  def loadDefaultCoilConfigulation(self):

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
      
          
  def saveDefaultConfig(self):
    
    self.saveDefaultCoilConfigulation()
    self.saveDefaultAxisDirections()
    self.saveDefaultVisualSettings()

    
  def saveDefaultCoilConfigulation(self):
    
    #name = tdnode.GetName()
    settings = qt.QSettings()
    
    settings.setValue(self.logic.widget.moduleName + '/' + 'ShowCoilLabel.' + str(self.name), self.showCoilLabel)
    
    value = [int(b) for b in self.activeCoils]
    settings.setValue(self.logic.widget.moduleName + '/' + 'ActiveCoils.' + str(self.name) + '.0', value)
    settings.setValue(self.logic.widget.moduleName + '/' + 'CoilPositions.' + str(self.name) + '.0', self.coilPositions)
    
    settings.setValue(self.logic.widget.moduleName + '/' + 'TipLength.' + str(self.name) + '.0', self.tipLength)
    settings.setValue(self.logic.widget.moduleName + '/' + 'CoilOrder.' + str(self.name) + '.0', int(self.coilOrder))

      
  def saveDefaultAxisDirections(self):
    
    #name = tdnode.GetName()
    settings = qt.QSettings()
    settings.setValue(self.logic.widget.moduleName + '/' + 'AxisDirections.' + str(self.name), self.axisDirections)
    

  def saveDefaultVisualSettings(self):
    
    #name = tdnode.GetName()
    settings = qt.QSettings()
    
    settings.setValue(self.logic.widget.moduleName + '/' + 'Opacity.' + str(self.name) + '.0', self.opacity)
    settings.setValue(self.logic.widget.moduleName + '/' + 'Radius.' + str(self.name) + '.0', self.radius)
    settings.setValue(self.logic.widget.moduleName + '/' + 'ModelColor.' + str(self.name) + '.0', self.modelColor)


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

    
  #def getEgramData(self, cath):
  #
  #  r = []
  #  
  #  if self.egramDataNode[cath]:
  #    text = self.egramDataNode[cath].GetText()
  #    list = text.split(',')
  #  
  #    for v in list:
  #      r.append(float(v))
  #      
  #  return r

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
    if self.egramDataNode:
      text = self.egramDataNode.GetText()
      for line in text.splitlines():
        cols = line.split(',')
        if header == None:
          header = cols
        else:
          values = [float(s) for s in cols]
          table.append(values)
        
    return (header, table)

      
    
      
    
