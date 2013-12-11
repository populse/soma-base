import sys
try:
  from traits.api import File, Float, Enum, Str, Int, Bool, List, Tuple, Instance, Event, CTrait
except ImportError:
  from enthought.traits.api import File, Float, Enum, Str, Int, Bool, List, Tuple, Instance, Event,CTrait

from soma.controller import Controller
from soma.sorted_dictionary import SortedDictionary
from soma.global_naming import GlobalNaming
from soma.functiontools import SomaPartial
from soma.pipeline.process_with_fom import ProcessWithFom
from soma.pipeline.process import Process
from soma.pipeline.pipeline_with_fom import PipelineWithFom
    
class Plug( Controller ):
  enabled = Bool( default_value=True )
  activated = Bool( default_value=False )
  output = Bool( default_value=False )
  optional = Bool( default_value=False )
  
  def __init__( self, **kwargs ):
    super( Plug, self ).__init__( **kwargs )
    # link -> ( node, plug )
    self.links_to = set()
    self.links_from = set()

    
class Node( Controller ):
  name = Str()
  enabled = Bool( default_value=True )
  activated = Bool( default_value=False )
  
  def __init__( self, pipeline, name, inputs, outputs ):
    super( Node, self ).__init__()
    self.pipeline = pipeline
    self.name = name
    self.plugs = {}
    self._callbacks = {}
    for i in inputs:
      if isinstance( i, dict ):
        d = i.copy()
        name = d.pop( 'name' )
        d[ 'output' ] = False
        plug = Plug( **d )
      else:
        name = i
        plug = Plug( output=False )
      self.plugs[ name ] = plug
      #plug.on_trait_change( self.update_plugs_hook, 'enabled' )
      plug.on_trait_change( pipeline.update_nodes_and_plugs_activation, 'enabled' )
    for i in outputs:
      plug = Plug( output=True )
      self.plugs[ i ] = plug
      plug.on_trait_change( pipeline.update_nodes_and_plugs_activation, 'enabled' )
    self.on_trait_change( pipeline.update_nodes_and_plugs_activation, 'enabled' )

  
  def connect( self, source_parameter, dest_node, dest_parameter ):
    callback = dest_node.connection_callback( dest_parameter )
    self._callbacks[ ( source_parameter, dest_node, dest_parameter ) ] = callback
    self.on_trait_change( callback, source_parameter )

  def connection_callback( self, parameter ):
    def callback( value ):
      setattr( self, parameter, value )
    return callback

  
  def get_trait( self, name ):
    return self.trait( name )

      
  
class ProcessNode( Node ):
  def __init__( self, pipeline, name, process, **kwargs ):
    self.process = Process.get_instance( process, **kwargs )
    self.kwargs = kwargs
    inputs = []
    outputs = []
    for parameter, trait in self.process.user_traits().iteritems():
      if parameter in ( 'nodes_activation', 'selection_changed' ):
        continue
      if isinstance( trait.handler, File ) and trait.handler.output:
        outputs.append( parameter )
      else:
        inputs.append( dict( name=parameter, optional=bool(trait.optional) ) )
    super( ProcessNode, self ).__init__( pipeline, name, inputs, outputs )

  def connect( self, source_parameter, dest_node, dest_parameter ):
    callback = dest_node.connection_callback( dest_parameter )
    #callback = SomaPartial( dest_node.set_parameter, dest_parameter )
    self._callbacks[ ( source_parameter, dest_node, dest_parameter ) ] = callback
    self.process.on_trait_change( callback, source_parameter )

  def connection_callback( self, parameter ):
    def callback( value ):
      setattr( self.process, parameter, value )
    return callback
  
  def get_trait( self, name ):
    return self.process.trait( name )
    


class PipelineNode( ProcessNode ):
  pass

    
    
class Switch( Node ):
  def __init__( self, pipeline, name, inputs, output ):
    self.add_trait( 'switch', Enum( *inputs ) )
    super( Switch, self ).__init__( pipeline, name, [ 'switch' ] + [ dict( name=i, optional=True ) for i in inputs], [ output ] )
    for n in inputs[ 1: ]:
      self.plugs[ n ].enabled = False
    #self.update_plugs()
  
  
  def _switch_changed( self, old, new ):
    self.plugs[ old ].enabled = False
    self.plugs[ new ].enabled = True
    #self.update_plugs()
    self.pipeline.update_nodes_and_plugs_activation()

  #def update_plugs( self ):
    #self.update_plugs_activation()


class Pipeline( Process ):
  
  selection_changed = Event()
  
  def __init__( self, **kwargs ):
    super( Pipeline, self ).__init__( **kwargs )
    super( Pipeline, self ).add_trait( 'nodes_activation', Instance( Controller ) )
    self.list_process_in_pipeline=[]
    self.attributes={}
    self.nodes_activation = Controller()
    self.nodes = SortedDictionary()
    self.node_position = {}
    self.pipeline_node = PipelineNode( self, '', self )
    self.nodes[ '' ] = self.pipeline_node
    self.do_not_export = set()
    self.pipeline_definition()

    for node_name, node in self.nodes.iteritems():
      for parameter_name, plug in node.plugs.iteritems():
        if parameter_name in ( 'nodes_activation', 'selection_changed' ):
          continue
        if ( node_name, parameter_name ) not in self.do_not_export and not plug.links_to and not plug.links_from:
          self.export_parameter( node_name, parameter_name )
    
    self.update_nodes_and_plugs_activation()
          
          
  def add_trait( self, name, trait ):
    super( Pipeline, self ).add_trait( name, trait )
    output = isinstance( trait, File ) and bool( trait.output )
    plug = Plug( output=output )
    self.pipeline_node.plugs[ name ] = plug
    ##plug.on_trait_change( self.pipeline_node.update_plugs_hook, 'enabled' )
    #if isinstance(trait,CTrait):
	#print 'trait in process'
    #else:
	#print trait
	#plug.on_trait_change(self.trait_in_pipeline_change, name)
	
    #print 'traittype',trait.is_trait_type( Instance)
    #print plug.trait
    plug.on_trait_change( self.update_nodes_and_plugs_activation, 'enabled' )
    #print 'nodesss',self.nodes
    #print 'nodes position',self.node_position

	
    
    
  #def trait_in_pipeline_change(self,object, name, old, new):
      #print 'trait_in_pipeline_change'
      #print object,name,old,new

    
  
  def add_process( self, name, process, **kwargs ):
    if name in self.nodes:
      raise ValueError( 'Pipeline cannot have two nodes with the same name : %s' % name )
    self.nodes[ name ] = node =ProcessNode( self, name, process, **kwargs )
    for parameter_name in self.nodes[ name ].plugs:
      if parameter_name in kwargs:
        self.do_not_export.add( ( name, parameter_name ) )
    self.nodes_activation.add_trait( name, Bool )
    setattr( self.nodes_activation, name, node.enabled )
    self.nodes_activation.on_trait_change( self._set_node_enabled, name )
    self.list_process_in_pipeline.append(process)

 	
  
  
  def add_switch( self, name, inputs, output ):
    if name in self.nodes:
      raise ValueError( 'Pipeline cannot have two nodes with the same name : %s' % name )
    node = Switch( self, name, inputs, output )
    self.nodes[ name ] = node
    self.export_parameter( name, 'switch', name )


  def parse_link( self, link ):
    source, dest = link.split( '->' )
    source_node_name, source_parameter, source_node, source_plug = self.parse_parameter( source )
    dest_node_name, dest_parameter, dest_node, dest_plug = self.parse_parameter( dest )
    return ( source_node_name, source_parameter, source_node, source_plug, dest_node_name, dest_parameter, dest_node, dest_plug )
  
  
  def parse_parameter( self, name ):
    dot = name.find( '.' )
    if dot < 0:
      node_name = ''
      node = self.pipeline_node
      parameter_name = name
    else:
      node_name = name[ :dot ]
      node = self.nodes.get( node_name )
      if node is None:
        raise ValueError( '%s is not a valid node name' % node_name )
      parameter_name = name[ dot+1: ]
    if parameter_name not in node.plugs:
      raise ValueError( '%s is not a valid parameter name for node %s' % ( parameter_name, ( node_name if node_name else 'pipeline' ) ) )
    return node_name, parameter_name, node, node.plugs[ parameter_name ] 

    
  def add_link( self, link ):
    source, dest = link.split( '->' )
    source_node_name, source_parameter, source_node, source_plug = self.parse_parameter( source )
    dest_node_name, dest_parameter, dest_node, dest_plug = self.parse_parameter( dest )
    if not source_plug.output and source_node is not self.pipeline_node:
      raise ValueError( 'Cannot link from an input plug : %s' % link )
    if dest_plug.output and source_node is not self.pipeline_node:
      raise ValueError( 'Cannot link to an output plug : %s' % link )
    source_plug.links_to.add( ( dest_node_name, dest_parameter, dest_node, dest_plug ) )
    dest_plug.links_from.add( ( source_node_name, source_parameter, source_node, source_plug ) )
    source_node.connect( source_parameter, dest_node, dest_parameter )
    dest_node.connect( dest_parameter, source_node, source_parameter )
    #source_node.update_plugs()
    #dest_node.update_plugs()
  
  
  def export_parameter( self, node_name, parameter_name, pipeline_parameter='' ):
    node = self.nodes[ node_name ]
    trait = node.get_trait( parameter_name )
    if trait is None:
      raise ValueError( 'Node %(n)s (%(nn)s) has no parameter %(p)s' % dict( n=node_name, nn=node.name, p=parameter_name ) )
    if pipeline_parameter is None:
      self.do_not_export.add( ( node_name,  parameter_name ) )
    else:
      if not pipeline_parameter:
        pipeline_parameter = parameter_name
      if pipeline_parameter in self.user_traits():
        raise ValueError( 'Parameter %(pn)s of node %(nn)s cannot be exported to pipeline parameter %(pp)s' % dict( nn=node_name, pn=parameter_name, pp=pipeline_parameter ) )
      self.add_trait( pipeline_parameter, trait )
      if isinstance( trait.handler, File ) and trait.handler.output:
        self.add_link( '%s.%s->%s' % ( node_name, parameter_name, pipeline_parameter ) )
      else:
        self.add_link(  '%s->%s.%s' % ( pipeline_parameter, node_name, parameter_name ) )
  
  
  def _set_node_enabled( self, node_name, value ):
    node = self.nodes.get( node_name )
    if node:
      node.enabled = value
  
  def update_nodes_and_plugs_activation( self ):
    print 'update_nodes_and_plugs_activation'
    stack = set()
    for node in self.nodes.itervalues():
      if isinstance( node, PipelineNode ):
        node.activated = node.enabled
        for plug in node.plugs.itervalues():
          plug.activated = node.activated and plug.enabled
      else:
        node.activated = False
        for plug in node.plugs.itervalues():
          plug.activated = False
      stack.add( node )
    while stack:
      new_stack = set()
      for node in stack:
        if isinstance( node, PipelineNode ):
          continue
        if node.enabled:
          node.activated = True
          for plug in node.plugs.itervalues():
            if plug.links_to:
              continue
            if plug.enabled:
              for nn, pn, n, p in plug.links_from:
                if p.activated:
                  plug.activated = True
                  break
              else:
                plug.activated = False
            else:
              plug.activated = False
            if not plug.activated and not plug.optional:
              node.activated = False
              break
          if node.activated:
            for plug in node.plugs.itervalues():
              if plug.enabled and plug.links_to:
                plug.activated = True
                for nn, pn, n, p in plug.links_to:
                  new_stack.add( n )
          else:
            for plug in node.plugs.itervalues():
              plug.activated = False  
      stack = new_stack
  
    stack = set( self.nodes.itervalues() )
    while stack:
      new_stack = set()
      for node in stack:
        if isinstance( node, PipelineNode ):
          continue
        if node.activated:
          output_connected = False
          for plug in node.plugs.itervalues():
            if plug.links_to:
              for nn, pn, n, p in plug.links_to:
                if p.activated:
                  break
              else:
                plug.activated = False
              if plug.activated:
                break
          else:
            # No output connected to an activated plug
            # => desactivate the node
            node.activated = False
            for plug in node.plugs.itervalues():
              plug.activated = False  
              for nn, pn, n, p in plug.links_from:
                new_stack.add( n )
      stack = new_stack
      
    pipeline_node = self.nodes[ '' ]
    traits_changed = False
    for plug_name, plug in pipeline_node.plugs.iteritems():
      for nn, pn, n, p in plug.links_to.union( plug.links_from ):
        if p.activated:
          break
      else:
        plug.activated = False
      trait = self.trait( plug_name )
      if plug.activated:
        if getattr( trait, 'hidden', False ):
          trait.hidden = False
          traits_changed = True
      else:
        if not getattr( trait, 'hidden', False ):
          trait.hidden = True
          traits_changed = True
    self.selection_changed = True
    if traits_changed:
      self.user_traits_changed = True

  
  def workflow( self ):
    result = Workflow()
    
    heads = {}
    tails = {}
    stack = self.nodes.items()
    while stack:
      name, node = stack.pop( 0 )
      if node.activated and isinstance( node, ProcessNode ) and not isinstance( node, PipelineNode ):
        if isinstance( node.process, Pipeline ):
          workflow = node.process.workflow()
          result.add_workflow( workflow, prefix = name + '.' )
          heads[ node ] = workflow.head
          tails[ node ] = workflow.tail
        else:
          result.add_node( name, node.process )
          heads[ node ] = tails[ node ] = [ node.process ]
    
    stack = self.nodes.items()
    while stack:
      name, node = stack.pop( 0 )
      if node.activated:
        if isinstance( node, Switch ):
          nodes_from = set()
          nodes_to = set()
          for plug in node.plugs.itervalues():
            if plug.activated:
              for nn, pn, n, p in plug.links_from:
                if n.activated and isinstance( n, ProcessNode ) and not isinstance( n, PipelineNode ):
                  nodes_from.update( tails[ n ] )
              for nn, pn, n, p in plug.links_to:
                if n.activated and isinstance( n, ProcessNode ) and not isinstance( n, PipelineNode ):
                  nodes_to.update( heads[ n ] )
          for source_node in nodes_from:
            for dest_node in nodes_to:
              result.add_link( source_node, dest_node )
        elif isinstance( node, ProcessNode ) and not isinstance( node, PipelineNode ):
          for plug in node.plugs.itervalues():
            for nn, pn, n, p in plug.links_to:
              if n.activated and isinstance( n, ProcessNode ) and not isinstance( n, PipelineNode ):
                for source_node in tails[ node ]:
                  for dest_node in heads[ n ]:
                    result.add_link( source_node, dest_node )
    return result


  def __call__( self ):
    for name, process_node in self.workflow().ordered_nodes():
      process_node()

    

class Workflow( object ):
  def __init__( self ):
    self.nodes = {}
    self.links = {}
    self.head = set()
    self.tail = set()
    
  def add_node( self, name, node ):
    print '!add_node!', name, node
    self.nodes[ node ] = ( name, set() )
    self.head.add( node )
    self.tail.add( node )
  
  
  def add_link( self, source_node, dest_node ):
    source_ancestors = self.nodes[ source_node ][ 1 ]
    dest_ancestors = self.nodes[ dest_node ][ 1 ]
    if source_node in dest_ancestors:
      return
    if dest_node is source_ancestors:
      raise ValueError( 'Loop detected in worflow' )
    print '!add_link!', '%s->%s' % ( self.nodes[ source_node ][ 0 ], self.nodes[ dest_node ][ 0 ] )
    source_links_to, source_links_from = self.links.setdefault( source_node, ( set(), set() ) )
    dest_links_to, dest_links_from = self.links.setdefault( dest_node, ( set(), set() ) )
    ancestors_stack = [ source_node ]
    while ancestors_stack:
      ancestor = ancestors_stack.pop( 0 )
      ancestors_stack.extend( self.links.setdefault( ancestor, ( set(), set() ) )[ 1 ] )
      ancestor_to, ancestor_from = self.links.setdefault( ancestor, ( set(), set() ) )
      descendant_stack = [ dest_node ]
      while descendant_stack:
        descendant = descendant_stack.pop( 0 )
        descendant_stack.extend( self.links.setdefault( descendant, ( set(), set() ) )[ 0 ] )
        descendant_to, descendant_from = self.links.setdefault( descendant, ( set(), set() ) )
        ancestor_to.discard( descendant )
        descendant_from.discard( ancestor )
        self.nodes[ descendant ][ 1 ].add( ancestor )
    source_links_to.add( dest_node )
    dest_links_from.add( source_node )
    self.head.discard( dest_node )
    self.tail.discard( source_node )

    
  def add_workflow( self, workflow, prefix='' ):
    for i, j in workflow.nodes.iteritems():
      print '!import_node!', prefix + j[ 0 ], i
      self.nodes[ i ] = ( prefix + j[ 0 ], j[ 1 ] )
    self.links.update( workflow.links )
    self.head.update( workflow.head )
    self.tail.update( workflow.tail )

  
  def node_str( self, node ):
    return self.nodes[ node ][ 0 ]
  
  
  def write( self, out=sys.stdout ):
    print >> out, 'digraph workflow {'
    ids = {}
    for n in self.nodes:
      id = str( len( ids ) )
      ids[ n ] = id
      print >> out, '  %s [label="%s"];' % ( id, self.node_str( n ) )
    #print >> out, 'head:', [ self.node_str( i ) for i in self.head ]
    #print >> out, 'tail:', [ self.node_str( i ) for i in self.tail ]
    for n, v in self.links.iteritems():
      for nn in v[ 0 ]:
        print >> out, '  %s -> %s;' % ( ids[ n ], ids[ nn ] )
    print >> out, '}'


  def ordered_nodes( self ):
    for head_node in self.head:
      for branch_node in self.ordered_branch( head_node ):
        yield branch_node
  
  
  def ordered_branch( self, node ):
    yield ( self.node_str( node ), node )
    for child_node in self.links[ node ][ 0 ]:
      for branch_node in self.ordered_branch( child_node ):
        yield branch_node

      
