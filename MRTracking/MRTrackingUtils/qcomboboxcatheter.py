import qt
from MRTrackingUtils.catheter import *
from qt import QComboBox

class QComboBoxCatheter(QComboBox):

  def __init__(self):
      
    super(QComboBoxCatheter, self).__init__()
    
    self.addDefaultItems()
    self.catheterList = []
    self.prevIndex = 0

    self.connect('currentIndexChanged(int)', self.onItemSelected)
    
    
  def addDefaultItems(self):

    self.insertSeparator(0)
    self.addItem('None')
    self.addItem('Create New Catheter')
    

  def clear():
      
    super(QComboBoxCatheter, self).clear()
    self.addDefaultItems()

    
  def addCatheter(self, cath):
      
    if isinstance(cath, Catheter):
      self.catheterList.append(cath)
      self.insertItem(len(self.catheterList)-1, cath.name)
      self.prevIndex = self.count - 4      # Last regular item (Note: self.count - 3 is a separator)
      self.setCurrentIndex(self.prevIndex)
        
    return len(self.catheterList)


  def getCatheter(self, name):
      
    for c in self.catheterList:
      if c.name == name:
        return c

    
  def onItemSelected(self, index):

    if index == self.count - 2:   # Special item: 'None'
      self.prevIndex = index
      print('None selected')
      pass   # Do nothing
    elif index == self.count - 1: # Special item: 'Create New Catheter'
      self.setCurrentIndex(self.count - 2)     # Tentatively set to 'None'
      self.createNewCatheter()
    else:                         # Regular item
      self.prevIndex = index
      print('%s is selected' % index)

      
  def createNewCatheter(self):
    print('Create New Catheter selected')
    newCath = Catheter('Cath1')

    self.addCatheter(newCath)
