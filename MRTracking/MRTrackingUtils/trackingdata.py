#------------------------------------------------------------
#
# TrakcingData class
#

import qt
import slicer

class TrackingData:

  def __init__(self):

    self.MAX_CATHETERS = 2
    self.MAX_COILS = 8
    
    #slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.ID = ''
    self.logic = None
    self.widget = None
    self.eventTag = ''

    self.curveNodeID = ''  # TODO: Is this needed?
    self.lastMTime = 0
    
    # Tip model
    self.tipModelNode = [None, None]      # TODO: The node ID is saved in Tracking Data Node
    self.tipTransformNode = [None, None]  # TODO: The node ID is saved in Tracking Data Node
    self.tipPoly = [None, None]

    # Coil configulation
    self.tipLength = [10.0, 10.0]
    self.coilPositions = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    self.activeCoils = [[True, True, True, True, False, False, False, False], [False, False, False, False, True, True, True, True]]
    self.showCoilLabel = False
    self.coilOrder = [True, True]

    # Coordinate system
    self.axisDirections = [1.0, 1.0, 1.0]
    
    # Visual settings
    self.opacity = [1.0, 1.0]
    self.radius = [0.5, 0.5]
    self.modelColor = [[0.0, 0.0, 1.0], [1.0, 0.359375, 0.0]]

    # Filtering
    self.transformProcessorNodes = [None] * self.MAX_COILS
    self.filteredTransformNodes = [None] * self.MAX_COILS

    ## Default values for self.coilPositions:
    self.defaultCoilPositions = {}
    self.defaultCoilPositions['"NavX-Ch0"'] = [[0,20,40,60],[0,20,40,60]]
    self.defaultCoilPositions['"NavX-Ch1"'] = [[0,20,40,60],[0,20,40,60]]
    self.defaultCoilPositions['"WWTracker"'] = [[10,30,50,70],[10,30,50,70]]


  def __del__(self):
    print("TrackingData.__del__() is called.")
    
    
  def setID(self, id):
    self.ID = id


  def setLogic(self, logic):
    self.logic = logic

    
  def isActive(self):
    if self.eventTag == '':
      return False
    else:
      return True

    
  def loadDefaultConfig(self):
    self.loadDefaultCoilConfigulation()
    self.loadDefaultAxisDirections()
    self.loadDefaultVisualSettings()
    

  def loadDefaultCoilConfigulation(self):

    tdnode = slicer.mrmlScene.GetNodeByID(self.ID)
    if not tdnode:
      return

    ## Load config
    settings = qt.QSettings()
    setting = []
    name = tdnode.GetName()
    
    for index in range(2):
      # Coil positions
      setting = settings.value(self.logic.widget.moduleName + '/' + 'CoilPositions.' + str(name) + '.' + str(index))
      array = []
      if setting != None:
        print('Found ' + str(name) + '.' + str(index) + ' in Setting')
        array = [float(f) for f in setting]
      else:
        if name in self.defaultCoilPositions:
          print('Found ' + str(name) + '.' + str(index) + ' in Default Config List')
          array = self.defaultCoilPositions[name][index]
          
      if len(array) > 0:
        try:
          #self.setCoilPositions(index, array)
          if len(array) <= len(self.coilPositions[index]):
            self.coilPositions[index] = array
        except ValueError:
          print('Format error in coilConfig string.')

      # Active coils
      setting = settings.value(self.logic.widget.moduleName + '/' + 'ActiveCoils.' + str(name) + '.' + str(index))
      if setting != None:
        array = [bool(int(i)) for i in setting]
        
        if len(array) > 0:
          try:
            if len(array) <= len(self.activeCoils[index]):
              self.activeCoils[index] = array
          except ValueError:
            print('Format error in activeCoils string.')
          
          
  def loadDefaultAxisDirections(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.ID)
    if not tdnode:
      return

    ## Load config
    settings = qt.QSettings()
    setting = []
    name = tdnode.GetName()

    setting = settings.value(self.logic.widget.moduleName + '/' + 'AxisDirections.' + str(name))
    if setting != None:
      self.axisDirections = [float(s) for s in setting]

    
  def loadDefaultVisualSettings(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.ID)
    if not tdnode:
      return

    ## Load config
    settings = qt.QSettings()
    setting = []
    name = tdnode.GetName()

    for index in range(2):

      setting = settings.value(self.logic.widget.moduleName + '/' + 'Opacity.' + str(name) + '.' + str(index))
      if setting != None:
        self.opacity[index] = float(setting)
        
      setting = settings.value(self.logic.widget.moduleName + '/' + 'Radius.' + str(name) + '.' + str(index))
      if setting != None:
        self.radius[index] = float(setting)

      setting = settings.value(self.logic.widget.moduleName + '/' + 'ModelColor.' + str(name) + '.' + str(index))
      if setting != None:
        self.modelColor[index] = [float(s) for s in setting]
      
          
  def saveDefaultConfig(self):
    
    self.saveDefaultCoilConfigulation()
    self.saveDefaultAxisDirections()
    self.saveDefaultVisualSettings()

    
  def saveDefaultCoilConfigulation(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.ID)
    if not tdnode:
      return

    name = tdnode.GetName()
    settings = qt.QSettings()
    
    settings.setValue(self.logic.widget.moduleName + '/' + 'ShowCoilLabel.' + str(name), self.showCoilLabel)
    
    for index in range(2):
      value = [int(b) for b in self.activeCoils[index]]
      settings.setValue(self.logic.widget.moduleName + '/' + 'ActiveCoils.' + str(name) + '.' + str(index), value)
      settings.setValue(self.logic.widget.moduleName + '/' + 'CoilPositions.' + str(name) + '.' + str(index), self.coilPositions[index])
      
      settings.setValue(self.logic.widget.moduleName + '/' + 'TipLength.' + str(name) + '.' + str(index), self.tipLength[index])
      settings.setValue(self.logic.widget.moduleName + '/' + 'CoilOrder.' + str(name) + '.' + str(index), int(self.coilOrder[index]))

      
  def saveDefaultAxisDirections(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.ID)
    if not tdnode:
      return

    name = tdnode.GetName()
    settings = qt.QSettings()
    settings.setValue(self.logic.widget.moduleName + '/' + 'AxisDirections.' + str(name), self.axisDirections)
    

  def saveDefaultVisualSettings(self):
    
    tdnode = slicer.mrmlScene.GetNodeByID(self.ID)
    if not tdnode:
      return

    name = tdnode.GetName()
    settings = qt.QSettings()
    
    for index in range(2):
      settings.setValue(self.logic.widget.moduleName + '/' + 'Opacity.' + str(name) + '.' + str(index), self.opacity[index])
      settings.setValue(self.logic.widget.moduleName + '/' + 'Radius.' + str(name) + '.' + str(index), self.radius[index])
      settings.setValue(self.logic.widget.moduleName + '/' + 'ModelColor.' + str(name) + '.' + str(index), self.modelColor[index])
    

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

    if node == None:
      return 0
    
    self.tipModelNode[index] = node
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.tipModelNode.%s" % (self.ID, index), node.GetID())
      return 1
    return 0

  
  def setTipTransformNode(self, index, node):
      
    if node == None:
      return 0
    
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

    self.axisDirections[dir] = sign
    if self.logic:
      self.logic.getParameterNode().SetParameter("TD.%s.axisDirection.%s" % (self.ID, dir), str(self.axisDirections[dir]))
      return 1
    return 0

    
  def saveParameters(self, trackingDataName, parameterNode):

    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius[0]))
    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius[0]))
    self.parameterNode.SetParameter("TD.%s.modelColor" % (trackingDataName), str(self.modelColor))
    self.parameterNode.SetParameter("TD.%s.tipLength" % (tipLength), str(self.tipLenngth))
    

  def loadParameters(self, parameterNode):
    pass
