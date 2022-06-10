import ctk
import qt
import slicer
import vtk
import numpy
import sitkUtils
import SimpleITK as sitk
from scipy.interpolate import Rbf
from MRTrackingUtils.qcomboboxcatheter import *
from MRTrackingUtils.qpointrecordingframe  import *
from MRTrackingUtils.panelbase import *

#from scipy.interpolate import griddata

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingSurfaceMapping(MRTrackingPanelBase):

  def __init__(self, label="SurfaceMapping"):
    super(MRTrackingSurfaceMapping, self).__init__(label)
    
    self.label = label
    self.currentCatheter = None
    self.scalarBarWidget = None
    self.lookupTable = None
    self.defaultEgramValueRange = [0.0, 20.0]

  def buildMainPanel(self, frame):

    layout = qt.QVBoxLayout(frame)

    pointGroupBox = ctk.ctkCollapsibleGroupBox()
    pointGroupBox.title = "Recording"
    pointGroupBox.collapsed = False

    # Point recording
    
    layout.addWidget(pointGroupBox)
    pointLayout = qt.QVBoxLayout(pointGroupBox)
    self.precording = QPointRecordingFrame(catheterComboBox=self.catheterComboBox)
    pointLayout.addWidget(self.precording)

    mappingLayout = qt.QFormLayout(frame)
    layout.addLayout(mappingLayout)

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

    # Point distance factor is used to generate a surface model from the point cloud
    self.pointDistanceFactorSliderWidget = ctk.ctkSliderWidget()
    self.pointDistanceFactorSliderWidget.singleStep = 0.1
    self.pointDistanceFactorSliderWidget.minimum = 0.0
    self.pointDistanceFactorSliderWidget.maximum = 20.0
    self.pointDistanceFactorSliderWidget.value = 8.0
    #self.minIntervalSliderWidget.setToolTip("")

    mappingLayout.addRow("Point Disntace Factor: ",  self.pointDistanceFactorSliderWidget)
    
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
    
    self.modelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onModelSelected)
    self.generateSurfaceButton.connect('clicked(bool)', self.onGenerateSurface)
    
    self.mapModelButton.connect('clicked(bool)', self.onMapModel)
    self.colorRangeWidget.connect('valuesChanged(double, double)', self.onUpdateColorRange)
    
    
  #--------------------------------------------------
  # GUI Slots

  def onSwitchCatheter(self):
    #
    # Should be implemented in the child class
    #
    pass


  
  #def onEgramRecordPointsSelected(self):
  #  
  #  td = self.currentCatheter    
  #  if td == None:
  #    return
  #  
  #  fnode = self.egramRecordPointsSelector.currentNode()
  #  if fnode:
  #    td.pointRecordingMarkupsNode = fnode
  #    fdnode = fnode.GetDisplayNode()
  #    if fdnode == None:
  #      fdnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialDisplayNode')
  #      slicer.mrmlScene.AddNode(fdnode)
  #      fnode.SetAndObserveDisplayNodeID(fdnode.GetID())
  #    if fnode:
  #      fdnode.SetTextScale(0.0)  # Hide the label
        

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


  def onResetPointRecording(self):
    td = self.currentCatheter        
    markupsNode = td.pointRecordingMarkupsNode
    if markupsNode:
      markupsNode.RemoveAllControlPoints()

      
  def onGenerateSurface(self):
    td = self.currentCatheter            
    markupsNode = td.pointRecordingMarkupsNode
    modelNode = self.modelSelector.currentNode()
    pdf = self.pointDistanceFactorSliderWidget.value
    
    if markupsNode:
      self.generateSurfaceModel(markupsNode, modelNode, pdf)

      
  def onMapModel(self):
    td = self.currentCatheter            
    #markupsNode = self.egramRecordPointsSelector.currentNode()
    markupsNode = self.precording.getCurrentFiducials()
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
        paramListStr = markupsNode.GetAttribute('MRTracking.' + str(td.catheterID) + '.EgramParamList')
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
    

  # TODO: Who should call this?
  def onPointRecordingMarkupsNodeSelected(self):
    td = self.currentCatheter
    fnode = td.pointRecordingMarkupsNode
    paramListStr = fnode.GetAttribute('MRTracking.' + str(td.catheterID) + '.EgramParamList')
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


  def generateSurfaceModel(self, markupsNode, modelNode, pointDistanceFactor):

    svnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')

    print('Generating a surface model from tracking data... ')
    
    ## Generate a scalar volume node
    # Get the bounding box
    print('Calculating bounding box... ')    
    bounds = [0.0] * 6
    markupsNode.GetBounds(bounds)
    print(bounds)

    b = numpy.array(bounds)
    b = b.reshape((3,2))
    origin = numpy.mean(b, axis=1)
    fov = numpy.abs(b[:,1]-b[:,0])
    fovMax = numpy.max(fov)
    boundingBoxRange = (fovMax * 1.5)/2.0 # 1.5 times larger than the bounding box; from the center to the end (1/2 of each dimension)
    b[:,0] = origin - boundingBoxRange
    b[:,1] = origin + boundingBoxRange
    bounds = b.reshape(-1)
    print(bounds)
    res = 256

    print('Converting fiducials to poly data...')
    poly = self.fiducialsToPoly(markupsNode)
   
    #Note: Altenatively, vtkImageEllipsoidSource may be used to generate a volume.
    # Generate density field from points
    # Use fixed radius
    print('Running vtkPointDensityFilter...')
    dens = vtk.vtkPointDensityFilter()
    dens.SetInputData(poly)

    # TODO - is the resolution good enoguh?
    dens.SetSampleDimensions(res, res, res)
    dens.SetDensityEstimateToFixedRadius()
    # TODO - Does this radius work for every case?
    pixelSize = boundingBoxRange * 2 / res

    # Note: the algorithm fails when the bounding box is too small..
    if pixelSize < 0.5:
      pixelSize = 0.5
    
    radius = pixelSize
    dens.SetRadius(radius)
    #dens.SetDensityEstimateToRelativeRadius()
    #dens.SetRelativeRadius(2.5)
    #dens.SetDensityFormToVolumeNormalized()
    dens.SetDensityFormToNumberOfPoints()
    dens.SetModelBounds(bounds)
    dens.ComputeGradientOn()
    dens.Update()

    print('Creating an image node...')    
    # Crete an image node - geometric parameters (origin, spacing) must be moved to the node object
    #imnode = slicer.vtkMRMLScalarVolumeNode()
    imnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')
    imnode.SetName('MRTracking_SurfaceMap_tmp')
    imdata = dens.GetOutput()
    imnode.SetAndObserveImageData(imdata)
    imnode.SetOrigin(imdata.GetOrigin())
    imnode.SetSpacing(imdata.GetSpacing())
    #imdata.SetOrigin([0.0, 0.0, 0.0])
    #imdata.SetSpacing([1.0, 1.0, 1.0])
    slicer.mrmlScene.AddNode(imnode)

    print('Applying BinaryThreshold...')    
    image  = sitkUtils.PullVolumeFromSlicer(imnode.GetID())
    binImage = sitk.BinaryThreshold(image, lowerThreshold=1.0, upperThreshold=256, insideValue=1, outsideValue=0)

    # Calculate the radius parameter for dilation and erosion
    radiusInPixel = int(numpy.ceil(pointDistanceFactor / pixelSize))
    if radiusInPixel < 1.0:
      radiusInPixel = 1

    # Dilate the target label
    print('Dilating the image...')    
    dilateFilter = sitk.BinaryDilateImageFilter()
    dilateFilter.SetBoundaryToForeground(False)
    dilateFilter.SetKernelRadius(radiusInPixel)
    dilateFilter.SetKernelType(sitk.sitkBall)
    dilateFilter.SetForegroundValue(1)
    dilateFilter.SetBackgroundValue(0)
    dilateImage = dilateFilter.Execute(binImage)

    # Fill holes in the target label
    print('Filling holes...')    
    fillHoleFilter = sitk.BinaryFillholeImageFilter()
    fillHoleFilter.SetForegroundValue(1)
    fillHoleFilter.SetFullyConnected(True)
    fillHoleImage = fillHoleFilter.Execute(dilateImage)

    # Erode the label
    print('Eroding the image...')    
    erodeFilter = sitk.BinaryErodeImageFilter()
    erodeFilter.SetBoundaryToForeground(False)
    erodeFilter.SetKernelType(sitk.sitkBall)
    erodeFilter.SetKernelRadius(radiusInPixel-1) # 1 pixel smaller than the radius for dilation.
    erodeFilter.SetForegroundValue(1)
    erodeFilter.SetBackgroundValue(0)
    erodeImage = erodeFilter.Execute(fillHoleImage)

    print('Pushing the volume to the MRML scene...')    
    sitkUtils.PushVolumeToSlicer(erodeImage, imnode.GetName(), 0, True)
    imdata = imnode.GetImageData()

    imdata.SetOrigin(imnode.GetOrigin())
    imdata.SetSpacing(imnode.GetSpacing())

    print('Running marching cubes...')    
    poly = self.marchingCubes(imdata)
    modelNode.SetAndObservePolyData(poly)

    slicer.mrmlScene.RemoveNode(imnode)
    print('Done.')    
    
    
  def fiducialsToPoly(self, markupsNode):
    
    pd = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    connectivity = vtk.vtkIntArray()
    connectivity.SetName('Connectivity')

    nPoints = markupsNode.GetNumberOfFiducials()
    
    pos = [0.0]*3
    
    for i in range(nPoints):
      markupsNode.GetNthFiducialPosition(i, pos)
      points.InsertNextPoint(pos[0], pos[1], pos[2])

    pd.SetPoints(points)
    
    return pd


  def marchingCubes(self, imageData):
    
    mc = vtk.vtkMarchingCubes()
    mc.SetInputData(imageData)
    mc.ComputeNormalsOff()
    mc.ComputeGradientsOff()
    mc.SetValue(0, 1.0)
    mc.Update()
    
    #smoothFilter = vtk.vtkSmoothPolyDataFilter()
    ##smoothFilter.SetInputConnection(confilter.GetOutputPort())
    #smoothFilter.SetInputData(mc.GetOutput())
    #smoothFilter.SetNumberOfIterations(15)
    #smoothFilter.SetRelaxationFactor(0.1)
    #smoothFilter.FeatureEdgeSmoothingOff()
    #smoothFilter.BoundarySmoothingOn()
    #smoothFilter.Update()

    smoothFilter2 = vtk.vtkWindowedSincPolyDataFilter()
    smoothFilter2.SetInputData(mc.GetOutput())
    smoothFilter2.SetNumberOfIterations(10)
    smoothFilter2.BoundarySmoothingOff()
    smoothFilter2.FeatureEdgeSmoothingOff()
    smoothFilter2.SetFeatureAngle(120)
    smoothFilter2.SetPassBand(0.001)
    smoothFilter2.NonManifoldSmoothingOn()
    smoothFilter2.NormalizeCoordinatesOn()
    smoothFilter2.Update()
    
    decimate = vtk.vtkDecimatePro()
    decimate.SetInputData(smoothFilter2.GetOutput())
    decimate.SetTargetReduction(0.1)
    decimate.PreserveTopologyOn()
    decimate.Update()
    
    return decimate.GetOutput()
