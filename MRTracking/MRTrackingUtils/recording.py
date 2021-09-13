import ctk
import qt
import slicer
from MRTrackingUtils.panelbase import *

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingRecording(MRTrackingPanelBase):

  def __init__(self, label="Recording"):
    super(MRTrackingRecording, self).__init__(label)

    self.recfile = None
    
    self.reslice = [False, False, False]
    self.resliceDriverLogic= slicer.modules.volumereslicedriver.logic()

    self.resliceCath = 0

    
  def buildMainPanel(self, frame):
    
    layout = qt.QFormLayout(frame)
    fileBoxLayout = qt.QHBoxLayout()

    self.fileLineEdit = qt.QLineEdit()
    self.fileDialogBoxButton = qt.QPushButton()
    self.fileDialogBoxButton.setCheckable(False)
    self.fileDialogBoxButton.text = '...'
    self.fileDialogBoxButton.setToolTip("Open file dialog box.")
    
    fileBoxLayout.addWidget(self.fileLineEdit)
    fileBoxLayout.addWidget(self.fileDialogBoxButton)
    layout.addRow("File Path:", fileBoxLayout)
    
    self.fileDialogBoxButton.connect('clicked(bool)', self.openDialogBox)
    self.fileLineEdit.editingFinished.connect(self.onFilePathEntered)
    
  #--------------------------------------------------
  # GUI Slots

  def openDialogBox(self):
    
    dlg = qt.QFileDialog()
    dlg.setFileMode(qt.QFileDialog.AnyFile)
    dlg.setNameFilter("CSV files (*.csv)")
    dlg.setAcceptMode(qt.QFileDialog.AcceptOpen)
    
    if dlg.exec_():
      filename = dlg.selectedFiles()[0]
      print(filename)

      self.fileLineEdit.text = filename

  def onFilePathEntered(self):
    pass

    
