import ctk
import qt
import slicer
from MRTrackingUtils.qcomboboxcatheter import *

class MRTrackingPanelBase():
  def __init__(self, label="Base"):

    self.label = label
    self.catheters = None     #CatheterCollection
    self.currentCatheter = None

  def setCatheterCollection(self, cath):

    self.catheters = cath

    
  def buildGUI(self, parent):
    parentLayout = qt.QVBoxLayout(parent)

    # Catheter selector
    selectorLayout = qt.QFormLayout(parent)
    parentLayout.addLayout(selectorLayout)
    
    self.catheterComboBox = QComboBoxCatheter()
    self.catheterComboBox.setCatheterCollection(self.catheters)
    self.catheterComboBox.currentIndexChanged.connect(self.onCatheterSelected)
    
    selectorLayout.addRow("Catheter: ", self.catheterComboBox)

    # Main panel
    mainPanelFrame = qt.QFrame(parent)
    parentLayout.addWidget(mainPanelFrame)
    self.buildMainPanel(mainPanelFrame)
    

  def onCatheterSelected(self):
    self.currentCatheter = self.catheterComboBox.getCurrentCatheter()
    self.onSwitchCatheter()

      
  def buildMainPanel(self, frame):
    #
    # Should be implemented in the child class
    # 
    pass


  def onSwitchCatheter(self):
    #
    # Should be implemented in the child class
    # 
    pass
