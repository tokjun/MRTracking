import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from TrackingData import *
import numpy

import CurveMaker
    
#------------------------------------------------------------
#
# MRTracking
#
class MRTracking(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MRTracking" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda, Wei Wang, Ehud Schmidt (BWH)"]
    self.parent.helpText = """
    Visualization of MR-tracked catheter. 
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH (P41EB015898, R01EB020667).
    """ 
    # replace with organization, grant and thanks.


#------------------------------------------------------------
#
# MRTrackingWidget
#
class MRTrackingWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = MRTrackingLogic(None)
    self.logic.setWidget(self)

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
    self.reloadButton.name = "CurveMaker Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------


    #--------------------------------------------------
    # GUI components
    
    #
    # Connection Area
    #
    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "Connection (OpenIGTLink)"
    self.layout.addWidget(connectionCollapsibleButton)

    # Layout within the dummy collapsible button
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

    #
    # connector selector
    #
    self.connectorSelector = slicer.qMRMLNodeComboBox()
    self.connectorSelector.nodeTypes = ( ("vtkMRMLIGTLConnectorNode"), "" )
    self.connectorSelector.selectNodeUponCreation = True
    self.connectorSelector.addEnabled = True
    self.connectorSelector.removeEnabled = False
    self.connectorSelector.noneEnabled = False
    self.connectorSelector.showHidden = False
    self.connectorSelector.showChildNodeTypes = False
    self.connectorSelector.setMRMLScene( slicer.mrmlScene )
    self.connectorSelector.setToolTip( "Establish a connection with the server" )
    connectionFormLayout.addRow("Connector: ", self.connectorSelector)
    
    self.connectorPort = qt.QSpinBox()
    self.connectorPort.objectName = 'PortSpinBox'
    self.connectorPort.setMaximum(64000)
    self.connectorPort.setValue(18944)
    self.connectorPort.setToolTip("Port number of the server")
    connectionFormLayout.addRow("Port: ", self.connectorPort)

    #
    # check box to trigger transform conversion
    #
    self.activeConnectionCheckBox = qt.QCheckBox()
    self.activeConnectionCheckBox.checked = 0
    self.activeConnectionCheckBox.enabled = 0
    self.activeConnectionCheckBox.setToolTip("Activate OpenIGTLink connection")
    connectionFormLayout.addRow("Active: ", self.activeConnectionCheckBox)


    #
    # Tracking node selector
    #
    trackingNodeCollapsibleButton = ctk.ctkCollapsibleButton()
    trackingNodeCollapsibleButton.text = "Tracking Node"
    self.layout.addWidget(trackingNodeCollapsibleButton)

    trackingNodeFormLayout = qt.QFormLayout(trackingNodeCollapsibleButton)

    self.trackingDataSelector = slicer.qMRMLNodeComboBox()
    self.trackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.trackingDataSelector.selectNodeUponCreation = True
    self.trackingDataSelector.addEnabled = True
    self.trackingDataSelector.removeEnabled = False
    self.trackingDataSelector.noneEnabled = False
    self.trackingDataSelector.showHidden = True
    self.trackingDataSelector.showChildNodeTypes = False
    self.trackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.trackingDataSelector.setToolTip( "Incoming tracking data" )
    trackingNodeFormLayout.addRow("TrackingData: ", self.trackingDataSelector)

    #
    # check box to trigger transform conversion
    #
    self.activeTrackingCheckBox = qt.QCheckBox()
    self.activeTrackingCheckBox.checked = 0
    self.activeTrackingCheckBox.enabled = 1
    self.activeTrackingCheckBox.setToolTip("Activate Tracking")
    trackingNodeFormLayout.addRow("Active: ", self.activeTrackingCheckBox)
    
    #
    # Configuration Selection Area
    #
    selectionCollapsibleButton = ctk.ctkCollapsibleButton()
    selectionCollapsibleButton.text = "Catheter Configuration"
    self.layout.addWidget(selectionCollapsibleButton)

    selectionFormLayout = qt.QFormLayout(selectionCollapsibleButton)

    #
    # Catheter #1 Tip Length (legnth between the catheter tip and the first coil)
    #
    self.tipLength1SliderWidget = ctk.ctkSliderWidget()
    self.tipLength1SliderWidget.singleStep = 0.5
    self.tipLength1SliderWidget.minimum = 0.0
    self.tipLength1SliderWidget.maximum = 100.0
    self.tipLength1SliderWidget.value = 10.0
    self.tipLength1SliderWidget.setToolTip("Set the length of the catheter tip.")
    selectionFormLayout.addRow("Cath 1 Tip Length (mm): ", self.tipLength1SliderWidget)
    
    #
    # Catheter #1 Catheter diameter
    #
    self.catheter1DiameterSliderWidget = ctk.ctkSliderWidget()
    self.catheter1DiameterSliderWidget.singleStep = 0.1
    self.catheter1DiameterSliderWidget.minimum = 0.1
    self.catheter1DiameterSliderWidget.maximum = 10.0
    self.catheter1DiameterSliderWidget.value = 1.0
    self.catheter1DiameterSliderWidget.setToolTip("Set the diameter of the catheter")
    selectionFormLayout.addRow("Cath 1 Diameter (mm): ", self.catheter1DiameterSliderWidget)

    #
    # Catheter #1 Catheter opacity
    #
    self.catheter1OpacitySliderWidget = ctk.ctkSliderWidget()
    self.catheter1OpacitySliderWidget.singleStep = 0.1
    self.catheter1OpacitySliderWidget.minimum = 0.0
    self.catheter1OpacitySliderWidget.maximum = 1.0
    self.catheter1OpacitySliderWidget.value = 1.0
    self.catheter1OpacitySliderWidget.setToolTip("Set the opacity of the catheter")
    selectionFormLayout.addRow("Cath 1 Opacity: ", self.catheter1OpacitySliderWidget)


    #
    # Catheter #2 Tip Length (legnth between the catheter tip and the first coil)
    #
    self.tipLength2SliderWidget = ctk.ctkSliderWidget()
    self.tipLength2SliderWidget.singleStep = 0.5
    self.tipLength2SliderWidget.minimum = 0.0
    self.tipLength2SliderWidget.maximum = 100.0
    self.tipLength2SliderWidget.value = 10.0
    self.tipLength2SliderWidget.setToolTip("Set the length of the catheter tip.")
    selectionFormLayout.addRow("Cath 2 Tip Length (mm): ", self.tipLength2SliderWidget)
    
    #
    # Catheter #2 diameter
    #
    self.catheter2DiameterSliderWidget = ctk.ctkSliderWidget()
    self.catheter2DiameterSliderWidget.singleStep = 0.1
    self.catheter2DiameterSliderWidget.minimum = 0.1
    self.catheter2DiameterSliderWidget.maximum = 10.0
    self.catheter2DiameterSliderWidget.value = 1.0
    self.catheter2DiameterSliderWidget.setToolTip("Set the diameter of the catheter")
    selectionFormLayout.addRow("Cath 2 Diameter (mm): ", self.catheter2DiameterSliderWidget)

    #
    # Catheter #2 opacity
    #
    self.catheter2OpacitySliderWidget = ctk.ctkSliderWidget()
    self.catheter2OpacitySliderWidget.singleStep = 0.1
    self.catheter2OpacitySliderWidget.minimum = 0.0
    self.catheter2OpacitySliderWidget.maximum = 1.0
    self.catheter2OpacitySliderWidget.value = 1.0
    self.catheter2OpacitySliderWidget.setToolTip("Set the opacity of the catheter")
    selectionFormLayout.addRow("Cath 2 Opacity: ", self.catheter2OpacitySliderWidget)

    #
    # Coil Selection Aare
    #
    coilCollapsibleButton = ctk.ctkCollapsibleButton()
    coilCollapsibleButton.text = "Coil Selection"
    self.layout.addWidget(coilCollapsibleButton)
    
    coilSelectionLayout = qt.QFormLayout(coilCollapsibleButton)
    
    #
    # Check box to show/hide coil labels 
    #
    self.showCoilLabelCheckBox = qt.QCheckBox()
    self.showCoilLabelCheckBox.checked = 0
    self.showCoilLabelCheckBox.setToolTip("Show/hide coil labels")
    coilSelectionLayout.addRow("Show Coil Labels: ", self.showCoilLabelCheckBox)

    #
    # Coil seleciton check boxes
    #
    self.coil_1_1_CheckBox = qt.QCheckBox()
    self.coil_1_1_CheckBox.checked = 1
    self.coil_1_1_CheckBox.text = "CH 1"
    self.coil_1_2_CheckBox = qt.QCheckBox()
    self.coil_1_2_CheckBox.checked = 1
    self.coil_1_2_CheckBox.text = "CH 2"
    self.coil_1_3_CheckBox = qt.QCheckBox()
    self.coil_1_3_CheckBox.checked = 1
    self.coil_1_3_CheckBox.text = "CH 3"
    self.coil_1_4_CheckBox = qt.QCheckBox()
    self.coil_1_4_CheckBox.checked = 1
    self.coil_1_4_CheckBox.text = "CH 4"
    self.coil_1_5_CheckBox = qt.QCheckBox()
    self.coil_1_5_CheckBox.checked = 0
    self.coil_1_5_CheckBox.text = "CH 5"
    self.coil_1_6_CheckBox = qt.QCheckBox()
    self.coil_1_6_CheckBox.checked = 0
    self.coil_1_6_CheckBox.text = "CH 6"
    self.coil_1_7_CheckBox = qt.QCheckBox()
    self.coil_1_7_CheckBox.checked = 0
    self.coil_1_7_CheckBox.text = "CH 7"
    self.coil_1_8_CheckBox = qt.QCheckBox()
    self.coil_1_8_CheckBox.checked = 0
    self.coil_1_8_CheckBox.text = "CH 8"

    self.coilGroup11Layout = qt.QHBoxLayout()
    self.coilGroup11Layout.addWidget(self.coil_1_1_CheckBox)
    self.coilGroup11Layout.addWidget(self.coil_1_2_CheckBox)
    self.coilGroup11Layout.addWidget(self.coil_1_3_CheckBox)
    self.coilGroup11Layout.addWidget(self.coil_1_4_CheckBox)
    coilSelectionLayout.addRow("Cath 1 Active Coils:", self.coilGroup11Layout)

    self.coilGroup12Layout = qt.QHBoxLayout()
    self.coilGroup12Layout.addWidget(self.coil_1_5_CheckBox)
    self.coilGroup12Layout.addWidget(self.coil_1_6_CheckBox)
    self.coilGroup12Layout.addWidget(self.coil_1_7_CheckBox)
    self.coilGroup12Layout.addWidget(self.coil_1_8_CheckBox)
    coilSelectionLayout.addRow("", self.coilGroup12Layout)

    self.coilOrder1DistalRadioButton = qt.QRadioButton("Distal First")
    self.coilOrder1DistalRadioButton.checked = 1
    self.coilOrder1ProximalRadioButton = qt.QRadioButton("Proximal First")
    self.coilOrder1ProximalRadioButton.checked = 0
    self.coilOrder1ButtonGroup = qt.QButtonGroup()
    self.coilOrder1ButtonGroup.addButton(self.coilOrder1DistalRadioButton)
    self.coilOrder1ButtonGroup.addButton(self.coilOrder1ProximalRadioButton)
    self.coilOrder1GroupLayout = qt.QHBoxLayout()
    self.coilOrder1GroupLayout.addWidget(self.coilOrder1DistalRadioButton)
    self.coilOrder1GroupLayout.addWidget(self.coilOrder1ProximalRadioButton)
    coilSelectionLayout.addRow("Cath 1 Coil Order:", self.coilOrder1GroupLayout)
    
    self.coil_2_1_CheckBox = qt.QCheckBox()
    self.coil_2_1_CheckBox.checked = 0
    self.coil_2_1_CheckBox.text = "CH 1"
    self.coil_2_2_CheckBox = qt.QCheckBox()
    self.coil_2_2_CheckBox.checked = 0
    self.coil_2_2_CheckBox.text = "CH 2"
    self.coil_2_3_CheckBox = qt.QCheckBox()
    self.coil_2_3_CheckBox.checked = 0
    self.coil_2_3_CheckBox.text = "CH 3"
    self.coil_2_4_CheckBox = qt.QCheckBox()
    self.coil_2_4_CheckBox.checked = 0
    self.coil_2_4_CheckBox.text = "CH 4"
    self.coil_2_5_CheckBox = qt.QCheckBox()
    self.coil_2_5_CheckBox.checked = 1
    self.coil_2_5_CheckBox.text = "CH 5"
    self.coil_2_6_CheckBox = qt.QCheckBox()
    self.coil_2_6_CheckBox.checked = 1
    self.coil_2_6_CheckBox.text = "CH 6"
    self.coil_2_7_CheckBox = qt.QCheckBox()
    self.coil_2_7_CheckBox.checked = 1
    self.coil_2_7_CheckBox.text = "CH 7"
    self.coil_2_8_CheckBox = qt.QCheckBox()
    self.coil_2_8_CheckBox.checked = 1
    self.coil_2_8_CheckBox.text = "CH 8"
    
    self.coilGroup21Layout = qt.QHBoxLayout()
    self.coilGroup21Layout.addWidget(self.coil_2_1_CheckBox)
    self.coilGroup21Layout.addWidget(self.coil_2_2_CheckBox)
    self.coilGroup21Layout.addWidget(self.coil_2_3_CheckBox)
    self.coilGroup21Layout.addWidget(self.coil_2_4_CheckBox)
    coilSelectionLayout.addRow("Cath 2 Active Coils:", self.coilGroup21Layout)

    self.coilGroup22Layout = qt.QHBoxLayout()
    self.coilGroup22Layout.addWidget(self.coil_2_5_CheckBox)
    self.coilGroup22Layout.addWidget(self.coil_2_6_CheckBox)
    self.coilGroup22Layout.addWidget(self.coil_2_7_CheckBox)
    self.coilGroup22Layout.addWidget(self.coil_2_8_CheckBox)
    coilSelectionLayout.addRow("", self.coilGroup22Layout)
    
    self.coilOrder2DistalRadioButton = qt.QRadioButton("Distal First")
    self.coilOrder2DistalRadioButton.checked = 1
    self.coilOrder2ProximalRadioButton = qt.QRadioButton("Proximal First")
    self.coilOrder2ProximalRadioButton.checked = 0
    self.coilOrder2ButtonGroup = qt.QButtonGroup()
    self.coilOrder2ButtonGroup.addButton(self.coilOrder2DistalRadioButton)
    self.coilOrder2ButtonGroup.addButton(self.coilOrder2ProximalRadioButton)
    self.coilOrder2GroupLayout = qt.QHBoxLayout()
    self.coilOrder2GroupLayout.addWidget(self.coilOrder2DistalRadioButton)
    self.coilOrder2GroupLayout.addWidget(self.coilOrder2ProximalRadioButton)
    coilSelectionLayout.addRow("Cath 2 Coil Order:", self.coilOrder2GroupLayout)

    #
    # Coordinate System
    #
    coordinateCollapsibleButton = ctk.ctkCollapsibleButton()
    coordinateCollapsibleButton.text = "Coordinate System"
    self.layout.addWidget(coordinateCollapsibleButton)

    coordinateLayout = qt.QFormLayout(coordinateCollapsibleButton)
    
    self.coordinateRPlusRadioButton = qt.QRadioButton("+X")
    self.coordinateRMinusRadioButton = qt.QRadioButton("-X")
    self.coordinateRPlusRadioButton.checked = 1
    self.coordinateRBoxLayout = qt.QHBoxLayout()
    self.coordinateRBoxLayout.addWidget(self.coordinateRPlusRadioButton)
    self.coordinateRBoxLayout.addWidget(self.coordinateRMinusRadioButton)
    self.coordinateRGroup = qt.QButtonGroup()
    self.coordinateRGroup.addButton(self.coordinateRPlusRadioButton)
    self.coordinateRGroup.addButton(self.coordinateRMinusRadioButton)
    coordinateLayout.addRow("Right:", self.coordinateRBoxLayout)

    self.coordinateAPlusRadioButton = qt.QRadioButton("+Y")
    self.coordinateAMinusRadioButton = qt.QRadioButton("-Y")
    self.coordinateAPlusRadioButton.checked = 1
    self.coordinateABoxLayout = qt.QHBoxLayout()
    self.coordinateABoxLayout.addWidget(self.coordinateAPlusRadioButton)
    self.coordinateABoxLayout.addWidget(self.coordinateAMinusRadioButton)
    self.coordinateAGroup = qt.QButtonGroup()
    self.coordinateAGroup.addButton(self.coordinateAPlusRadioButton)
    self.coordinateAGroup.addButton(self.coordinateAMinusRadioButton)
    coordinateLayout.addRow("Anterior:", self.coordinateABoxLayout)

    self.coordinateSPlusRadioButton = qt.QRadioButton("+Z")
    self.coordinateSMinusRadioButton = qt.QRadioButton("-Z")
    self.coordinateSPlusRadioButton.checked = 1
    self.coordinateSBoxLayout = qt.QHBoxLayout()
    self.coordinateSBoxLayout.addWidget(self.coordinateSPlusRadioButton)
    self.coordinateSBoxLayout.addWidget(self.coordinateSMinusRadioButton)
    self.coordinateSGroup = qt.QButtonGroup()
    self.coordinateSGroup.addButton(self.coordinateSPlusRadioButton)
    self.coordinateSGroup.addButton(self.coordinateSMinusRadioButton)
    coordinateLayout.addRow("Superior:", self.coordinateSBoxLayout)

    #
    # Reslice
    #
    resliceCollapsibleButton = ctk.ctkCollapsibleButton()
    resliceCollapsibleButton.text = "Image Reslice"
    self.layout.addWidget(resliceCollapsibleButton)

    resliceLayout = qt.QFormLayout(resliceCollapsibleButton)
    
    self.resliceCath1RadioButton = qt.QRadioButton("Cath 1")
    self.resliceCath2RadioButton = qt.QRadioButton("Cath 2")
    self.resliceCath1RadioButton.checked = 0
    self.resliceCathBoxLayout = qt.QHBoxLayout()
    self.resliceCathBoxLayout.addWidget(self.resliceCath1RadioButton)
    self.resliceCathBoxLayout.addWidget(self.resliceCath2RadioButton)

    self.resliceCathGroup = qt.QButtonGroup()
    self.resliceCathGroup.addButton(self.resliceCath1RadioButton)
    self.resliceCathGroup.addButton(self.resliceCath2RadioButton)
    resliceLayout.addRow("Reslice Catheter:", self.resliceCathBoxLayout)
    
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
    resliceLayout.addRow("Reslice Plane:", self.resliceBoxLayout)

    #
    # Point-to-Point registration
    #
    registrationCollapsibleButton = ctk.ctkCollapsibleButton()
    registrationCollapsibleButton.text = "Point-to-Point Registration"
    self.layout.addWidget(registrationCollapsibleButton)
    
    registrationLayout = qt.QFormLayout(registrationCollapsibleButton)

    self.reg1TrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.reg1TrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.reg1TrackingDataSelector.selectNodeUponCreation = True
    self.reg1TrackingDataSelector.addEnabled = True
    self.reg1TrackingDataSelector.removeEnabled = False
    self.reg1TrackingDataSelector.noneEnabled = False
    self.reg1TrackingDataSelector.showHidden = True
    self.reg1TrackingDataSelector.showChildNodeTypes = False
    self.reg1TrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.reg1TrackingDataSelector.setToolTip( "Tracking data 1" )
    registrationLayout.addRow("TrackingData 1: ", self.reg1TrackingDataSelector)

    self.reg2TrackingDataSelector = slicer.qMRMLNodeComboBox()
    self.reg2TrackingDataSelector.nodeTypes = ( ("vtkMRMLIGTLTrackingDataBundleNode"), "" )
    self.reg2TrackingDataSelector.selectNodeUponCreation = True
    self.reg2TrackingDataSelector.addEnabled = True
    self.reg2TrackingDataSelector.removeEnabled = False
    self.reg2TrackingDataSelector.noneEnabled = False
    self.reg2TrackingDataSelector.showHidden = True
    self.reg2TrackingDataSelector.showChildNodeTypes = False
    self.reg2TrackingDataSelector.setMRMLScene( slicer.mrmlScene )
    self.reg2TrackingDataSelector.setToolTip( "Tracking data 2" )
    registrationLayout.addRow("TrackingData 2: ", self.reg2TrackingDataSelector)

    
    #
    # Connections
    #
    self.connectorSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onConnectorSelected)
    self.trackingDataSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTrackingDataSelected)
    self.activeConnectionCheckBox.connect('toggled(bool)', self.onActiveConnection)
    self.activeTrackingCheckBox.connect('toggled(bool)', self.onActiveTracking)
    self.tipLength1SliderWidget.connect("valueChanged(double)", self.onTipLength1Changed)
    self.catheter1DiameterSliderWidget.connect("valueChanged(double)", self.onCatheter1DiameterChanged)
    self.catheter1OpacitySliderWidget.connect("valueChanged(double)", self.onCatheter1OpacityChanged)
    self.tipLength2SliderWidget.connect("valueChanged(double)", self.onTipLength2Changed)
    self.catheter2DiameterSliderWidget.connect("valueChanged(double)", self.onCatheter2DiameterChanged)
    self.catheter2OpacitySliderWidget.connect("valueChanged(double)", self.onCatheter2OpacityChanged)
    self.showCoilLabelCheckBox.connect('toggled(bool)', self.onCoilLabelChecked)
    
    self.coil_1_1_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_2_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_3_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_4_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_5_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_6_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_7_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_1_8_CheckBox.connect('toggled(bool)', self.onCoilChecked)

    self.coil_2_1_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_2_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_3_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_4_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_5_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_6_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_7_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    self.coil_2_8_CheckBox.connect('toggled(bool)', self.onCoilChecked)
    
    self.coilOrder1DistalRadioButton.connect('clicked(bool)', self.onCoilChecked)
    self.coilOrder1ProximalRadioButton.connect('clicked(bool)', self.onCoilChecked)
    self.coilOrder2DistalRadioButton.connect('clicked(bool)', self.onCoilChecked)
    self.coilOrder2ProximalRadioButton.connect('clicked(bool)', self.onCoilChecked)
    
    self.resliceAxCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceSagCheckBox.connect('toggled(bool)', self.onResliceChecked)
    self.resliceCorCheckBox.connect('toggled(bool)', self.onResliceChecked)

    self.resliceCath1RadioButton.connect('clicked(bool)', self.onSelectResliceCath)
    self.resliceCath2RadioButton.connect('clicked(bool)', self.onSelectResliceCath)

    self.coordinateRPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateRMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateAMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSPlusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)
    self.coordinateSMinusRadioButton.connect('clicked(bool)', self.onSelectCoordinate)

    
    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass


  #--------------------------------------------------
  # OpenIGTLink
  #
  def connectToServer(self, addr, port):

    if self.connectorSelector.currentNode() == None:
      return

    cnode = self.connectorSelector.currentNode()

    cnode.SetTypeClient(addr, port)
    cnode.Start()


  def waitForClient(self, port):
  
    if self.connectorSelector.currentNode() == None:
      return

    cnode = self.connectorSelector.currentNode()

    cnode.SetTypeServer(port)
    cnode.Start()

    
  def disconnect(self):

    if self.connectorSelector.currentNode() == None:
      return

    cnode = self.connectorSelector.currentNode()
    
    if cnode == None:
      return False

    cnode.Stop()

    
  def active(self):
    # Check the activation status.
    # Return True, if the connector is connected to the server

    if self.connectorSelector.currentNode() == None:
      return

    cnode = self.connectorSelector.currentNode()
    
    if cnode == None:
      return False
      
    #if cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.STATE_WAIT_CONNECTION or cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.STATE_CONNECTED:
    if cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.StateWaitConnection or cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.StateConnected:
      return True
    else:
      return False
    
    
  def connected(self):
    # Check the connection status.
    # Return True, if the connector is connected to the server

    if self.connectorSelector.currentNode() == None:
      return

    cnode = self.connectorSelector.currentNode()

    if cnode == None:
      return False
      
    #if cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.STATE_CONNECTED:
    if cnode.GetState() == slicer.vtkMRMLIGTLConnectorNode.StateConnected:
      return True
    else:
      return False

    
  #--------------------------------------------------
  # GUI Call Back functions
  #

  def onActiveConnection(self):
    
    if self.connectorSelector.currentNode() == None:
      return

    if self.activeConnectionCheckBox.checked == True:
      if self.connected() != True:
        port  = self.connectorPort.value
        self.waitForClient(port)
    else:
      self.disconnect()

    #time.sleep(1)
    #self.updateGUI()

  def onConnectorSelected(self):
    cnode = self.connectorSelector.currentNode()    
    # self.logic.setConnector(cnode)
    self.updateConnectorGUI()

  def onActiveTracking(self):
    if self.activeTrackingCheckBox.checked == True:
      self.logic.activateTracking()
    else:
      self.logic.deactivateTracking()

    
  def onTrackingDataSelected(self):
    tdnode = self.trackingDataSelector.currentNode()    
    #self.logic.setTrackingData(cnode)
    tdata = self.logic.switchCurrentTrackingData(tdnode)
    self.updateTrackingDataGUI(tdata)

    if tdata.eventTag != '':
      self.activeTrackingCheckBox.checked == True
    else:
      self.activeTrackingCheckBox.checked == False
      
      
  def onRejectRegistration(self):
    self.logic.acceptNewMatrix(self, False)

    
  def onTipLength1Changed(self):
    self.logic.setTipLength(self.tipLength1SliderWidget.value, 1)

    
  def onCatheter1DiameterChanged(self):
    self.logic.setCatheterDiameter(self.catheter1DiameterSliderWidget.value, 1)
    

  def onCatheter1OpacityChanged(self):
    self.logic.setCatheterOpacity(self.catheter1OpacitySliderWidget.value, 1)
    
  def onTipLength2Changed(self):
    self.logic.setTipLength(self.tipLength2SliderWidget.value, 2)

  def onCatheter2DiameterChanged(self):
    self.logic.setCatheterDiameter(self.catheter2DiameterSliderWidget.value, 2)
    

  def onCatheter2OpacityChanged(self):
    self.logic.setCatheterOpacity(self.catheter2OpacitySliderWidget.value, 2)
    
    
  def onCoilLabelChecked(self):
    self.logic.setShowCoilLabel(self.showCoilLabelCheckBox.checked)


  def onCoilChecked(self):
    activeCoils1 = [
      self.coil_1_1_CheckBox.checked,
      self.coil_1_2_CheckBox.checked,
      self.coil_1_3_CheckBox.checked,
      self.coil_1_4_CheckBox.checked,
      self.coil_1_5_CheckBox.checked,
      self.coil_1_6_CheckBox.checked,
      self.coil_1_7_CheckBox.checked,
      self.coil_1_8_CheckBox.checked
    ]
    activeCoils2 = [
      self.coil_2_1_CheckBox.checked,
      self.coil_2_2_CheckBox.checked,
      self.coil_2_3_CheckBox.checked,
      self.coil_2_4_CheckBox.checked,
      self.coil_2_5_CheckBox.checked,
      self.coil_2_6_CheckBox.checked,
      self.coil_2_7_CheckBox.checked,
      self.coil_2_8_CheckBox.checked
    ]

    coilOrder1 = 'distal'
    if self.coilOrder1ProximalRadioButton.checked:
      coilOrder1 = 'proximal'
    coilOrder2 = 'distal'
    if self.coilOrder2ProximalRadioButton.checked:
      coilOrder2 = 'proximal'

    self.logic.setActiveCoils(activeCoils1, activeCoils2, coilOrder1, coilOrder2)
    
  def onResliceChecked(self):
    
    ax  = self.resliceAxCheckBox.checked
    sag = self.resliceSagCheckBox.checked
    cor = self.resliceCorCheckBox.checked

    self.logic.setReslice(ax, sag, cor)

    
  def onSelectResliceCath(self):

    if self.resliceCath1RadioButton.checked:
      self.logic.setResliceCath(1)
    else:
      self.logic.setResliceCath(2)

      
  def onSelectCoordinate(self):

    rPositive = self.coordinateRPlusRadioButton.checked
    aPositive = self.coordinateAPlusRadioButton.checked
    sPositive = self.coordinateSPlusRadioButton.checked
    
    self.logic.setAxisDirections(rPositive, aPositive, sPositive)
    
      
  def onReload(self, moduleName="MRTracking"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


  def updateConnectorGUI(self):

    #if self.logic.connected():
    if self.active():
      self.activeConnectionCheckBox.setChecked(True)
    else:
      self.activeConnectionCheckBox.setChecked(False)

    # Enable/disable 'Active' checkbox 
    if self.connectorSelector.currentNode():
      self.activeConnectionCheckBox.setEnabled(True)
    else:
      self.activeConnectionCheckBox.setEnabled(False)


  def updateTrackingDataGUI(self, tdata):
    # Enable/disable GUI components based on the state machine
    
    if self.logic.isTrackingActive():
      self.activeTrackingCheckBox.checked = True
    else:
      self.activeTrackingCheckBox.checked = False
    
    self.tipLength1SliderWidget.value = tdata.tipLength[0]
    self.catheter1DiameterSliderWidget.value = tdata.cmRadius[0] * 2
    self.catheter1OpacitySliderWidget.value = tdata.cmOpacity[0]
    self.tipLength2SliderWidget.value = tdata.tipLength[1]
    self.catheter2DiameterSliderWidget.value = tdata.cmRadius[1] * 2
    self.catheter2OpacitySliderWidget.value = tdata.cmOpacity[1]
    
    self.showCoilLabelCheckBox.checked = tdata.showCoilLabel
    
    self.coil_1_1_CheckBox.checked = tdata.activeCoils1[0]
    self.coil_1_2_CheckBox.checked = tdata.activeCoils1[1]
    self.coil_1_3_CheckBox.checked = tdata.activeCoils1[2]
    self.coil_1_4_CheckBox.checked = tdata.activeCoils1[3]
    self.coil_1_5_CheckBox.checked = tdata.activeCoils1[4]
    self.coil_1_6_CheckBox.checked = tdata.activeCoils1[5]
    self.coil_1_7_CheckBox.checked = tdata.activeCoils1[6]
    self.coil_1_8_CheckBox.checked = tdata.activeCoils1[7]
    
    self.coil_2_1_CheckBox.checked = tdata.activeCoils2[0]
    self.coil_2_2_CheckBox.checked = tdata.activeCoils2[1]
    self.coil_2_3_CheckBox.checked = tdata.activeCoils2[2]
    self.coil_2_4_CheckBox.checked = tdata.activeCoils2[3]
    self.coil_2_5_CheckBox.checked = tdata.activeCoils2[4]
    self.coil_2_6_CheckBox.checked = tdata.activeCoils2[5]
    self.coil_2_7_CheckBox.checked = tdata.activeCoils2[6]
    self.coil_2_8_CheckBox.checked = tdata.activeCoils2[7]

    if tdata.axisDirection[0] > 0.0:
      self.coordinateRPlusRadioButton.checked = 1
    else:
      self.coordinateRMinusRadioButton.checked = 1
      
    if tdata.axisDirection[1] > 0.0:
      self.coordinateAPlusRadioButton.checked = 1
    else:
      self.coordinateAMinusRadioButton.checked = 1

    if tdata.axisDirection[2] > 0.0:
      self.coordinateSPlusRadioButton.checked = 1
    else:
      self.coordinateSMinusRadioButton.checked = 1

      
#------------------------------------------------------------
#
# MRTrackingLogic
#
class MRTrackingLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent):
    ScriptedLoadableModuleLogic.__init__(self, parent)

    self.scene = slicer.mrmlScene
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)

    self.widget = None

    self.eventTag = {}

    # IGTL Conenctor Node ID
    # self.connectorNodeID = ''
    
    # CurveMaker
    self.cmLogic = CurveMaker.CurveMakerLogic()

    # Tip model
    #self.tipLength = [10.0, 10.0]
    #self.tipModelNode = [None, None]
    #self.tipTransformNode = [None, None]
    #self.tipPoly = [None, None]
    #self.showCoilLabel = False
    #self.activeCoils1 = [False, False, False, False, True, True, True, True]
    #self.activeCoils2 = [True, True, True, True, False, False, False, False]
    
    self.reslice = [False, False, False]
    self.resliceDriverLogic= slicer.modules.volumereslicedriver.logic()

    self.sliceNodeRed = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
    self.sliceNodeYellow = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()
    self.sliceNodeGreen = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()

    self.resliceCath = 1

    #self.axisDirection = [1.0, 1.0, 1.0]

    self.currentTrackingDataNodeID = ''
    self.TrackingData = {}


  def addNewTrackingData(self, tdnode):
    if not tdnode:
      return
    
    if tdnode.GetID() in self.TrackingData:
      print('TrackingData "%s" has already been registered.' % tdnode.GetID())
    else:
      td = TrackingData()
      td.cmLogic = self.cmLogic
      self.TrackingData[tdnode.GetID()] = td
      
      self.setupFiducials(tdnode, 1)
      self.setupFiducials(tdnode, 2)

  def switchCurrentTrackingData(self, tdnode):
    if not tdnode:
      return

    if not (tdnode.GetID() in self.TrackingData):
      self.addNewTrackingData(tdnode)

    self.currentTrackingDataNodeID = tdnode.GetID()
    return self.TrackingData[tdnode.GetID()]
  

  def getCurrentTrackingData(self):
    return self.TrackingData[self.currentTrackingDataNodeID]
  

  def setWidget(self, widget):
    self.widget = widget


  def setTipLength(self, length, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.tipLength[index-1] = length
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)


  def setCatheterDiameter(self, diameter, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.cmRadius[index-1] = diameter / 2.0
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)
    

  def setCatheterOpacity(self, opacity, index):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.cmOpacity[index-1] = opacity
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, index)

        
  def setShowCoilLabel(self, show):
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.showCoilLabel = show
        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 1)
        self.updateCatheter(tnode, 2)

        
  def isStringInteger(self, s):
    try:
        int(s)
        return True
    except ValueError:
        return False


  def setActiveCoils(self, coils1, coils2, coilOrder1, coilOrder2):
    print("setActiveCoils(self, coils1, coils2, coilOrder1, coilOrder2)")
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        td.activeCoils1 = coils1
        td.activeCoils2 = coils2
        if coilOrder1 == 'distal':
          td.coilOrder1 = True
        else:
          td.coilOrder1 = False
        if coilOrder2 == 'distal':
          td.coilOrder2 = True
        else:
          td.coilOrder2 = False

        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 1)
        self.updateCatheter(tnode, 2)
        
    return True


  def setReslice(self, ax, sag, cor):
    self.reslice = [ax, sag, cor]
    for nodeID in self.TrackingData:
      tnode = slicer.mrmlScene.GetNodeByID(nodeID)
      self.updateCatheter(tnode, 1)
      self.updateCatheter(tnode, 2)
   

  def setResliceCath(self, index):
    self.resliceCath = index

    
  def setAxisDirections(self, rPositive, aPositive, sPositive):
    
    nodeID = self.currentTrackingDataNodeID
    if nodeID:
      td = self.TrackingData[nodeID]
      if td:
        if rPositive:
          td.axisDirection[0] = 1.0
        else:
          td.axisDirection[0] = -1.0
          
        if aPositive:
          td.axisDirection[1] = 1.0
        else:
          td.axisDirection[1] = -1.0
          
        if sPositive:
          td.axisDirection[2] = 1.0
        else:
          td.axisDirection[2] = -1.0

        tnode = slicer.mrmlScene.GetNodeByID(nodeID)
        self.updateCatheter(tnode, 1)
        self.updateCatheter(tnode, 2)
   
    
  def setupFiducials(self, tdnode, index):

    if not tdnode:
      return
    
    # Set up markups fiducial node, if specified in the connector node
    cmFiducialsID = tdnode.GetAttribute('MRTracking.cmFiducials%d' % index)
    if cmFiducialsID != None:
      self.cmLogic.CurrentSourceNode = self.scene.GetNodeByID(cmFiducialsID)
    else:
      self.cmLogic.CurrentSourceNode = None
      
    # Set up model node, if specified in the connector node
    cmModelID = tdnode.GetAttribute('MRTracking.cmModel%d' % index)
    if cmModelID != None:
      self.cmLogic.CurrentDestinationNode = self.scene.GetNodeByID(cmModelID)
      if self.cmLogic.CurrentSourceNode:
        self.cmLogic.CurrentSourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.CurrentDestinationNode.GetID())
    else:
      self.cmLogic.CurrentDestinationNode = None
      
    #if self.cmLogic.CurrentSourceNode:
    #  cnode.SetAttribute('CoilPositions', cmFiducialsID)

    td = self.TrackingData[tdnode.GetID()]
    
    # Set up tip model node, if specified in the connector node
    tipModelID = tdnode.GetAttribute('MRTracking.tipModel%d' % index)
    if tipModelID != None:
      td.tipModelNode[index-1] = self.scene.GetNodeByID(tipModelID)
    else:
      td.tipModelNode[index-1] = None

    tipTransformNodeID = tdnode.GetAttribute('MRTracking.tipTransform%d' % index)
    if tipTransformNodeID != None:
      td.tipTransformNode[index-1] = self.scene.GetNodeByID(tipTransformNodeID)
    else:
      td.tipTransformNode[index-1] = None

    ## Set up incoming node, if specified in the connector node
    #incomingNodeID = tdnode.GetAttribute('MRTracking.incomingNode%d' % index)
    #if incomingNodeID != None:
    #  incomingNode = self.scene.GetNodeByID(incomingNodeID)
    #  if incomingNode:
    #      self.eventTag[incomingNodeID] = incomingNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
    #tdnode.eventTag = incomingNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
    
        
  def onMessageReceived(self, node):
    #print ("onMessageReceived(self, %s)" % node.GetID())
    #if node.GetID() == self.connectorNodeID:
    #  for tdNodeID in self.TrackingData:
        #print (" updating %s" % tdNodeID)
    print("onMessageReceived(self, node) %s" % node.GetClassName())
    parentID = node.GetAttribute('MRTracking.parent')
    
    if parentID == '':
      return

    tdnode = slicer.mrmlScene.GetNodeByID(parentID)
    
    if tdnode and tdnode.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      print("updateCatheter")
      self.updateCatheterNode(tdnode, 1)
      self.updateCatheterNode(tdnode, 2)

      
  def updateCatheterNode(self, tdnode, index):
    #print("updateCatheterNode(%s, %d) is called" % (tdnode.GetID(), index) )
    # node shoud be vtkMRMLIGTLTrackingDataBundleNode

    fiducialNode = None

    cathName = 'Catheter_%d' % index

    ## Catheter 1
    fiducialNodeID = tdnode.GetAttribute(cathName)
    if fiducialNodeID != None:
      fiducialNode = self.scene.GetNodeByID(fiducialNodeID)
    
    if fiducialNode == None:
      fiducialNode = self.scene.CreateNodeByClass("vtkMRMLMarkupsFiducialNode")
      fiducialNode.SetLocked(True)
      fiducialNode.SetName('CoilGroup_%d' % index)
      self.scene.AddNode(fiducialNode)
      fiducialNodeID = fiducialNode.GetID()
      tdnode.SetAttribute(cathName, fiducialNodeID)
      
    self.cmLogic.CurrentSourceNode = fiducialNode

    # Check if the curve model exists; if not, create one.
    destinationNode = None
    nodeID = self.cmLogic.CurrentSourceNode.GetAttribute('CurveMaker.CurveModel')
    if nodeID:
      destinationNode = self.scene.GetNodeByID(nodeID)
    if destinationNode == None:
      destinationNode = self.scene.CreateNodeByClass("vtkMRMLModelNode")
      destinationNode.SetName('Catheter')
      self.scene.AddNode(destinationNode)
      #self.scene.AddNode(modelDisplayNode)
      
    self.cmLogic.CurrentDestinationNode = destinationNode

    if self.cmLogic.CurrentDestinationNode:
      tdnode.SetAttribute('MRTracking.cmModel%d' % index, self.cmLogic.CurrentDestinationNode.GetID())
    if self.cmLogic.CurrentSourceNode:
      tdnode.SetAttribute('MRTracking.cmFiducials%d' % index, self.cmLogic.CurrentSourceNode.GetID())
        
    if self.cmLogic.CurrentDestinationNode and self.cmLogic.CurrentSourceNode:
      self.cmLogic.CurrentSourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.CurrentDestinationNode.GetID())
              
    # Update coordinates in the fiducial node.
    nCoils = tdnode.GetNumberOfTransformNodes()
    td = self.TrackingData[tdnode.GetID()]
    mask = td.activeCoils1[0:nCoils]
    if index == 2:
      mask = td.activeCoils2[0:nCoils]
    nActiveCoils = sum(mask)
    if fiducialNode.GetNumberOfFiducials() != nActiveCoils:
      fiducialNode.RemoveAllMarkups()
      for i in range(nActiveCoils):
        fiducialNode.AddFiducial(0.0, 0.0, 0.0)
    j = 0

    # Max. number of coils is 8.
    if nCoils > 8:
      nCoils = 8
      
    for i in range(nCoils):
      if mask[i]:
        tnode = tdnode.GetTransformNode(i)
        trans = tnode.GetTransformToParent()
        #fiducialNode.SetNthFiducialPositionFromArray(j, trans.GetPosition())
        v = trans.GetPosition()
        coilID = j
        if index == 1 and td.coilOrder1 == False:
          coilID = nCoils - j - 1
        if index == 2 and td.coilOrder2 == False:
          coilID = nCoils - j - 1
        fiducialNode.SetNthFiducialPosition(coilID, v[0] * td.axisDirection[0], v[1] * td.axisDirection[1], v[2] * td.axisDirection[2])
        j += 1
      
    self.updateCatheter(tdnode, index)


  def updateCatheter(self, tdnode, index):

    if tdnode == None:
      return
    
    cmFiducialsID = tdnode.GetAttribute('MRTracking.cmFiducials%d' % index)
    if cmFiducialsID == None:
      return

    sourceNode = self.scene.GetNodeByID(cmFiducialsID)

    if sourceNode == None:
      return

    cmModelID = sourceNode.GetAttribute('CurveMaker.CurveModel')
    if cmModelID == None:
      return
    
    destinationNode = self.scene.GetNodeByID(cmModelID)

    td = self.TrackingData[tdnode.GetID()]
    
    modelDisplayNode = destinationNode.GetDisplayNode()
    if modelDisplayNode:
      modelDisplayNode.SetColor(td.cmModelColor[index-1])
      modelDisplayNode.SetOpacity(td.cmOpacity[index-1])
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetSliceDisplayModeToIntersection()

    # Update catheter using the CurveMaker module
    self.cmLogic.setTubeRadius(td.cmRadius[index-1], sourceNode)
    self.cmLogic.enableAutomaticUpdate(1, sourceNode)
    self.cmLogic.setInterpolationMethod('cardinal', sourceNode)
    self.cmLogic.updateCurve()

    # Skip if the model has not been created. (Don't call this section before self.cmLogic.updateCurve()
    if not (sourceNode.GetID() in self.cmLogic.CurvePoly) or (self.cmLogic.CurvePoly[sourceNode.GetID()] == None):
      return
    
    # Show/hide fiducials for coils
    fiducialDisplayNode = sourceNode.GetDisplayNode()
    if fiducialDisplayNode:
      fiducialDisplayNode.SetVisibility(td.showCoilLabel)

    # Add a extended tip
    ## make sure that there is more than one points
    if sourceNode.GetNumberOfFiducials() < 2:
      return
    
    curvePoly = self.cmLogic.CurvePoly[sourceNode.GetID()]
    lines = curvePoly.GetLines()
    points = curvePoly.GetPoints()
    pts = vtk.vtkIdList()
    
    lines.GetCell(0, pts)
    n = pts.GetNumberOfIds()
    if n > 1:
      p0 = numpy.array(points.GetPoint(pts.GetId(0)))
      p1 = numpy.array(points.GetPoint(pts.GetId(1)))
      v10 = p0 - p1
      n10 = v10 / numpy.linalg.norm(v10) # Normal vector at the tip
      pe = p0 + n10 * td.tipLength[index-1]

      ## Calculate rotation matrix
      ## Check if <n10> is not parallel to <s>=(0.0, 1.0, 0.0)
      s = numpy.array([0.0, 1.0, 0.0])
      t = numpy.array([1.0, 0.0, 0.0])
      if n10[1] < 0.95:
        t = numpy.cross(s, n10)
        s = numpy.cross(n10, t)
      else:
        s = numpy.cross(n10, t)
        t = numpy.cross(s, n10)

    if td.tipPoly[index-1]==None:
      td.tipPoly[index-1] = vtk.vtkPolyData()

    if td.tipModelNode[index-1] == None:
      td.tipModelNode[index-1] = self.scene.CreateNodeByClass('vtkMRMLModelNode')
      td.tipModelNode[index-1].SetName('Tip')
      self.scene.AddNode(td.tipModelNode[index-1])
      tdnode.SetAttribute('MRTracking.tipModel%d' % index, td.tipModelNode[index-1].GetID())
        
    if td.tipTransformNode[index-1] == None:
      td.tipTransformNode[index-1] = self.scene.CreateNodeByClass('vtkMRMLLinearTransformNode')
      td.tipTransformNode[index-1].SetName('TipTransform')
      self.scene.AddNode(td.tipTransformNode[index-1])
      tdnode.SetAttribute('MRTracking.tipTransform%d' % index, td.tipTransformNode[index-1].GetID())

    matrix = vtk.vtkMatrix4x4()
    matrix.SetElement(0, 0, t[0])
    matrix.SetElement(1, 0, t[1])
    matrix.SetElement(2, 0, t[2])
    matrix.SetElement(0, 1, s[0])
    matrix.SetElement(1, 1, s[1])
    matrix.SetElement(2, 1, s[2])
    matrix.SetElement(0, 2, n10[0])
    matrix.SetElement(1, 2, n10[1])
    matrix.SetElement(2, 2, n10[2])
    matrix.SetElement(0, 3, pe[0])
    matrix.SetElement(1, 3, pe[1])
    matrix.SetElement(2, 3, pe[2])
    td.tipTransformNode[index-1].SetMatrixTransformToParent(matrix)
    
    # if the tracking data is current:
    if self.currentTrackingDataNodeID == tdnode.GetID() and self.resliceCath == index:
        if self.reslice[0]:
          self.resliceDriverLogic.SetDriverForSlice(td.tipTransformNode[index-1].GetID(), self.sliceNodeRed)
          self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_AXIAL, self.sliceNodeRed)
        else:
          self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeRed)
          self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeRed)
        if self.reslice[1]:
          self.resliceDriverLogic.SetDriverForSlice(td.tipTransformNode[index-1].GetID(), self.sliceNodeYellow)
          self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_SAGITTAL, self.sliceNodeYellow)
        else:
          self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeYellow)
          self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeYellow)
        
        if self.reslice[2]:
          self.resliceDriverLogic.SetDriverForSlice(td.tipTransformNode[index-1].GetID(), self.sliceNodeGreen)
          self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_CORONAL, self.sliceNodeGreen)
        else:
          self.resliceDriverLogic.SetDriverForSlice('', self.sliceNodeGreen)
          self.resliceDriverLogic.SetModeForSlice(self.resliceDriverLogic.MODE_NONE, self.sliceNodeGreen)

    self.updateTipModelNode(td.tipModelNode[index-1], td.tipPoly[index-1], p0, pe, td.cmRadius[index-1], td.cmModelColor[index-1], td.cmOpacity[index-1])


  def onConnectedEvent(self, caller, event):
    #if self.widget != None:
    #  self.widget.updateGUI()
    pass


  def onDisconnectedEvent(self, caller, event):
    #if self.widget != None:
    #  self.widget.updateGUI()
    pass

  def updateTipModelNode(self, tipModelNode, poly, p0, pe, radius, color, opacity):
    #tipModel = self.scene.CreateNodeByClass('vtkMRMLModelNode')

    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    points.SetNumberOfPoints(2)
    cellArray.InsertNextCell(2)
    
    points.SetPoint(0, p0)
    cellArray.InsertCellPoint(0)
    points.SetPoint(1, pe)
    cellArray.InsertCellPoint(1)

    poly.Initialize()
    poly.SetPoints(points)
    poly.SetLines(cellArray)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetInputData(poly)
    tubeFilter.SetRadius(radius)
    tubeFilter.SetNumberOfSides(20)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius*2.0)
    sphere.SetCenter(pe)
    sphere.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tubeFilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tubeFilter.GetOutputPort())
    apd.Update()
    
    tipModelNode.SetAndObservePolyData(apd.GetOutput())
    tipModelNode.Modified()

    tipDispID = tipModelNode.GetDisplayNodeID()
    if tipDispID == None:
      tipDispNode = self.scene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      self.scene.AddNode(tipDispNode)
      tipDispNode.SetScene(self.scene)
      tipModelNode.SetAndObserveDisplayNodeID(tipDispNode.GetID());
      tipDispID = tipModelNode.GetDisplayNodeID()
      
    tipDispNode = self.scene.GetNodeByID(tipDispID)
      
    tipDispNode.SetColor(color)
    tipDispNode.SetOpacity(opacity)
    tipDispNode.SliceIntersectionVisibilityOn()
    tipDispNode.SetSliceDisplayModeToIntersection()
    

  def onIncomingNodeModifiedEvent(self, caller, event):
    print("onIncomingNodeModifiedEvent(self, caller, event)")
    self.onMessageReceived(caller)


  def onNodeRemovedEvent(self, caller, event, obj=None):
    delkey = ''
    if obj == None:
      for k in self.eventTag:
        node = self.scene.GetNodeByID(k)
        if node == None:
          delkey = k
          break

    if delkey != '':
      del self.eventTag[delkey]

  def activateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    
    if tdnode:
      print("Observer added.")
      # Since TrackingDataBundle does not invoke ModifiedEvent, obtain the first child node
      if tdnode.GetNumberOfTransformNodes() > 0:
        childNode = tdnode.GetTransformNode(1)
        childNode.SetAttribute('MRTracking.parent', tdnode.GetID())
        td.eventTag = childNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        return True
      else:
        return False  # Could not add observer.

  
  def deactivateTracking(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    tdnode = slicer.mrmlScene.GetNodeByID(self.currentTrackingDataNodeID)
    if tdnode:
      if tdnode.GetNumberOfTransformNodes() > 0:
        childNode = tdnode.GetTransformNode(1)
        td.eventTag = childNode.RemoveObserver(td.eventTag)
        td.eventTag = ''
        return True
      else:
        return False

  def isTrackingActive(self):
    td = self.TrackingData[self.currentTrackingDataNodeID]
    return td.isActive()
    
      
