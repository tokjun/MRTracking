import ctk
import qt
import slicer
from MRTrackingUtils.panelbase import *

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingReslice(MRTrackingPanelBase):

  def __init__(self, label="Reslice"):
    super(MRTrackingReslice, self).__init__(label)
    
    self.label = label

    self.reslice = [False, False, False]
    self.resliceDriverLogic= slicer.modules.volumereslicedriver.logic()

    self.sliceNodeRed = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
    self.sliceNodeYellow = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()
    self.sliceNodeGreen = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()

    self.resliceCath = 0

    self.nCath = 2

  def buildMainPanel(self, frame):    

    resliceLayout = qt.QFormLayout(frame)

    self.resliceCathRadioButton = [None] * self.nCath
    self.resliceCathBoxLayout = qt.QHBoxLayout()
    self.resliceCathGroup = qt.QButtonGroup()
    for cath in range(self.nCath):
      self.resliceCathRadioButton[cath] = qt.QRadioButton("Cath %d" % cath)
      if cath == self.resliceCath:
        self.resliceCathRadioButton[cath].checked = 0
      self.resliceCathBoxLayout.addWidget(self.resliceCathRadioButton[cath])
      self.resliceCathGroup.addButton(self.resliceCathRadioButton[cath])
      
    resliceLayout.addRow("Catheter:", self.resliceCathBoxLayout)
    
    self.resliceAxCheckBox = qt.QCheckBox()
    self.resliceAxCheckBox.checked = 0
    self.resliceAxCheckBox.text = "AX"
    self.resliceSagCheckBox = qt.QCheckBox()
    self.resliceSagCheckBox.checked = 0
    self.resliceSagCheckBox.text = "SAG"
    self.resliceCorCheckBox = qt.QCheckBox()
    self.resliceCorCheckBox.checked = 0
    self.resliceCorCheckBox.text = "COR"

    self.resliceBoxLayout = qt.QHBoxLayout()
    self.resliceBoxLayout.addWidget(self.resliceAxCheckBox)
    self.resliceBoxLayout.addWidget(self.resliceSagCheckBox)
    self.resliceBoxLayout.addWidget(self.resliceCorCheckBox)
    resliceLayout.addRow("Plane:", self.resliceBoxLayout)

    self.resliceAxCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceSagCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceCorCheckBox.connect('toggled(bool)', self.onResliceChecked)

    for cath in range(self.nCath):    
      self.resliceCathRadioButton[cath].connect('clicked(bool)', self.onSelectResliceCath)
      #self.resliceCath1RadioButton.connect('clicked(bool)', self.onSelectResliceCath)
    

  #--------------------------------------------------
  # GUI Slots

  def onSwitchCatheter(self):
    #
    # Should be implemented in the child class
    # 
    self.update()


  def onResliceChecked(self):
    
    ax  = self.resliceAxCheckBox.checked
    sag = self.resliceSagCheckBox.checked
    cor = self.resliceCorCheckBox.checked

    self.reslice = [ax, sag, cor]
    self.update()
    

  def onSelectResliceCath(self):

    for cath in range(self.nCath):
      if self.resliceCathRadioButton[cath].checked:
        self.resliceCath = cath
        
    self.update()

    
  #--------------------------------------------------
  # Setup Slice Driver
  
  def update(self):

    index = self.resliceCath
    
    tipTransformNodeID = ''
    if self.currentCatheter and self.currentCatheter.tipTransformNode:
      tipTransformNodeID = self.currentCatheter.tipTransformNode.GetID()
    if tipTransformNodeID == '':
      return
      
    # if the tracking data is current:
    if self.reslice[0]:
      self.resliceDriverLogic.SetDriverForSlice(tipTransformNodeID, self.sliceNodeRed)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_AXIAL, self.sliceNodeRed)
    else:
      self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeRed)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeRed)
    if self.reslice[1]:
      self.resliceDriverLogic.SetDriverForSlice(tipTransformNodeID, self.sliceNodeYellow)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_SAGITTAL, self.sliceNodeYellow)
    else:
      self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeYellow)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeYellow)
      
    if self.reslice[2]:
      self.resliceDriverLogic.SetDriverForSlice(tipTransformNodeID, self.sliceNodeGreen)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_CORONAL, self.sliceNodeGreen)
    else:
      self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeGreen)
      self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeGreen)
    
