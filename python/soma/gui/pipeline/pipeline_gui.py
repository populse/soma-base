from pprint import pprint
from PyQt4 import QtGui, QtCore
try:
  from traits.api import File
except ImportError:
  from enthought.traits.api import File

try:
  import capsul
  from capsul.sorted_dictionary import SortedDictionary
  from capsul.pipeline.pipeline import Switch
except ImportError:
  from soma.sorted_dictionary import SortedDictionary
  from soma.pipeline.pipeline import Switch

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

BLUE_1 = QtGui.QColor.fromRgbF(0.7, 0.7, 0.9, 1)
BLUE_2 = QtGui.QColor.fromRgbF(0.5, 0.5, 0.7, 1)
LIGHT_BLUE_1 = QtGui.QColor.fromRgbF(0.95, 0.95, 1.0, 1)
LIGHT_BLUE_2 = QtGui.QColor.fromRgbF(0.85, 0.85, 0.9, 1)

GRAY_1 = QtGui.QColor.fromRgbF(0.7, 0.7, 0.8, 1)
GRAY_2 = QtGui.QColor.fromRgbF(0.4, 0.4, 0.4, 1)
LIGHT_GRAY_1 = QtGui.QColor.fromRgbF(0.7, 0.7, 0.8, 1)
LIGHT_GRAY_2 = QtGui.QColor.fromRgbF(0.6, 0.6, 0.7, 1)

SAND_1 = QtGui.QColor.fromRgb(204, 178, 76)
SAND_2 = QtGui.QColor.fromRgb(255, 229, 127)
LIGHT_SAND_1 = QtGui.QColor.fromRgb(217, 198, 123)
LIGHT_SAND_2 = QtGui.QColor.fromRgb(255, 241, 185)

GOLD_1 = QtGui.QColor.fromRgb(255, 229, 51)
GOLD_2 = QtGui.QColor.fromRgb(229, 153, 51)
LIGHT_GOLD_1 = QtGui.QColor.fromRgb(225, 239, 131)
LIGHT_GOLD_2 = QtGui.QColor.fromRgb(240, 197, 140)
#LIGHT_GOLD_1 = QtGui.QColor.fromRgb(225, 236, 111)
#LIGHT_GOLD_2 = QtGui.QColor.fromRgb(236, 179, 104)

BROWN_1 = QtGui.QColor.fromRgb(233, 198, 175)
BROWN_2 = QtGui.QColor.fromRgb(211, 141, 95)
LIGHT_BROWN_1 = QtCore.Qt.gray #TBI
LIGHT_BROWN_2 = QtCore.Qt.gray #TBI

RED_1 = QtGui.QColor.fromRgb(175, 54, 16)
RED_2 = QtGui.QColor.fromRgb(234, 131, 31)
LIGHT_RED_1 = QtCore.Qt.gray #TBI
LIGHT_RED_2 = QtCore.Qt.gray #TBI

PURPLE_1 = QtGui.QColor.fromRgb(212, 199, 204)
PURPLE_2 = QtGui.QColor.fromRgb(200, 183, 190)
DEEP_PURPLE_1 = QtGui.QColor.fromRgb(157, 126, 139)
DEEP_PURPLE_2 = QtGui.QColor.fromRgb(121, 97, 124)






#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class Plug( QtGui.QGraphicsPolygonItem ):
  
  def __init__(self, height, width, activated=True, optional=False, parent=None):
    super(Plug, self).__init__(parent)
    if optional:
      if activated:
        color = QtCore.Qt.darkGreen
      else:
        color = QtGui.QColor( '#BFDB91' )
    else:
      if activated:
        color = QtCore.Qt.black
      else:
        color = QtCore.Qt.gray
    if True:
      brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
      brush.setColor(color)
      polygon = QtGui.QPolygonF( [ QtCore.QPointF( 0,0 ),
                                   QtCore.QPointF( width, (height-5)/2.0 ),
                                   QtCore.QPointF( 0, height-5 ) 
                                 ] )
      self.setPen(QtGui.QPen(QtCore.Qt.NoPen))
    else:
      brush = QtGui.QBrush(QtCore.Qt.Dense4Pattern)
      brush.setColor(color)
      polygon = QtGui.QPolygonF( [ QtCore.QPointF( 0, 0 ),
                                   QtCore.QPointF( width/3.0, (height-5)/4.0 ),
                                   QtCore.QPointF( width/3.0, 0 ),
                                   QtCore.QPointF( width, (height-5)/2.0 ),
                                   QtCore.QPointF( width/3.0, (height-5) ),
                                   QtCore.QPointF( width/3.0, (height-5)*0.75 ),
                                   QtCore.QPointF( 0, height-5 ),
                                 ] )
    self.setPolygon( polygon )
    self.setBrush( brush )
    self.setZValue( 3 )

  def get_plug_point(self):
    return self.mapToParent( QtCore.QPointF(self.boundingRect().size().width()/2.0, self.boundingRect().size().height()/2.0) )

    
  

class NodeGWidget(QtGui.QGraphicsItemGroup):
  _colors = { 
    'default': ( BLUE_1, BLUE_2, LIGHT_BLUE_1, LIGHT_BLUE_2 ),
    'switch': ( SAND_1, SAND_2, LIGHT_SAND_1, LIGHT_SAND_2 ),
  }
  
  def __init__( self, name, parameters, 
                number=None, active=True,
                style= None, parent=None ):
    super(NodeGWidget, self).__init__(parent)
    if style is None:
      style = 'default'
    self.name = name
    self.parameters = parameters
    self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
    self.in_plugs = {}
    self.out_plugs = {}
    self.active = active
    self.number = number
    #gradient = QtGui.QRadialGradient(50, 50, 50, 50, 50)

    
    if self.active:
      color_1, color_2 = self._colors[ style ][ 0:2 ]
    else:
      color_1, color_2 = self._colors[ style ][ 2:4 ]
    gradient = QtGui.QLinearGradient( 0, 0, 0, 50 )
    gradient.setColorAt( 0, color_1 )
    gradient.setColorAt( 1, color_2 )
    self.bg_brush = QtGui.QBrush( gradient )

    if self.active:
      color_1 = GRAY_1
      color_2 = GRAY_2
    else:
      color_1 = LIGHT_GRAY_1
      color_2 = LIGHT_GRAY_2
    gradient = QtGui.QLinearGradient( 0, 0, 0, 50 )
    gradient.setColorAt( 1, color_1 )
    gradient.setColorAt( 0, color_2 )
    self.title_brush = QtGui.QBrush( gradient )

    #title_font = QtGui.QApplication.font()
    #title_font.setWeight(QtGui.QFont.Bold)

    self._build()

  def get_title(self):
    if self.number is None:
      return self.name
    else:
      return self.name + ":" + repr(self.number)

      
  def _build(self):
    margin = 5
    plug_width = 12
    name = self.name
    self.title = QtGui.QGraphicsTextItem(self.get_title(), self)
    font = self.title.font()
    font.setWeight(QtGui.QFont.Bold)
    self.title.setFont(font)
    self.title.setPos(margin, margin)
    self.title.setZValue(2)
    # always add to group after setPos
    self.addToGroup(self.title)

    pos = margin + margin + self.title.boundingRect().size().height()
    for in_param, pipeline_plug in self.parameters.iteritems():
      output = (not pipeline_plug.output if self.name in ('inputs','outputs') else pipeline_plug.output)
      if output:
        continue
      param_name = QtGui.QGraphicsTextItem(in_param, self)
      plug = Plug(param_name.boundingRect().size().height(), plug_width, activated=pipeline_plug.activated, optional=pipeline_plug.optional, parent=self )
      param_name.setZValue(2)
      plug.setPos(margin, pos)
      param_name.setPos(plug.boundingRect().size().width() + margin, pos)
      self.addToGroup(param_name)
      self.addToGroup(plug)
      self.in_plugs[in_param] = plug
      pos = pos + param_name.boundingRect().size().height()


    for out_param, pipeline_plug in self.parameters.iteritems():
      output = (not pipeline_plug.output if self.name in ('inputs','outputs') else pipeline_plug.output)
      if not output:
        continue
      param_name = QtGui.QGraphicsTextItem(out_param, self)
      plug = Plug(param_name.boundingRect().size().height(), plug_width, activated=pipeline_plug.activated, optional=pipeline_plug.optional, parent=self)
      param_name.setZValue(2)
      param_name.setPos(plug.boundingRect().size().width() + margin, pos)
      plug.setPos(plug.boundingRect().size().width() + margin + param_name.boundingRect().size().width() + margin, pos)
      self.addToGroup(plug)
      self.addToGroup(param_name) 
      self.out_plugs[out_param] = plug
      pos = pos + param_name.boundingRect().size().height()

    self.box = QtGui.QGraphicsRectItem(self)
    self.box.setBrush(self.bg_brush)
    self.box.setPen(QtGui.QPen(QtCore.Qt.NoPen))
    self.box.setZValue(-1)
    self.addToGroup(self.box)
    self.box.setRect(self.boundingRect())

    self.box_title = QtGui.QGraphicsRectItem(self)
    rect = self.title.mapRectToParent(self.title.boundingRect())
    rect.setWidth(self.boundingRect().width())
    self.box_title.setRect(rect)
    self.box_title.setBrush(self.title_brush)
    self.box_title.setPen(QtGui.QPen(QtCore.Qt.NoPen))
    self.addToGroup(self.box_title)

  def postscript( self, file_name ):
    printer = QtGui.QPrinter( QtGui.QPrinter.HighResolution )
    printer.setOutputFormat( QtGui.QPrinter.PostScriptFormat )
    printer.setOutputFileName( file_name );
    #qreal xmargin = contentRect.width()*0.01;
    #qreal ymargin = contentRect.height()*0.01;
    #printer.setPaperSize(10*contentRect.size()*1.02,QPrinter::DevicePixel);
    #printer.setPageMargins(xmargin,ymargin,xmargin,ymargin,QPrinter::DevicePixel);
    painter = QtGui.QPainter()
    painter.begin( printer )
    painter.setPen( QtCore.Qt.blue )
    painter.setFont( QtGui.QFont( 'Arial', 30 ) )
    painter.drawText( 0, 0, 'Ca marche !' )
    #render(&painter,QRectF(QPointF(0,0),10*contentRect.size()),contentRect);
    painter.end()


class Link(QtGui.QGraphicsPathItem):

  def __init__(self, origin, target, active, weak, parent=None):
    super(Link, self).__init__(parent)
    pen = QtGui.QPen()
    pen.setWidth(2)
    if active:
      pen.setBrush(RED_2)
    else:
      pen.setBrush(QtCore.Qt.gray)
    if weak:
        pen.setStyle(QtCore.Qt.DashLine)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)

    path = QtGui.QPainterPath()
    path.moveTo(origin.x(), origin.y())
    path.cubicTo(origin.x() + 100, origin.y(),
                 target.x() - 100, target.y(),
                 target.x(), target.y())
    self.setPath(path)
    self.setPen(pen)
    self.setZValue( 0.5 )

  def update(self, origin, target):
    path = QtGui.QPainterPath()
    path.moveTo(origin.x(), origin.y())
    path.cubicTo(origin.x() + 100, origin.y(),
                 target.x() - 100, target.y(),
                 target.x(), target.y())

    self.setPath(path)


class PipelineScene(QtGui.QGraphicsScene):
  
  def __init__( self, parent=None ):
    super( PipelineScene, self ).__init__( parent )
    self.gnodes = {}
    self.glinks = {}
    self._pos = 50
    self.pos = {}

    self.changed.connect( self.update_paths )
  
  def add_node( self, name, gnode ):
    self.addItem( gnode )
    pos = self.pos.get( name )
    if pos is None:
      gnode.setPos( self._pos, self._pos )
      self._pos += 100
    else:
      gnode.setPos( pos )
    self.gnodes[ name ] = gnode
  
  
  def add_link( self, source, dest, active, weak ):
    source_gnode_name, source_param = source
    if not source_gnode_name:
      source_gnode_name  = 'inputs'
    source_gnode = self.gnodes[ source_gnode_name ]
    dest_gnode_name, dest_param = dest
    if not dest_gnode_name:
      dest_gnode_name = 'outputs'
    dest_gnode = self.gnodes[ dest_gnode_name ]
    if dest_param in dest_gnode.in_plugs:
      glink = Link( source_gnode.mapToScene( source_gnode.out_plugs[ source_param ].get_plug_point() ),
                    dest_gnode.mapToScene( dest_gnode.in_plugs[ dest_param ].get_plug_point() ),
                    active, weak )
      self.glinks[ ( (source_gnode_name, source_param), (dest_gnode_name, dest_param) ) ] = glink
      self.addItem( glink )

    
  def update_paths(self):
    for i in self.items():
      if isinstance( i, NodeGWidget ):
        self.pos[ i.name ] = i.pos()

    for source_dest, glink in self.glinks.iteritems():
      source, dest = source_dest
      source_gnode_name, source_param = source
      dest_gnode_name, dest_param = dest
      source_gnode = self.gnodes[ source_gnode_name ]
      dest_gnode = self.gnodes[ dest_gnode_name ]
      glink.update( source_gnode.mapToScene( source_gnode.out_plugs[ source_param ].get_plug_point() ),
                    dest_gnode.mapToScene( dest_gnode.in_plugs[ dest_param ].get_plug_point() ) )
                     

  def set_pipeline( self, pipeline ):
    pipeline_inputs = SortedDictionary()
    pipeline_outputs = SortedDictionary()
    for name, plug in pipeline.nodes[ '' ].plugs.iteritems():
      if plug.output:
        pipeline_outputs[name]=plug
      else:
        pipeline_inputs[name]=plug
    if pipeline_inputs:
      self.add_node( 'inputs', NodeGWidget( 'inputs', pipeline_inputs, active=True ) )
    for node_name, node in pipeline.nodes.iteritems():
      if not node_name: continue
      if isinstance( node, Switch ):
        style = 'switch'
      else:
        style = None
      self.add_node( node_name, NodeGWidget( node_name, node.plugs, active=node.activated, style=style ) )
    if pipeline_outputs:
      self.add_node( 'outputs', NodeGWidget( 'outputs', pipeline_outputs, active=True ) )

    for source_node_name, source_node in pipeline.nodes.iteritems():
      for source_parameter, source_plug in source_node.plugs.iteritems():
        for dest_node_name, dest_parameter, dest_node, dest_plug, weak_link in source_plug.links_to:
          self.add_link((source_node_name, source_parameter ), ( dest_node_name, dest_parameter ), 
                         active=source_plug.activated and dest_plug.activated,
                         weak=weak_link)
  
  

class PipelineView(QtGui.QGraphicsView):

  def __init__(self, pipeline, parent=None):
    super( PipelineView, self ).__init__( parent )
    self.scene = None
    self.set_pipeline( pipeline )
    
  
  def _set_pipeline( self, pipeline ):
    if self.scene:
      pos = self.scene.pos
      pprint( dict( ( i, ( j.x(), j.y() ) ) for i, j in pos.iteritems() ) )
    else:
      pos = dict( ( i, QtCore.QPointF( *j ) ) for i, j in pipeline.node_position.iteritems() )
    self.scene = PipelineScene()
    self.scene.pos = pos
    self.scene.set_pipeline( pipeline )
    self.setWindowTitle( pipeline.name )
    self.setScene(self.scene)

    
  def set_pipeline( self, pipeline ):
    self._set_pipeline( pipeline )
    
    # Setup callback to update view when pipeline state is modified                         
    def reset_pipeline():
      self._set_pipeline( pipeline )
    pipeline.on_trait_change( reset_pipeline, 'selection_changed' )

  def zoom_in(self):
    self.scale(1.2, 1.2)

  def zoom_out(self):
    self.scale(1.0/1.2, 1.0/1.2)

  def wheelEvent(self, event):
    if event.modifiers() == QtCore.Qt.ControlModifier:
      if event.delta() < 0:
        self.zoom_out()
      else:
        self.zoom_in()
      event.accept()
    else:
      QtGui.QGraphicsView.wheelEvent(self, event)

      
      
if __name__ == '__main__':
  import sys
  try:
    from capsul.pipeline.pipeline import Morphologist, GreyWhite
  except ImportError:
    from soma.pipeline.pipeline import Morphologist, GreyWhite
  from soma.gui.widget_controller_creation import ControllerWidget
  from soma.functiontools import SomaPartial as partial
  
  app = QtGui.QApplication( sys.argv )

  morphologist = Morphologist()
  morphologist.select_normalization = 'none'
  #morphologist.nodes[ 'left_grey_white' ].enabled = False
  view1 = PipelineView( morphologist )
  view1.show()
  def set_morphologist_pipeline():
    view1.set_pipeline( morphologist )
  #morphologist.nodes_activation.on_trait_change( set_morphologist_pipeline )
  morphologist.on_trait_change( set_morphologist_pipeline, 'selection_changed' )
  #morphologist.on_trait_change( partial( view1.set_pipeline, morphologist ), 'select_normalization' )
  #view2 = PipelineView( GreyWhite() )
  #view2.show()

  cw = ControllerWidget( morphologist, live=True )
  cw.show()
  
  #morphologist.trait( 'nobias' ).hidden = True
  #cw.controller.user_traits_changed = True
  #printer = QtGui.QPrinter( QtGui.QPrinter.HighResolution )
  #printer.setOutputFormat( QtGui.QPrinter.PostScriptFormat )
  #printer.setOutputFileName( sys.argv[ 1 ] )
  #painter = QtGui.QPainter()
  #painter.begin( printer )

  #scale = QtGui.QTransform.fromScale( .5, .5 )
  #painter.setTransform( scale )
  #view1.scene.render( painter )
  #painter.end()
  
  app.exec_()
  del view1
  #del view2

