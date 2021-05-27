import ctk
import qt
import slicer
import vtk
import numpy
from scipy.interpolate import Rbf
#from scipy.interpolate import griddata

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingSurfaceMapping():

  def __init__(self, label="SurfaceMapping"):

    self.label = label
    self.mrTrackingLogic = None
    self.nCath = 2
    self.cath = 0
    self.currentTrackingDataNode = None
    self.scalarBarWidget = None
    self.lookupTable = None
    self.defaultEgramValueRange = [0.0, 20.0]

  def buildGUI(self, parent):

    mappingLayout = qt.QFormLayout(parent)
    
    # Tracking node selector
    self.mappingTrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.mappingTrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.mappingTrackingDataSelector.selectNodeUponCreation = True
    self.mappingTrackingDataSelector.addEnabled = True
    self.mappingTrackingDataSelector.removeEnabled = False
    self.mappingTrackingDataSelector.noneEnabled = False
    self.mappingTrackingDataSelector.showHidden = True
    self.mappingTrackingDataSelector.showChildNodeTypes = False
    self.mappingTrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.mappingTrackingDataSelector.setToolTip( "Tracking Data for Reslicing" )
    mappingLayout.addRow("Tracking Data: ", self.mappingTrackingDataSelector)

    self.cathRadioButton = [None] * self.nCath
    self.cathBoxLayout = qt.QHBoxLayout()
    self.cathGroup = qt.QButtonGroup()
    for cath in range(self.nCath):
      self.cathRadioButton[cath] = qt.QRadioButton("Cath %d" % cath)
      if cath == self.cath:
        self.cathRadioButton[cath].checked = 0
      self.cathBoxLayout.addWidget(self.cathRadioButton[cath])
      self.cathGroup.addButton(self.cathRadioButton[cath])

    self.egramRecordPointsSelector = slicer.qMRMLNodeComboBox()
    self.egramRecordPointsSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.egramRecordPointsSelector.selectNodeUponCreation = True
    self.egramRecordPointsSelector.addEnabled = True
    self.egramRecordPointsSelector.removeEnabled = False
    self.egramRecordPointsSelector.noneEnabled = True
    self.egramRecordPointsSelector.showHidden = True
    self.egramRecordPointsSelector.showChildNodeTypes = False
    self.egramRecordPointsSelector.setMRMLScene( slicer.mrmlScene )
    self.egramRecordPointsSelector.setToolTip( "Fiducials for recording Egram data" )
    mappingLayout.addRow("Points: ", self.egramRecordPointsSelector)

    self.modelSelector = slicer.qMRMLNodeComboBox()
    self.modelSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.modelSelector.selectNodeUponCreation = True
    self.modelSelector.addEnabled = True
    self.modelSelector.removeEnabled = True
    self.modelSelector.noneEnabled = True
    self.modelSelector.showHidden = True
    self.modelSelector.showChildNodeTypes = False
    self.modelSelector.setMRMLScene( slicer.mrmlScene )
    self.modelSelector.setToolTip( "Surface model node" )
    mappingLayout.addRow("Model: ", self.modelSelector)

    # Minimum interval between two consective points
    self.pointRecordingDistanceSliderWidget = ctk.ctkSliderWidget()
    self.pointRecordingDistanceSliderWidget.singleStep = 0.1
    self.pointRecordingDistanceSliderWidget.minimum = 0.0
    self.pointRecordingDistanceSliderWidget.maximum = 20.0
    self.pointRecordingDistanceSliderWidget.value = 0.0
    #self.minIntervalSliderWidget.setToolTip("")

    mappingLayout.addRow("Min. Distance: ",  self.pointRecordingDistanceSliderWidget)

    self.forceConvexCheckBox = qt.QCheckBox()
    self.forceConvexCheckBox.checked = 0
    self.forceConvexCheckBox.text = "Force convex"
    self.smoothingCheckBox = qt.QCheckBox()
    self.smoothingCheckBox.checked = 1
    self.smoothingCheckBox.text = "Smoothing"

    self.surfaceBoxLayout = qt.QHBoxLayout()
    self.surfaceBoxLayout.addWidget(self.forceConvexCheckBox)
    self.surfaceBoxLayout.addWidget(self.smoothingCheckBox)
    
    mappingLayout.addRow("Surface:", self.surfaceBoxLayout)
    
    activeBoxLayout = qt.QHBoxLayout()
    self.activeGroup = qt.QButtonGroup()
    self.activeOnRadioButton = qt.QRadioButton("ON")
    self.activeOffRadioButton = qt.QRadioButton("Off")
    self.activeOffRadioButton.checked = 1
    activeBoxLayout.addWidget(self.activeOnRadioButton)
    self.activeGroup.addButton(self.activeOnRadioButton)
    activeBoxLayout.addWidget(self.activeOffRadioButton)
    self.activeGroup.addButton(self.activeOffRadioButton)

    mappingLayout.addRow("Active: ", activeBoxLayout)

    self.resetPointButton = qt.QPushButton()
    self.resetPointButton.setCheckable(False)
    self.resetPointButton.text = 'Erase Points'
    self.resetPointButton.setToolTip("Erase all the points recorded for surface mapping.")

    mappingLayout.addRow(" ",  self.resetPointButton)

    self.generateSurfaceButton = qt.QPushButton()
    self.generateSurfaceButton.setCheckable(False)
    self.generateSurfaceButton.text = 'Generate Surface Map'
    self.generateSurfaceButton.setToolTip("Generate a surface model from the collected points.")

    mappingLayout.addRow(" ",  self.generateSurfaceButton)
    
    self.paramSelector = qt.QComboBox()
    self.paramSelector.addItem('None')
    
    mappingLayout.addRow("Egram Param",  self.paramSelector)
    
    self.mapModelButton = qt.QPushButton()
    self.mapModelButton.setCheckable(False)
    self.mapModelButton.text = 'Color Map'
    self.mapModelButton.setToolTip("Map the surface model with Egram Data.")

    mappingLayout.addRow(" ",  self.mapModelButton)

    #-- Color range
    self.colorRangeWidget = ctk.ctkRangeWidget()
    self.colorRangeWidget.setToolTip("Set color range")
    self.colorRangeWidget.setDecimals(2)
    self.colorRangeWidget.singleStep = 0.05
    self.colorRangeWidget.minimumValue = self.defaultEgramValueRange[0]
    self.colorRangeWidget.maximumValue = self.defaultEgramValueRange[1]
    self.colorRangeWidget.minimum = -50.0
    self.colorRangeWidget.maximum = 50.0
    mappingLayout.addRow("Color range: ", self.colorRangeWidget)
    
    self.mappingTrackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onMappingTrackingDataSelected)
    self.egramRecordPointsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onEgramRecordPointsSelected)
    self.modelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onModelSelected)
    self.pointRecordingDistanceSliderWidget.connect("valueChanged(double)", self.pointRecordingDistanceChanged)

    self.forceConvexCheckBox.connect('toggled(bool)', self.onSurfacePropertyChanged)
    self.smoothingCheckBox.connect('toggled(bool)', self.onSurfacePropertyChanged)
    
    self.resetPointButton.connect('clicked(bool)', self.onResetPointRecording)
    self.generateSurfaceButton.connect('clicked(bool)', self.onGenerateSurface)
    
    #self.paramSelector.connect('currentTextChanged(QString)', self.onParamSelected)
    self.mapModelButton.connect('clicked(bool)', self.onMapModel)
    self.colorRangeWidget.connect('valuesChanged(double, double)', self.onUpdateColorRange)
    
    for cath in range(self.nCath):    
      self.cathRadioButton[cath].connect('clicked(bool)', self.onSelectCath)

    self.activeOnRadioButton.connect('clicked(bool)', self.onActive)
    self.activeOffRadioButton.connect('clicked(bool)', self.onActive)

  def setMRTrackingLogic(self, t):
    self.mrTrackingLogic = t

    
  #--------------------------------------------------
  # GUI Slots

  def getTrackingData(self):
    if self.mrTrackingLogic == None:
      return None
    tdnode = self.currentTrackingDataNode
    if tdnode == None:
      return None
    td = self.mrTrackingLogic.TrackingData[tdnode.GetID()]
    return td

  def onMappingTrackingDataSelected(self):
    td = self.getTrackingData()
    if td:
      td.pointRecording[self.cath] = False      
      self.activeOffRadioButton.checked = 1
    self.currentTrackingDataNode = self.mappingTrackingDataSelector.currentNode()

    
  def onEgramRecordPointsSelected(self):
    td = self.getTrackingData()
    if td == None:
      return
    fnode = self.egramRecordPointsSelector.currentNode()
    if fnode:
      td.pointRecordingMarkupsNode[self.cath] = fnode
      fdnode = fnode.GetDisplayNode()
      if fdnode == None:
        fdnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialDisplayNode')
        slicer.mrmlScene.AddNode(fdnode)
        fnode.SetAndObserveDisplayNodeID(fdnode.GetID())
      if fnode:
        fdnode.SetTextScale(0.0)  # Hide the label
        

  def onModelSelected(self):
    mnode = self.modelSelector.currentNode()
    if mnode:
      dnode = mnode.GetDisplayNode()
      if dnode == None:
        dnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelDisplayNode')
        slicer.mrmlScene.AddNode(dnode)
        mnode.SetAndObserveDisplayNodeID(dnode.GetID())
      if dnode:
        dnode.SetVisibility(1)
        dnode.SetOpacity(0.5)


  def onSurfacePropertyChanged(self):
    self.controlPointsUpdated()

        
  def pointRecordingDistanceChanged(self):
    d = self.pointRecordingDistanceSliderWidget.value
    td = self.getTrackingData()    
    if td == None:
      return
    td.pointRecordingDistance[self.cath] = d

    
  def onResetPointRecording(self):
    td = self.getTrackingData()
    markupsNode = td.pointRecordingMarkupsNode[self.cath]
    if markupsNode:
      markupsNode.RemoveAllControlPoints()

      
  def onGenerateSurface(self):
    td = self.getTrackingData()
    markupsNode = td.pointRecordingMarkupsNode[self.cath]
    modelNode = self.modelSelector.currentNode()
    
    if markupsNode:
      self.generateSurfaceModel(markupsNode, modelNode)

      
  def onMapModel(self):
    td = self.getTrackingData()
    #markupsNode = td.pointRecordingMarkupsNode[self.cath]
    markupsNode = self.egramRecordPointsSelector.currentNode()
    modelNode = self.modelSelector.currentNode()
    
    if markupsNode and modelNode:

      # Copy markups to numpy array
      nPoints = markupsNode.GetNumberOfFiducials()
      #points = numpy.ndarray(shape=(nPoints, 3))
      pointsX = numpy.ndarray(shape=(nPoints, ))
      pointsY = numpy.ndarray(shape=(nPoints, ))
      pointsZ = numpy.ndarray(shape=(nPoints, ))
      values = numpy.ndarray(shape=(nPoints, ))
      pos = [0.0]*3

      # Obtain the parameter to map
      paramStr = self.paramSelector.currentText
      paramIndex = -1
      if paramStr != '' and paramStr != 'None':
        paramListStr = markupsNode.GetAttribute('MRTracking.EgramParamList')
        if paramListStr:
          paramList = paramListStr.split(',')
          i = 0
          for p in paramList: # Check the index
            if p == paramStr:
              paramIndex = i
            i = i + 1

      if paramIndex < 0: # 'None' is selected
        return
      
      if paramStr == 'Max(mV)':
        self.colorRangeWidget.minimum = -50.0
        self.colorRangeWidget.maximum = 50.0
      elif paramStr == 'Min(mV)':
        self.colorRangeWidget.minimum = -50.0
        self.colorRangeWidget.maximum = 50.0
      elif paramStr == 'LAT(ms)':
        self.colorRangeWidget.minimum = -1000.0
        self.colorRangeWidget.maximum = 1000.0
      else: # Default
        self.colorRangeWidget.minimum = -100.0
        self.colorRangeWidget.maximum = 100.0
      
      for i in range(nPoints):
        markupsNode.GetNthFiducialPosition(i, pos)
        #points[i][0] = pos[0] # X
        #points[i][1] = pos[1] # Y
        #points[i][2] = pos[2] # Z
        pointsX[i] = pos[0] # X
        pointsY[i] = pos[1] # Y
        pointsZ[i] = pos[2] # Z
        desc = markupsNode.GetNthControlPointDescription(i)
        paramsStr = desc.split(',')
        params = [float(s) for s in paramsStr]
        values[i] = params[paramIndex]
      
      poly = modelNode.GetPolyData()
      polyDataNormals = vtk.vtkPolyDataNormals()
      
      if vtk.VTK_MAJOR_VERSION <= 5:
        polyDataNormals.SetInput(poly)
      else:
        polyDataNormals.SetInputData(poly)
      
      polyDataNormals.ComputeCellNormalsOn()
      polyDataNormals.Update()
      polyData = polyDataNormals.GetOutput()
      
      # Copy obtain points from the surface map
      nPoints = polyData.GetNumberOfPoints()
      nCells = polyData.GetNumberOfCells()
      pSurface=[0.0, 0.0, 0.0]
      minDistancePoint = [0.0, 0.0, 0.0]
      
      # Create a list of points on the surface
      #surfacePoints = numpy.ndarray(shape=(nPoints, 3))
      surfacePointsX = numpy.ndarray(shape=(nPoints,))
      surfacePointsY = numpy.ndarray(shape=(nPoints,))
      surfacePointsZ = numpy.ndarray(shape=(nPoints,))
      
      pointValue = vtk.vtkDoubleArray()
      pointValue.SetName("Colors")
      pointValue.SetNumberOfComponents(1)
      pointValue.SetNumberOfTuples(nPoints)
      pointValue.Reset()
      pointValue.FillComponent(0,0.0);
      
      p=[0.0, 0.0, 0.0]
      for id in range(nPoints):
        polyData.GetPoint(id, p)
        #surfacePoints[id][0] = p[0]
        #surfacePoints[id][1] = p[1]
        #surfacePoints[id][2] = p[2]
        surfacePointsX[id] = p[0]
        surfacePointsY[id] = p[1]
        surfacePointsZ[id] = p[2]

      # Linear interpolation
      #grid = griddata(points, values, surfacePoints, method='linear')

      # Radial basis function (RBF) interplation
      rbfi = Rbf(pointsX, pointsY, pointsZ, values)  # radial basis function interpolator instance
      grid = rbfi(surfacePointsX, surfacePointsY, surfacePointsZ)

      for id in range(nPoints):
        pointValue.InsertValue(id, grid[id])
      
      modelNode.AddPointScalars(pointValue)
      modelNode.SetActivePointScalars("Colors", vtk.vtkDataSetAttributes.SCALARS)
      modelNode.Modified()
      displayNode = modelNode.GetModelDisplayNode()
      displayNode.SetActiveScalarName("Colors")
      displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileColdToHotRainbow.txt')
      displayNode.SetScalarRangeFlag(0) # Manual
      displayNode.SetScalarRange(self.defaultEgramValueRange[0], self.defaultEgramValueRange[1])
      displayNode.SetScalarVisibility(1)
      
      if self.scalarBarWidget == None:
        self.createScalarBar();
      self.scalarBarWidget.SetEnabled(1)
      
      actor = self.scalarBarWidget.GetScalarBarActor()
      actor.SetTitle(paramStr)

      
  def onUpdateColorRange(self, min, max):
    
    modelNode = self.modelSelector.currentNode()
    
    if modelNode:
      dispNode = modelNode.GetDisplayNode()
      dispNode.SetScalarRange(min, max)
      dispNode.Modified()

    if self.lookupTable:
      self.lookupTable.SetRange(min, max)      
      
      
  def createScalarBar(self):
    
    if self.scalarBarWidget == None: 
      self.scalarBarWidget = vtk.vtkScalarBarWidget()

      actor = self.scalarBarWidget.GetScalarBarActor()
      actor.SetOrientationToVertical()
      actor.SetNumberOfLabels(11)
      actor.SetTitle("Egram")
      actor.SetLabelFormat(" %#8.3f")
      actor.SetPosition(0.1, 0.1)
      actor.SetWidth(0.1)
      actor.SetHeight(0.8)
      
      layout = slicer.app.layoutManager()
      view = layout.threeDWidget(0).threeDView()
      renderer = layout.activeThreeDRenderer()
      self.scalarBarWidget.SetInteractor(renderer.GetRenderWindow().GetInteractor())

    colorTable = slicer.mrmlScene.GetNodeByID('vtkMRMLColorTableNodeFileColdToHotRainbow.txt')
    self.lookupTable = colorTable.GetLookupTable()
    self.lookupTable.SetRange(self.defaultEgramValueRange[0], self.defaultEgramValueRange[1])
    self.scalarBarWidget.GetScalarBarActor().SetLookupTable(self.lookupTable)
    

  def onSelectCath(self):
    for cath in range(self.nCath):
      if self.cathRadioButton[cath].checked:
        self.cath = cath

        
  def onActive(self):
    td = self.getTrackingData()
    if td == None:
      return
    if self.activeOnRadioButton.checked:
      # Add observer
      fnode = td.pointRecordingMarkupsNode[self.cath]
      if fnode:
        # Two observers are registered. The PointModifiedEvent is used to handle new points, whereas
        # the ModifiedEvent is used to capture the change of Egram parameter list (in the attribute)
        tag1 = fnode.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.controlPointsUpdated, 2)
        tag2 = fnode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.controlPointsNodeUpdated, 2)
        fnode.SetAttribute('SurfaceMapping.ObserverTag.PointModified', str(tag1))
        fnode.SetAttribute('SurfaceMapping.ObserverTag.Modified', str(tag2))
      td.pointRecording[self.cath] = True
      
    else:
      td.pointRecording[self.cath] = False
      fnode = td.pointRecordingMarkupsNode[self.cath]
      if fnode:
        tag = fnode.GetAttribute('SurfaceMapping.ObserverTag.PointModified')
        if tag != None:
          fnode.RemoveObserver(int(tag))
          fnode.SetAttribute('SurfaceMapping.ObserverTag.PointModified', None)
        tag = fnode.GetAttribute('SurfaceMapping.ObserverTag.Modified')
        if tag != None:
          fnode.RemoveObserver(int(tag))
          fnode.SetAttribute('SurfaceMapping.ObserverTag.Modified', None)

          
  def controlPointsUpdated(self,caller=None,event=None):
    td = self.getTrackingData()
    # Update the surface model
    fnode = td.pointRecordingMarkupsNode[self.cath]
    mnode = self.modelSelector.currentNode()
    mtmlogic = slicer.modules.markupstomodel.logic()
    
    if (fnode != None) and (mnode != None) and (mtmlogic != None):
      #mtmlogic.UpdateClosedSurfaceModel(fnode, mnode)
      fForceConvex = self.forceConvexCheckBox.checked;
      fSmoothing = self.smoothingCheckBox.checked
      mtmlogic.UpdateClosedSurfaceModel(fnode, mnode, fSmoothing, fForceConvex, 15.0)
      

  def controlPointsNodeUpdated(self,caller,event):
    td = self.getTrackingData()
    fnode = td.pointRecordingMarkupsNode[self.cath]
    paramListStr = fnode.GetAttribute('MRTracking.EgramParamList')
    if paramListStr:
      print(paramListStr)
      paramList = paramListStr.split(',')
      print(paramList)
      if len(paramList) != self.paramSelector.count - 1: # Note: The QComboBox has 'None' has the first item.
        self.paramSelector.clear()
        self.paramSelector.addItem('None')
        for p in paramList:
          self.paramSelector.addItem(p)
      else:
        i = 1
        for p in paramList:
          self.paramSelector.setItemText(i, p)
          i = i + 1


  def generateSurfaceModel(self, markupsNode, modelNode):

    svnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')

    ## Generate a scalar volume node
    # Get the bounding box
    bounds = [0.0] * 6
    markupsNode.GetBounds(bounds)
    
    b = numpy.array(bounds)
    b = b.reshape((3,2))
    origin = numpy.mean(b, axis=1)
    fov = numpy.abs(b[:,1]-b[:,0])
    fov = fov * 1.2 # 1.2 times larger than the bounding box
    b[:,0] = origin - fov/2.0
    b[:,1] = origin + fov/2.0
    bounds = b.reshape(-1)
    
    # Calculate the size of the volume
    #fov = numpy.max(b[:,1]-b[:0]) * 1.5 # 1.5 times larger than the bounding box
    #spacing = [fov/256]*3
    #
    ## Set parameters
    #parameters = {}
    #parameters['OutputVolume'] = svnode.GetID()
    #parameters['FillValue']    = '0.00'
    #parameters['Dimension']    = '3'
    #parameters['Size']         = '256, 256, 256'
    #parameters['Origin']       = center
    #parameters['Spacing']      = spacing
    #parameters['Direction']    = '1.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 1.00'
    #
    ## Execute
    #imageMaker = slicer.modules.imagemaker
    #cliNode = slicer.cli.runSync(imagemaker, None, parameters)
    ## Process results
    #if cliNode.GetStatus() & cliNode.ErrorsMask:
    #  # error
    #  errorText = cliNode.GetErrorText()
    #  slicer.mrmlScene.RemoveNode(cliNode)
    #  raise ValueError("CLI execution failed: " + errorText)
    ## success
    #slicer.mrmlScene.RemoveNode(cliNode)

    poly = self.fiducialsToPoly(markupsNode)
    
    #Note: Altenatively, vtkImageEllipsoidSource may be used to generate a volume.
    # Generate density field from points
    # Use fixed radius
    dens = vtk.vtkPointDensityFilter()
    dens.SetInputData(poly)
    dens.SetSampleDimensions(256,256,256)
    dens.SetDensityEstimateToFixedRadius()
    dens.SetRadius(2)
    #dens.SetDensityEstimateToRelativeRadius()
    #dens.SetRelativeRadius(2.5)
    #dens.SetDensityFormToVolumeNormalized()
    dens.SetDensityFormToNumberOfPoints()
    dens.SetModelBounds(bounds)
    dens.ComputeGradientOn()
    dens.Update()
    
    # Crete an image node - geometric parameters (origin, spacing) must be moved to the node object
    #imnode = slicer.vtkMRMLScalarVolumeNode()
    imnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')
    imdata = dens.GetOutput()
    imnode.SetAndObserveImageData(imdata)
    imnode.SetOrigin(imdata.GetOrigin())
    imnode.SetSpacing(imdata.GetSpacing())
    imdata.SetOrigin([0.0, 0.0, 0.0])
    imdata.SetSpacing([1.0, 1.0, 1.0])
    slicer.mrmlScene.AddNode(imnode)

  def fiducialsToPoly(self, markupsNode):
    
    pd = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    connectivity = vtk.vtkIntArray()
    connectivity.SetName('Connectivity')
    #stress = vtk.vtkFloatArray()
    #stress.SetName('Stress')

    nPoints = markupsNode.GetNumberOfFiducials()
    
    pos = [0.0]*3
    
    for i in range(nPoints):
      markupsNode.GetNthFiducialPosition(i, pos)
      points.InsertNextPoint(pos[0], pos[1], pos[2])
      #stress.InsertNextTuple1(float(v[5]))
      #connectivity.InsertNextTuple1(float(v[4]))

    #for line in iter(lambda: f.readline(), ""):
    #  v = line.split(',')
    #  cell = vtk.vtkTriangle()
    #  Ids = cell.GetPointIds()
    #  for kId in range(len(v)):
    #    Ids.SetId(kId,int(v[kId]))
    #  cells.InsertNextCell(cell)
    #f.close()

    pd.SetPoints(points)
    #pd.SetPolys(cells)
    #pd.GetPointData().AddArray(stress)
    #pd.GetPointData().AddArray(connectivity)

    return pd
