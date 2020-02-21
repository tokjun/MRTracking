import ctk
import qt
import slicer

#------------------------------------------------------------
#
# MRTrackingFiducialRegistration class
#

class MRTrackingFiducialRegistration():

  def __init__(self, label="Registration"):

    self.label = label

    
  def buildGUI(self, parent):

    registrationLayout = qt.QFormLayout(parent)

    self.fromTrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.fromTrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.fromTrackingDataSelector.selectNodeUponCreation = True
    self.fromTrackingDataSelector.addEnabled = True
    self.fromTrackingDataSelector.removeEnabled = False
    self.fromTrackingDataSelector.noneEnabled = False
    self.fromTrackingDataSelector.showHidden = True
    self.fromTrackingDataSelector.showChildNodeTypes = False
    self.fromTrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.fromTrackingDataSelector.setToolTip( "Tracking Data (From)" )
    registrationLayout.addRow("TrackingData (From): ", self.fromTrackingDataSelector)

    self.toTrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.toTrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.toTrackingDataSelector.selectNodeUponCreation = True
    self.toTrackingDataSelector.addEnabled = True
    self.toTrackingDataSelector.removeEnabled = False
    self.toTrackingDataSelector.noneEnabled = False
    self.toTrackingDataSelector.showHidden = True
    self.toTrackingDataSelector.showChildNodeTypes = False
    self.toTrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.toTrackingDataSelector.setToolTip( "Tracking data (To)")
    registrationLayout.addRow("TrackingData (To): ", self.toTrackingDataSelector)

    pointBoxLayout = qt.QHBoxLayout()
    pointGroup = qt.QButtonGroup()

    self.useTipRadioButton = qt.QRadioButton("Tip")
    self.useAllRadioButton = qt.QRadioButton("All ")
    self.useTipRadioButton.checked = 1
    pointBoxLayout.addWidget(self.useTipRadioButton)
    pointGroup.addButton(self.useTipRadioButton)
    pointBoxLayout.addWidget(self.useAllRadioButton)
    pointGroup.addButton(self.useAllRadioButton)

    registrationLayout.addRow("Points: ", pointBoxLayout)

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

    self.collectButton.connect(qt.SIGNAL("clicked()"), self.onCollectPoints)

    
  def onCollectPoints(self):
      print ("onCollectPoints(self)")

  
