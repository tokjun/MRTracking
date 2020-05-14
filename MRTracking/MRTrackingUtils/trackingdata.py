#------------------------------------------------------------
#
# TrakcingData class
#

class TrackingData:

  def __init__(self):
    
    #slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.widget = None
    self.eventTag = ''

    # self.activeTrackingDataNodeID = ''

    self.curveNodeID = ''
    
    self.opacity = [1.0, 1.0]
    self.radius = [0.5, 0.5]
    self.modelColor = [[0.0, 0.0, 1.0], [1.0, 0.359375, 0.0]]

    # Tip model
    self.tipLength = [10.0, 10.0]
    self.coilPositions = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    self.tipModelNode = [None, None]
    self.tipTransformNode = [None, None]
    self.tipPoly = [None, None]
    self.showCoilLabel = False
    self.activeCoils1 = [False, False, False, False, True, True, True, True]
    self.activeCoils2 = [True, True, True, True, False, False, False, False]

    # Coil order (True if Distal -> Proximal)
    self.coilOrder1 = True
    self.coilOrder2 = True
    
    self.axisDirection = [1.0, 1.0, 1.0]


  def isActive(self):
    if self.eventTag == '':
      return False
    else:
      return True

    
      
