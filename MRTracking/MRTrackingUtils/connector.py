import ctk
import qt
import slicer

#------------------------------------------------------------
#
# MRTrackingIGTLConnector class
#

class MRTrackingIGTLConnector():

  def __init__(self, cname="Connector"):

    self.cname = cname
    self.port = 18944

    self.connectorSelector = None
    self.portSpinBox = None
    self. activeConnectionCheckBox = None 
    
  def buildGUI(self, parent, minimal=False, createNode=False):

    # 
    # If 'minimal' is set to True, buildGUI() creates a shrinked GUI to save space.
    #
    
    if self.connectorSelector == None:
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
        
    if self.portSpinBox == None:
      self.portSpinBox = qt.QSpinBox()
      self.portSpinBox.objectName = 'PortSpinBox'
      self.portSpinBox.setMaximum(64000)
      self.portSpinBox.setValue(self.port)
      self.portSpinBox.setToolTip("Port number of the server")
      
    if self.activeConnectionCheckBox == None:
      self.activeConnectionCheckBox = qt.QCheckBox()
      self.activeConnectionCheckBox.checked = 0
      self.activeConnectionCheckBox.enabled = 0
      self.activeConnectionCheckBox.setToolTip("Activate OpenIGTLink connection")
      
    if minimal == False:
      
      connectorGroupBox = ctk.ctkCollapsibleGroupBox()
      connectorGroupBox.title = self.cname
      parent.addWidget(connectorGroupBox)
      connectorFormLayout = qt.QFormLayout(connectorGroupBox)
      connectorFormLayout.addRow("Connector: ", self.connectorSelector)
      connectorFormLayout.addRow("Port: ", self.portSpinBox)
      connectorFormLayout.addRow("Active: ", self.activeConnectionCheckBox)

    else:

      connectorFormLayout = parent
      
      frame = qt.QFrame()
      boxLayout = qt.QHBoxLayout(frame)
      boxLayout.addWidget(self.connectorSelector)
      boxLayout.addWidget(self.portSpinBox)
      boxLayout.addWidget(self.activeConnectionCheckBox)
      connectorFormLayout.addRow(self.cname + ": ", frame)

    if createNode:
      cnode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLIGTLConnectorNode')
      cnode.SetName(self.cname)
      cnode.SetTypeServer(self.port)
      slicer.mrmlScene.AddNode(cnode)
      self.connectorSelector.setCurrentNode(cnode)
      self.onConnectorSelected()


    #--------------------------------------------------
    # Connections
    #--------------------------------------------------
    self.connectorSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onConnectorSelected)
    self.activeConnectionCheckBox.connect('toggled(bool)', self.onActiveConnection)


  #--------------------------------------------------
  # GUI Slots
  #

  def onActiveConnection(self):
    
    if self.connectorSelector.currentNode() == None:
      return

    if self.activeConnectionCheckBox.checked == True:
      if self.connected() != True:
        port  = self.portSpinBox.value
        self.waitForClient(port)
    else:
      self.disconnect()

    #time.sleep(1)
    #self.updateGUI()


  def onConnectorSelected(self):
    cnode = self.connectorSelector.currentNode()    
    self.updateConnectorGUI()


    
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


  #--------------------------------------------------
  # OpenIGTLink
  #
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


  #def onConnectedEvent(self, caller, event):
  #  #if self.widget != None:
  #  #  self.widget.updateGUI()
  #  pass


  #def onDisconnectedEvent(self, caller, event):
  #  #if self.widget != None:
  #  #  self.widget.updateGUI()
  #  pass

    
