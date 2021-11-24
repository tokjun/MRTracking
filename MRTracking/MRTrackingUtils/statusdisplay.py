#------------------------------------------------------------
#
# Status Display Class
#

import qt
from MRTrackingUtils.connector import *
from MRTrackingUtils.catheter import *

class StatusDisplayWidget(qt.QWidget): 
  
  def __init__(self):
    super(StatusDisplayWidget, self).__init__(None)

    self.setMinimumHeight(200)
    self.setStyleSheet("background-color:black;")
    
    self.margin_x = 10
    self.margin_y = 10
    self.inner_margin_x = 5
    self.inner_margin_y = 5
    self.font_h   = 12
    self.font_w   = 8
    self.led_r_h    = 10
    self.led_r_w    = 10
    self.led_intv_x = 32
    self.name_w   = 160
    
    self.color_fg_base = qt.QColor(140,140,140)
    self.color_fg_high = qt.QColor(240,240,240)
    self.color_fg_low = qt.QColor(100,100,100)
    self.color_fg_act  = qt.QColor(50,255,50)
    self.color_fg_war = qt.QColor(255,255,50)
    self.color_fg_err = qt.QColor(255,50,50)

    self.pen_fg_base_frame = qt.QPen(self.color_fg_base, 2)
    self.pen_fg_base = qt.QPen(self.color_fg_base, 2)
    self.pen_fg_high = qt.QPen(self.color_fg_high, 2)
    self.pen_fg_act  = qt.QPen(self.color_fg_act , 2)
    self.pen_fg_on   = qt.QPen(self.color_fg_high, 2)
    self.pen_fg_off  = qt.QPen(self.color_fg_low , 2)
    
    self.pen_led_on  = qt.QPen(self.color_fg_high, 2)
    self.pen_led_off = qt.QPen(self.color_fg_low , 1)
    self.pen_led_rcv = qt.QPen(self.color_fg_act , 2)
    self.pen_led_war = qt.QPen(self.color_fg_war , 2)
    self.pen_led_err = qt.QPen(self.color_fg_err , 2)

    self.connector_box_h = self.font_h+self.inner_margin_y*2
    self.connector0_text_x = self.margin_x + self.inner_margin_x*2 + self.name_w
    self.connector1_text_x = self.inner_margin_x*3 + self.name_w
    self.connector_text_y = self.margin_y + self.inner_margin_y + self.font_h
    self.catheter_base_x = self.margin_x + self.inner_margin_x + self.name_w + self.inner_margin_x
    self.catheter_base_y = self.margin_y + self.font_h + self.inner_margin_y * 4
    self.catheter_row_h  = self.led_r_h*2+self.inner_margin_y

    self.repaintTimer = qt.QTimer()

    # MRTrackingIGTLConnector
    self.connectors = []
    self.catheters = None

    
  def addConnector(self, connector):
    self.connectors.append(connector)

    
  def setCatheterCollection(self, cc):
    self.catheters = cc

    
  def paintEvent(self, event=None):
    qp = qt.QPainter()
    
    qp.begin(self)

    w = self.width
    h = self.height
    mid_x = w/2

    qp.setPen(self.pen_fg_base_frame)
    qp.drawRect(self.margin_x,               self.margin_y, w/2-self.margin_x-self.inner_margin_x, self.connector_box_h)
    qp.drawRect(mid_x + self.inner_margin_x, self.margin_y, w/2-self.margin_x-self.inner_margin_x, self.connector_box_h)

    if len(self.connectors) >= 2:
      qp.setPen(self.pen_fg_base)
      qp.drawText(self.margin_x + self.inner_margin_x, self.connector_text_y, self.connectors[0].cname + ' :')
      qp.drawText(mid_x + self.inner_margin_x*2,       self.connector_text_y, self.connectors[1].cname + ' :')
      
      text_x = [self.connector0_text_x, self.connector1_text_x + mid_x]
      for i in range(2):
        if self.connectors[i].active():
          if self.connectors[i].connected():
            qp.setPen(self.pen_fg_act)
            qp.drawText(text_x[i], self.connector_text_y, "Connected")
          else:
            qp.setPen(self.pen_fg_on)
            qp.drawText(text_x[i], self.connector_text_y, "Waiting")
        else:
          qp.setPen(self.pen_fg_off)
          qp.drawText(text_x[i], self.connector_text_y, "Off")
      
    # Draw LEDs
    if self.catheters:
      n = self.catheters.getNumberOfCatheters()
      for i in range(n):
        cath = self.catheters.getCatheter(i)
        if cath:
          if cath.isActive():
            qp.setPen(self.pen_fg_act)
          else:
            qp.setPen(self.pen_fg_base)
          text_y = self.catheter_base_y + self.catheter_row_h*i + self.font_h
          qp.drawText(self.margin_x + self.inner_margin_x, text_y, cath.name + ' :')

          # Coil activation
          for j in range(8):
            c_id = j
            if not cath.coilOrder: # Proximal -> Distal
              c_id = 7-j
            
            if cath.activeCoils[c_id]:
              qp.setPen(self.pen_led_on)
            else:
              qp.setPen(self.pen_led_off)

            x = self.catheter_base_x+self.led_intv_x*j
            qp.drawEllipse(qt.QPoint(x+self.font_w/2, self.catheter_base_y+self.catheter_row_h*i+self.font_h/2),
                           self.led_r_w, self.led_r_h)
            qp.drawText(x, text_y, str(c_id+1))
      
    qp.end()


  def onRepaintTimer(self):
      
      self.repaint()
      
  def clean(self):
    
    self.stopTimer()

    
  def startTimer(self):

    if self.repaintTimer.isActive() == False:
      self.repaintTimer.timeout.connect(self.onRepaintTimer)
      self.repaintTimer.start(200)
      return True
    else:
      return False  # Could not add observer.

    
  def stopTimer(self):
    if self.repaintTimer.isActive() == True:
      self.repaintTimer.stop()


