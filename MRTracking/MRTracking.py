import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from MRTrackingUtils.connector import *
from MRTrackingUtils.surfacemapping import *
from MRTrackingUtils.reslice import *
from MRTrackingUtils.registration import *
from MRTrackingUtils.qcomboboxcatheter import *
from MRTrackingUtils.catheter import *
from MRTrackingUtils.catheterconfig import *
from MRTrackingUtils.recording import *
from MRTrackingUtils.statusdisplay import *
import numpy
import functools

#------------------------------------------------------------
#
# MRTracking
#
class MRTracking(ScriptedLoadableModule):
  """MRTrakcing module is available at:
  https://github.com/tokjun/MRTracking
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MRTracking" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda (BWH), Wei Wang (BWH), Ehud Schmidt (BWH, JHU)"]
    self.parent.helpText = """
    Visualization of MR-tracked catheter. 
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH (5R01EB022011, P41EB015898, R01EB020667).
    """ 


#------------------------------------------------------------
#
# MRTrackingWidget
#
        
class MRTrackingWidget(ScriptedLoadableModuleWidget):
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = MRTrackingLogic(None)
    #self.logic.setWidget(self)

    #--------------------------------------------------
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    reloadCollapsibleButton.collapsed = True
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------

    #--------------------------------------------------
    # GUI components
    
    self.statusWidget = StatusDisplayWidget()
    self.layout.addWidget(self.statusWidget)
    self.statusWidget.startTimer()
    self.statusWidget.setCatheterCollection(self.logic.catheters)

    #
    # Main Tab
    #
    mainTabWidget = qt.QTabWidget()
    self.layout.addWidget(mainTabWidget)
    
    #--------------------------------------------------
    # Connection
    #--------------------------------------------------

    connectionFrame = qt.QFrame()
    mainTabWidget.addTab(connectionFrame, "Connection")

    # Layout within the dummy collapsible button
    connectionFormLayout = qt.QFormLayout(connectionFrame)

    self.igtlConnector1 = MRTrackingIGTLConnector("Connector 1  (MRI)")
    self.igtlConnector1.port = 18944
    self.igtlConnector1.buildGUI(connectionFormLayout, minimal=True, createNode=True)
    self.statusWidget.addConnector(self.igtlConnector1)

    self.igtlConnector2 = MRTrackingIGTLConnector("Connector 2 (NavX)")
    self.igtlConnector2.port = 18945
    self.igtlConnector2.buildGUI(connectionFormLayout, minimal=True, createNode=True)
    self.statusWidget.addConnector(self.igtlConnector2)


    #--------------------------------------------------
    # Tracking Node
    #--------------------------------------------------

    catheterFrame = qt.QFrame()
    mainTabWidget.addTab(catheterFrame, "Tracking")
    
    catheterSpacer = qt.QSpacerItem(0,0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    catheterLayout = qt.QVBoxLayout(catheterFrame)
    catheterInnerFrame = qt.QFrame()
    catheterLayout.addWidget(catheterInnerFrame)
    catheterLayout.addSpacerItem(catheterSpacer)

    self.catheterConfig = MRTrackingCatheterConfig("Catheter Configuration")
    self.catheterConfig.setCatheterCollection(self.logic.catheters)
    self.catheterConfig.buildGUI(catheterInnerFrame)

    #--------------------------------------------------
    # Surface Model & Mapping
    #--------------------------------------------------
    
    mappingFrame = qt.QFrame()
    mainTabWidget.addTab(mappingFrame, "Mapping")
    
    mappingSpacer = qt.QSpacerItem(0,0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    mappingLayout = qt.QVBoxLayout(mappingFrame)
    mappingInnerFrame = qt.QFrame()
    mappingLayout.addWidget(mappingInnerFrame)
    mappingLayout.addSpacerItem(mappingSpacer)
    
    self.surfaceMapping = MRTrackingSurfaceMapping("Surface Mapping")
    self.surfaceMapping.setCatheterCollection(self.logic.catheters)
    self.surfaceMapping.buildGUI(mappingInnerFrame)


    #--------------------------------------------------
    # Image Reslice
    #--------------------------------------------------

    resliceFrame = qt.QFrame()
    mainTabWidget.addTab(resliceFrame, "Reslice")

    resliceSpacer = qt.QSpacerItem(0,0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    resliceLayout = qt.QVBoxLayout(resliceFrame)
    resliceInnerFrame = qt.QFrame()
    resliceLayout.addWidget(resliceInnerFrame)
    resliceLayout.addSpacerItem(resliceSpacer)

    self.reslice = MRTrackingReslice("Image Reslice")
    self.reslice.setCatheterCollection(self.logic.catheters)    
    self.reslice.buildGUI(resliceInnerFrame)
    
    #--------------------------------------------------
    # Point-to-Point registration
    #--------------------------------------------------

    registrationFrame = qt.QFrame()
    mainTabWidget.addTab(registrationFrame, "Registration")

    registrationSpacer = qt.QSpacerItem(0,0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    registrationLayout = qt.QVBoxLayout(registrationFrame)
    registrationInnerFrame = qt.QFrame()
    registrationLayout.addWidget(registrationInnerFrame)
    registrationLayout.addSpacerItem(registrationSpacer)

    self.registration =  MRTrackingFiducialRegistration()
    self.registration.setCatheterCollection(self.logic.catheters)
    self.registration.buildGUI(registrationInnerFrame)

    #--------------------------------------------------
    # Recording
    #--------------------------------------------------

    recordingFrame = qt.QFrame()
    mainTabWidget.addTab(recordingFrame, "Recording")

    recordingSpacer = qt.QSpacerItem(0,0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    recordingLayout = qt.QVBoxLayout(recordingFrame)
    recordingInnerFrame = qt.QFrame()
    recordingLayout.addWidget(recordingInnerFrame)
    recordingLayout.addSpacerItem(recordingSpacer)

    self.recording = MRTrackingRecording("Recording")
    self.recording.setCatheterCollection(self.logic.catheters)    
    self.recording.buildGUI(recordingInnerFrame, False)
    
    #--------------------------------------------------
    # Connections
    #--------------------------------------------------
    
    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass

  
  def onReload(self, moduleName="MRTracking"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


      
#------------------------------------------------------------
#
# MRTrackingLogic
#
class MRTrackingLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent):
    ScriptedLoadableModuleLogic.__init__(self, parent)

    self.scene = slicer.mrmlScene
    
    self.widget = None

    self.catheters = CatheterCollection()
    self.registration = None

    # Create a parameter node
    self.parameterNode = self.getParameterNode()

    # Time to monitor data integrity
    self.monitoringTimer = qt.QTimer()

    self.addObservers()
    

  def addObservers(self):
    # Add observers
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAddedEvent)
    #self.scene.AddObserver(slicer.vtkMRMLScene.NodeAboutToBeRemovedEvent, self.onNodeRemovedEvent)
    #self.scene.AddObserver(slicer.vtkMRMLScene.StartSaveEvent, self.onSceneStartSaveEvent)
    self.scene.AddObserver(slicer.vtkMRMLScene.EndImportEvent, self.onSceneImportedEvent)
    self.scene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.onSceneClosedEvent)


  def clean(self):
    
    self.stopTimer()

    
  def startTimer(self):

    # The following section adds a timer-driven observer
    # NOTE: The timer interval is set to 1000 ms as assumed in TrackerStabilizer (see vtkSlicerTrackerStabilizerLogic.cxx)
    if self.monitoringTimer.isActive() == False:
      self.monitoringTimer.timeout.connect(self.monitorDataTrackingBundle)
      self.monitoringTimer.start(1000)
      #print("Timer started.")
      return True
    else:
      return False  # Could not add observer.

    
  def stopTimer(self):
    if self.monitoringTimer.isActive() == True:
      self.monitoringTimer.stop()

      
  def monitorDataTrackingBundle(self):

    # Check if the transform nodes under the tracking data bundles points
    # are associated with the bundle node.
    
    tdlist = slicer.util.getNodesByClass("vtkMRMLIGTLTrackingDataBundleNode")
    count = 0
    for tdnode in tdlist:
      if not tdnode:
        continue
      nTrans = tdnode.GetNumberOfTransformNodes()
      for i in range(nTrans):
        tnode = tdnode.GetTransformNode(i)
        if tnode:
          tnode.SetAttribute('MRTracking.trackingDataBundle', tdnode.GetID())
      count = count + 1
      
    
  def isStringInteger(self, s):
    try:
        int(s)
        return True
    except ValueError:
        return False

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAddedEvent(self, caller, eventId, callData):
    # print("New node: {0}".format(callData.GetName()))
    # if str(callData.GetAttribute("ModuleName")) == self.moduleName:
    #   print ("parameterNode added")
  
    if callData.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      self.startTimer()

    ## Check if the transform nodes under the tracking data bundles points
    ## are associated with the bundle node.
    #if callData.GetClassName() == 'vtkMRMLLinearTransformNode':
    #  tdlist = slicer.util.getNodesByClass("vtkMRMLIGTLTrackingDataBundleNode")
    #  for tdnode in tdlist:
    #    if not tdnode:
    #      continue
    #    nTrans = tdnode.GetNumberOfTransformNodes()
    #    for i in range(nTrans):
    #      tnode = tdnode.GetTransformNode(i)
    #      if tnode:
    #        tnode.SetAttribute('MRTracking.trackingDataBundle', tdnode.GetID())

      
  #def onNodeRemovedEvent(self, caller, event, obj=None):

  ## TODO: slicer.vtkMRMLScene.StartSaveEvent is not captured... 
  #def onSceneStartSaveEvent(self, caller, event, obj=None):
  #  print ("onSceneStartSaveEvent()")
  #
  #  ## Scene should be saved as Bundle as the Slicer tries to overwrite the nodes with the same names
  #  ## if scene is saved in a folder.
  #
  #  ## Because vtkMRMLIGTLTrackingDataBundleNode does not save the child transforms,
  #  ## we tag the parent tracking data bundle node as an attribute in each child transform.
  #  tdlist = slicer.util.getNodesByClass("vtkMRMLIGTLTrackingDataBundleNode")
  #  for tdnode in tdlist:
  #    if not tdnode:
  #      continue
  #    nTrans = tdnode.GetNumberOfTransformNodes()
  #    for i in range(nTrans):
  #      tnode = tdnode.GetTransformNode(i)
  #      if tnode:
  #        tnode.SetAttribute('MRTracking.trackingDataBundle', tdnode.GetID())
          
    
  def onSceneImportedEvent(self, caller, event, obj=None):
    print ("onSceneImportedEvent()")

    self.clean()

    # Look for tracking data ("vtkMRMLIGTLTrackingDataBundleNode") in the imported scene.
    tdlist = slicer.util.getNodesByClass("vtkMRMLIGTLTrackingDataBundleNode")

    if len(tdlist) > 0:
    
      #for tdnode in tdlist:
      #  if not (tdnode.GetID() in self.TrackingData):
      #    self.addNewTrackingData(tdnode)
      
      # Because vtkMRMLIGTLTrackingDataBundleNode does not recover the child transforms
      # we add them based on the attributes in each child transform. (see onSceneStartSaveEvent())
      
      tlist = slicer.util.getNodesByClass("vtkMRMLLinearTransformNode")
      for tnode in tlist:
        if not tnode:
          continue
        nodeID = str(tnode.GetAttribute('MRTracking.trackingDataBundle'))
        if nodeID == '':
          continue
        tdnode = slicer.mrmlScene.GetNodeByID(nodeID)
        if tdnode:
          matrix = vtk.vtkMatrix4x4()
          tnode.GetMatrixTransformToParent(matrix)
          print("Adding new tracking node to the bundle: %s" % tnode.GetName())
          tdnode.UpdateTransformNode(tnode.GetName(), matrix)
          
          filteredNodeID = str(tnode.GetAttribute('MRTracking.filteredNode'))
          if filteredNodeID != '':
            filteredNode = slicer.mrmlScene.GetNodeByID(filteredNodeID)
            slicer.mrmlScene.RemoveNode(filteredNode)
            
          processorNodeID = str(tnode.GetAttribute('MRTracking.processorNode'))
          if processorNodeID != '':
            processorNode = slicer.mrmlScene.GetNodeByID(processorNodeID)
            slicer.mrmlScene.RemoveNode(processorNode)
      
          # Sincce UpdateTransformNode creates a new transform node, discard the old one:
          # Remove filtered node and processor node
          slicer.mrmlScene.RemoveNode(tnode)
          
          ## TODO: Set filtered transforms?

      #for tdnode in tdlist:
      #  self.TrackingData[tdnode.GetID()].loadConfigFromParameterNode()
          
      self.startTimer()

      
  def onSceneClosedEvent(self, caller, event, obj=None):
    
    print ("onSceneClosedEvent()")
    self.stopTimer()
    self.clean()

      
