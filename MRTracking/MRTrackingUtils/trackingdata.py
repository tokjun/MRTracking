#------------------------------------------------------------
#
# TrakcingData class
#

class TrackingData:

  def __init__(self):

    self.MAX_CATHETERS = 2
    self.MAX_COILS = 8
    
    #slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.ID = ''
    self.logic = None
    self.widget = None
    self.eventTag = ''

    # self.activeTrackingDataNodeID = ''

    self.curveNodeID = ''  # TODO: Is this needed?
    
    self.opacity = [1.0, 1.0]
    self.radius = [0.5, 0.5]
    self.modelColor = [[0.0, 0.0, 1.0], [1.0, 0.359375, 0.0]]

    # Filtering
    self.transformProcessorNodes = [None] * self.MAX_COILS
    self.filteredTransformNodes = [None] * self.MAX_COILS
    

    # Tip model
    self.tipLength = [10.0, 10.0]
    self.coilPositions = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    self.tipModelNode = [None, None]  # TODO: The node ID is saved in Tracking Data Node
    self.tipTransformNode = [None, None]  # TODO: The node ID is saved in Tracking Data Node
    self.tipPoly = [None, None]
    self.showCoilLabel = False
    self.activeCoils = [[False, False, False, False, True, True, True, True], [True, True, True, True, False, False, False, False]]

    # Coil order (True if Distal -> Proximal)
    self.coilOrder = [True, True]
    
    self.axisDirection = [1.0, 1.0, 1.0]
    
    self.lastMTime = 0

    
  def setID(self, id):
    self.ID = id


  def setLogic(self, logic):
    self.logic = logic

  def isActive(self):
    if self.eventTag == '':
      return False
    else:
      return True

    
  def setCurveNodeID(self, id):
    
    self.curveNodeID = id
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.curveNodeID" % self.ID, id)
      return 1
    return 0


  def setOpacity(self, index, opacity):
    
    self.opacity[index] = opacity

    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.opacity.%s" % (self.ID, index), str(self.opacity[index]))
      return 1
    return 0
    

  def setRadius(self, index, r):

    self.radius[index] = r
    
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.radius.%s" % (self.ID, index), str(self.radius[index]))
      return 1
    return 0


  def setModelColor(self, index, color):
    
    self.color[index] = color
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.modelColor.%s" % (self.ID, index), str(self.color[index]))
      return 1
    return 0

  
  def setTipLength(self, index, length):
    
    self.tipLength[index] = length
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.tipLength.%s" % (self.ID, index), str(self.tipLength[index]))
      return 1
    return 0


  def setCoilPosition(self, index, position):

    self.coilPositions[index] = position
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.coilPosition.%s" % (self.ID, index), str(self.coilPositions[index]))
      return 1
    return 0


  def setTipModelNode(self, index, node):
    
    self.tipModelNode[index] = node
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.tipModelNode.%s" % (self.ID, index), node.GetID())
      return 1
    return 0

  
  def setTipTransformNode(self, index, node):
      
    self.tipTransformNode[index] = node
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.tipTransformNode.%s" % (self.ID, index), node.GetID())
      return 1
    return 0

  
  #self.tipPoly = [None, None]
  def setShowCoilLabel(self, s):
    
    self.showCoilLabel = s
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.showCoilLabel" % self.ID, str(self.showCoilLabel))
      return 1
    return 0

  
  def setActiveCoils(self, index, coils):
    
    self.activeCoils[index] = coils
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.activeCoils.%s" % (self.ID, index), str(self.activeCoils[index]))
      return 1
    return 0

  
  def setCoilOrder(self, index, s):
    # Coil order (True if Distal -> Proximal)
    
    self.coilOrder[index] = s
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.coilOrder.%s" % (self.ID, index), str(self.coilOrder[index]))
      return 1
    return 0

  
  def setAxisDirection(self, dir, sign):
    # dir: 0 = x, 1 = y, 2 = z

    self.axisDirection[dir] = sign
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.axisDirection.%s" % (self.ID, dir), str(self.axisDirection[dir]))
      return 1
    return 0

    
  def saveParameters(self, trackingDataName, parameterNode):

    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius[0]))
    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius[0]))
    self.parameterNode.SetParameter("TD.%s.modelColor" % (trackingDataName), str(self.modelColor))
    self.parameterNode.SetParameter("TD.%s.modelColor" % (tipLength), str(self.tipLenngth))
    
  def loadParameters(self, parameterNode):
    pass
