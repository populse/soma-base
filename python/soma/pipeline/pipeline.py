#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

import os
import sys
try:
  import traits.api as traits
  from traits.api import File, Float, Enum, Str, Int, Bool, List, Tuple, Instance, Any, Event, CTrait
except ImportError:
  import enthought.traits.api as traits
  from enthought.traits.api import File, Float, Enum, Str, Int, Bool, List, Tuple, Instance, Any, Event,CTrait

from soma.controller import Controller
from soma.sorted_dictionary import SortedDictionary
from soma.process import Process
from soma.process import get_process_instance
from memory import _joblib_run_process, _run_process


class Plug(Controller):
    enabled = Bool(default_value=True)
    activated = Bool(default_value=False)
    output = Bool(default_value=False)
    optional = Bool(default_value=False)

    def __init__(self, **kwargs):
        super(Plug, self).__init__(**kwargs)
        # link -> ( node, plug )
        self.links_to = set()
        self.links_from = set()


class Node(Controller):
    name = Str()
    enabled = Bool(default_value=True)
    activated = Bool(default_value=False)

    def __init__(self, pipeline, name, inputs, outputs):
        super(Node, self).__init__()
        self.pipeline = pipeline
        self.name = name
        self.plugs = {}
        self._callbacks = {}
        for i in inputs:
            if isinstance(i, dict):
                d = i.copy()
                name = d.pop('name')
                d['output'] = False
                plug = Plug(**d)
            else:
                name = i
                plug = Plug(output=False)
            self.plugs[name] = plug
            plug.on_trait_change(pipeline.update_nodes_and_plugs_activation,
                                 'enabled')
        for i in outputs:
            plug = Plug(output=True, optional=True)
            self.plugs[i] = plug
            plug.on_trait_change(pipeline.update_nodes_and_plugs_activation,
                                 'enabled')
        self.on_trait_change(pipeline.update_nodes_and_plugs_activation,
                             'enabled')

    def connect(self, source_parameter, dest_node, dest_parameter):
        def value_callback(value):
            if (value is not None and self.plugs[source_parameter].activated
                and dest_node.plugs[dest_parameter].activated):
                dest_node.set_plug_value(dest_parameter, value)
        self._callbacks[(source_parameter, dest_node, dest_parameter)] = value_callback
        self.set_callback_on_plug(source_parameter, value_callback)

    def set_callback_on_plug(self, plug_name, callback):
        self.on_trait_change(callback, plug_name)

    def get_plug_value(self, plug_name):
        return getattr(self, plug_name)

    def set_plug_value(self, plug_name, value):
        setattr(self, plug_name, value)

    def get_trait(self, name):
        return self.trait(name)


class ProcessNode(Node):
    def __init__(self, pipeline, name, process, **kwargs):
        self.process = get_process_instance(process, **kwargs)
        self.kwargs = kwargs
        inputs = []
        outputs = []
        for parameter, trait in self.process.user_traits().iteritems():
            if parameter in ('nodes_activation', 'selection_changed'):
                continue
            # hack: Accept other output traits
            #if isinstance(trait.handler, File) and trait.handler.output:
            if trait.handler.output:
                outputs.append(parameter)
            else:
                inputs.append(dict(name=parameter,
                      optional=bool(trait.optional or parameter in kwargs)))
        super(ProcessNode, self).__init__(pipeline, name, inputs, outputs)

    def set_callback_on_plug(self, plug_name, callback):
        self.process.on_trait_change(callback, plug_name)

    def get_plug_value(self, plug_name):
        if not isinstance(self.get_trait(plug_name).handler,
                      traits.Event):
            return getattr(self.process, plug_name)
        else:
            return None

    def set_plug_value(self, plug_name, value):
        # hack: undefined trait value
        from traits.trait_base import _Undefined
        if value in ["", "<undefined>"]:
            value = _Undefined()
        setattr(self.process, plug_name, value)

    def get_trait(self, name):
        return self.process.trait(name)


class PipelineNode(ProcessNode):
    pass


class Switch(Node):
    def __init__(self, pipeline, name, inputs, outputs):
        # hack: multi outputs
        if not isinstance(outputs, list):
            outputs = [outputs, ]
        self._outputs = outputs
        self.add_trait('switch', Enum(*inputs))
        print outputs, [dict(name=i, optional=True) for i in outputs]
        super(Switch, self).__init__(pipeline, name,
              ['switch'] + [dict(name=i, optional=True) for i in inputs],
              outputs)
        for i in inputs:
            self.add_trait(i, Any())
        for i in outputs:
            self.add_trait(i, Any())
            # hack: set the output trait flag
            output_trait = self.get_trait(i)
            output_trait.handler.output = True
        for n in inputs[1:]:
            self.plugs[n].enabled = False

    def _anytrait_changed(self, name, value):
        output = getattr(self, '_output', None)
        if output:
            if name == self.switch:
                setattr(self, output, value)

    def _switch_changed(self, old, new):
        self.plugs[old].enabled = False
        self.plugs[new].enabled = True
        self.pipeline.update_nodes_and_plugs_activation()
        setattr(self, self._output, getattr(self, new))


class Pipeline(Process):

  selection_changed = Event()

  def __init__( self, **kwargs ):
    super( Pipeline, self ).__init__( **kwargs )
    super( Pipeline, self ).add_trait( 'nodes_activation', Instance( Controller ) )
    self.list_process_in_pipeline=[]
    self.attributes = {}
    self.nodes_activation = Controller()
    self.nodes = SortedDictionary()
    self.node_position = {}
    self.pipeline_node = PipelineNode( self, '', self )
    self.nodes[ '' ] = self.pipeline_node
    self.do_not_export = set()
    self.pipeline_definition()
    self._caller = _joblib_run_process

    for node_name, node in self.nodes.iteritems():
      for parameter_name, plug in node.plugs.iteritems():
        if parameter_name in ( 'nodes_activation', 'selection_changed' ):
          continue
        if ((node_name, parameter_name) not in self.do_not_export and 
            not plug.links_to and not plug.links_from and
            not self.nodes[node_name].get_trait(parameter_name).optional):
          self.export_parameter(node_name, parameter_name)


    self.update_nodes_and_plugs_activation()


  def add_trait( self, name, trait ):
    super( Pipeline, self ).add_trait( name, trait )
    # hack
    #output = isinstance( trait, File ) and bool( trait.output )
    output = bool( trait.output )
    plug = Plug( output=output )
    self.pipeline_node.plugs[ name ] = plug
    plug.on_trait_change( self.update_nodes_and_plugs_activation, 'enabled' )


  def add_process( self, name, process, **kwargs ):
    if name in self.nodes:
      raise ValueError( 'Pipeline cannot have two nodes with the same name : %s' % name )
    self.nodes[ name ] = node = ProcessNode( self, name, process, **kwargs )
    for parameter_name in self.nodes[ name ].plugs:
      if parameter_name in kwargs:
        self.do_not_export.add( ( name, parameter_name ) )
    self.nodes_activation.add_trait( name, Bool )
    setattr( self.nodes_activation, name, node.enabled )
    self.nodes_activation.on_trait_change( self._set_node_enabled, name )
    self.list_process_in_pipeline.append(process)


  def add_switch( self, name, inputs, outputs ):
    if name in self.nodes:
      raise ValueError( 'Pipeline cannot have two nodes with the same name : %s' % name )
    #print "switch", name, inputs, output
    node = Switch( self, name, inputs, outputs )
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


  def add_link( self, link, only_if_activated=False ):
    source, dest = link.split( '->' )
    source_node_name, source_parameter, source_node, source_plug = self.parse_parameter( source )
    dest_node_name, dest_parameter, dest_node, dest_plug = self.parse_parameter( dest )
    if not source_plug.output and source_node is not self.pipeline_node:
      raise ValueError( 'Cannot link from an input plug : %s' % link )
    # hack: cant link output parameters
    if dest_plug.output and dest_node is not self.pipeline_node:
      raise ValueError( 'Cannot link to an output plug : %s' % link )
    source_plug.links_to.add( ( dest_node_name, dest_parameter, dest_node, dest_plug, only_if_activated ) )
    dest_plug.links_from.add( ( source_node_name, source_parameter, source_node, source_plug, False ) )
    if isinstance( dest_node, ProcessNode ) and isinstance( source_node, ProcessNode ):
      source_trait = source_node.process.trait( source_parameter )
      dest_trait = dest_node.process.trait( dest_parameter )
      if source_trait.output and not dest_trait.output:
        dest_trait.connected_output = True
    source_node.connect( source_parameter, dest_node, dest_parameter )
    dest_node.connect( dest_parameter, source_node, source_parameter )


  def export_parameter( self, node_name, parameter_name,
                       pipeline_parameter=None, only_if_activated=False):
    node = self.nodes[ node_name ]
    trait = node.get_trait( parameter_name )
    if trait is None:
      raise ValueError( 'Node %(n)s (%(nn)s) has no parameter %(p)s' % dict( n=node_name, nn=node.name, p=parameter_name ) )
    if not pipeline_parameter:
      pipeline_parameter = parameter_name
    if pipeline_parameter in self.user_traits():
      raise ValueError( 'Parameter %(pn)s of node %(nn)s cannot be exported to pipeline parameter %(pp)s' % dict( nn=node_name, pn=parameter_name, pp=pipeline_parameter ) )
    self.add_trait( pipeline_parameter, trait )
    # hack
    #if isinstance( trait.handler, File ) and trait.handler.output:
    if trait.handler.output:
      self.add_link( '%s.%s->%s' % ( node_name, parameter_name,
                                     pipeline_parameter ),
                                     only_if_activated=only_if_activated )
    else:
      self.add_link(  '%s->%s.%s' % ( pipeline_parameter,
                                      node_name, parameter_name ),
                                      only_if_activated=only_if_activated )


  def _set_node_enabled( self, node_name, value ):
    node = self.nodes.get( node_name )
    if node:
      node.enabled = value


  def update_nodes_and_plugs_activation( self ):
    inactive_links = []
    for node in self.nodes.itervalues():
      for source_plug_name, source_plug in node.plugs.iteritems():
        for nn, pn, n, p, only_if_activated in source_plug.links_to:
          if not source_plug.activated or not p.activated:
            inactive_links.append( ( node, source_plug_name, source_plug, n, pn, p ) )
    #print inactive_links

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
          for plug_name, plug in node.plugs.iteritems():
            if plug.links_to:
              continue
            if plug.enabled:
              for nn, pn, n, p, only_if_activated in plug.links_from:
                if p.activated and not only_if_activated:
                  plug.activated = True
                  break
                else:
                  plug.activated = False
            else:
              plug.activated = False
            if not plug.activated and not (plug.optional or ( node.name, plug_name ) in self.do_not_export ):
              node.activated = False
              break
          if node.activated:
            for plug in node.plugs.itervalues():
              if plug.enabled:
                activated = False
                for nn, pn, n, p, only_if_activated in plug.links_to:
                  if not only_if_activated:
                    activated = True
                    break
                if activated:
                  plug.activated = True
                  for nn, pn, n, p, only_if_activated in plug.links_to:
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
              for nn, pn, n, p, only_if_activated in plug.links_to:
                if p.activated and not only_if_activated:
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
              for nn, pn, n, p, only_if_activated in plug.links_from:
                new_stack.add( n )
      stack = new_stack

    pipeline_node = self.nodes[ '' ]
    traits_changed = False
    for plug_name, plug in pipeline_node.plugs.iteritems():
      for nn, pn, n, p, only_if_activated in plug.links_to.union( plug.links_from ):
        if p.activated and not only_if_activated:
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

    for node, source_plug_name, source_plug, n, pn, p in inactive_links:
      if (source_plug.activated and p.activated):
        value = node.get_plug_value( source_plug_name )
        node._callbacks[ ( source_plug_name, n, pn ) ]( value )



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
              for nn, pn, n, p, only_if_activated in plug.links_from:
                if p.activated and isinstance( n, ProcessNode ) and not isinstance( n, PipelineNode ):
                  nodes_from.update( tails[ n ] )
              for nn, pn, n, p, only_if_activated in plug.links_to:
                if p.activated and isinstance( n, ProcessNode ) and not isinstance( n, PipelineNode ):
                  nodes_to.update( heads[ n ] )
          for source_node in nodes_from:
            for dest_node in nodes_to:
              result.add_link( source_node, dest_node )
        elif isinstance( node, ProcessNode ) and not isinstance( node, PipelineNode ):
          for plug in node.plugs.itervalues():
            for nn, pn, n, p, only_if_activated in plug.links_to:
              if n.activated and isinstance( n, ProcessNode ) and not isinstance( n, PipelineNode ):
                for source_node in tails[ node ]:
                  for dest_node in heads[ n ]:
                    result.add_link( source_node, dest_node )
    return result

  def __call__(self):
        """ Call the pipeline nodes
        """
        print 'Execution of', self.id
        for cnt, node  in enumerate(self.workflow().ordered_nodes()):
            name, process_node = node
            print process_node.__class__.__mro__
            self._caller(os.getcwd(), "{0}-{1}".format(cnt + 1, name),
                         process_node)



class Workflow( object ):
  def __init__( self ):
    self.nodes = {}
    self.links = {}
    self.head = set()
    self.tail = set()

  def add_node( self, name, node ):
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
    for child_node in self.links.get( node, [[]] )[ 0 ]:
      for branch_node in self.ordered_branch( child_node ):
        yield branch_node


