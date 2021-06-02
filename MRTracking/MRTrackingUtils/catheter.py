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

class CatheterCollection(QObject):

  updateCatheter = Signal()
  
  def __init__(self):

    self.catheterList = []

    
  def add(self, cath):
      
    if isinstance(cath, Catheter):
      self.catheterList.append(cath)

    self.updateCatheter.emit()


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
    self.ID = ''           # Tracking node ID associated with this catheter.
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

    
  def saveParameters(self, trackingDataName, parameterNode):

    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius))
    self.parameterNode.SetParameter("TD.%s.radius" % (trackingDataName), str(self.radius))
    self.parameterNode.SetParameter("TD.%s.modelColor" % (trackingDataName), str(self.modelColor))
    self.parameterNode.SetParameter("TD.%s.tipLength" % (tipLength), str(self.tipLenngth))
    

  def loadParameters(self, parameterNode):
    pass


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

      
    
      
    
