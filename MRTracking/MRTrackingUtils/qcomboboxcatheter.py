import qt
from MRTrackingUtils.catheter import *
from qt import QComboBox, QInputDialog, Slot

class QComboBoxCatheter(QComboBox):

  # Signals
    
  def __init__(self):
      
    super(QComboBoxCatheter, self).__init__()
    
    self.addDefaultItems()
    self.collection = None
    self.prevIndex = 0
    self.addingDefaultItems = False

    self.currentIndexChanged.connect(self.onItemSelected) # Signal 'currentIndexChanged(int)'

    
  def setCatheterCollection(self, collection):

    # Remove the existing signal/slot connection
    if self.collection:
      self.collection.cleared.disconnect(self.onCatheterCleared)
      self.collection.added.disconnect(self.onCatheterAdded)
      self.collection.removed.disconnect(self.onCatheterRemoved)
      
    self.collection = collection
    self.updateItems()

    self.collection.cleared.connect(self.onCatheterCleared)
    self.collection.added.connect(self.onCatheterAdded)
    self.collection.removed.connect(self.onCatheterRemoved)

    
  def updateItems(self):

    if self.collection == None:
      return False

    # Turn off the signal while updating
    self.clearAll()
    
    n = self.collection.getNumberOfCatheters()
    for i in range(n):
      c = self.collection.getCatheter(i)
      self.insertItem(self.count-3, c.name)

  
  def addDefaultItems(self):

    self.disableAddition = True
    self.insertSeparator(0)
    self.addItem('None')
    self.addItem('Create New Catheter')
    self.disableAddition = False

    
  def clearAll(self):
    self.clear()
    self.addDefaultItems()


  def getCurrentCatheterIndex(self):
    #
    # Get the current catheter index. It gives the same value as QComboBox.currentIndex
    # *when a catheter is selected*; however, unlike QComboBox.currentIndex,
    # getCurrentCatheterIndex() can return 'None' when 'None' is selected. 
    #
    index = self.currentIndex
    if index > self.count-3: # If index points to 'None'
      return None
    else:
      return index
    
    
  def getCurrentCatheter(self):

    if self.collection == None:
      return None

    index = self.getCurrentCatheterIndex()

    if index == None:
      return None
    else:
      return self.collection.getCatheter(index)

  
  def getCatheter(self, index):
    if index >= 0 and index < self.collection.getNumberOfCatheters():
      return self.collection.getCatheter(index)
    else:
      None

  def setCurrentCatheterIndex(self, index):
    if index == None:
      self.setCurrentCatheterNone()
    else:
      self.setCurrentIndex(index)

      
  def setCurrentCatheterNone(self):
    self.setCurrentIndex(self.count-2)
      
    
  def onItemSelected(self, index):

    if index == self.count - 2:   # Special item: 'None'
      self.prevIndex = index
      #print('None selected')
      pass   # Do nothing
    elif index == self.count - 1: # Special item: 'Create New Catheter'
      if self.disableAddition == False and self.itemText(index) == 'Create New Catheter':
        self.setCurrentCatheterNone() # Tentatively set to 'None'
        self.createNewCatheter()
    else:                         # Regular item
      self.prevIndex = index

      
  def createNewCatheter(self):

    if self.collection == None:
      return False
    
    text = QInputDialog.getText(self, "Catheter Name Dialog", "Catheter Name:")
    if text:
      newCath = Catheter(text)
      self.collection.add(newCath)


  @Slot()
  def onCatheterCleared(self):
    self.clearAll()

    
  @Slot(int)
  def onCatheterAdded(self, index):

    prevIndex = self.getCurrentCatheterIndex()
    cath = self.collection.getCatheter(index)
    if cath == None:
      print('Error: Could not add a catheter to the ComboBox.')
      return
    
    self.insertItem(self.count-3, cath.name)
    #self.prevIndex = self.count-4      # Last regular item (Note: self.count - 3 is a separator)
    #self.setCurrentIndex(prevIndex)
    self.setCurrentCatheterIndex(prevIndex)
    

  @Slot(int)
  def onCatheterRemoved(self, index):

    if self.collection == None:
      return False
    
    self.removeItem(index)
    self.setCurrentCatheterNone() # self.setCurrentIndex(self.count-2) # Select 'None'
    
