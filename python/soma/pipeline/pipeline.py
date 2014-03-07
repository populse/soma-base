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
import logging

try:
    import traits.api as traits
    from traits.api import File, Float, Enum, Str, Int, Bool, List, Tuple,\
        Instance, Any, Event, CTrait, Directory
except ImportError:
    import enthought.traits.api as traits
    from enthought.traits.api import File, Float, Enum, Str, Int, Bool, List,\
        Tuple, Instance, Any, Event, CTrait, Directory

from soma.controller import Controller
from soma.sorted_dictionary import SortedDictionary
from soma.process import Process
from soma.process import get_process_instance

from topological_sort import GraphNode, Graph


class Plug(Controller):
    """ Overload of traits in oder to keep the pipeline memory.
    """
    # User parameter to control the Plug activation
    enabled = Bool(default_value=True)
    # Parameter describing the Plug status
    activated = Bool(default_value=False)
    # Parameter to type the Plug as an output
    output = Bool(default_value=False)
    # Parameter to create an aptional Plug
    optional = Bool(default_value=False)

    def __init__(self, **kwargs):
        """ Generate a Plug, i.e. a traits with the memory of the
        pipeline adjacent nodes
        """
        super(Plug, self).__init__(**kwargs)
        # The links correspond to edges in the graph theory
        # links_to = successor
        # links_from = predecessor
        # A link is a tuple of the form (node, plug)
        self.links_to = set()
        self.links_from = set()


class Node(Controller):
    """ Basic Node structure of the pipeline that need to be tuned.
    """
    # Node name
    name = Str()
    # User parameter to control the Node activation
    enabled = Bool(default_value=True)
    # Parameter describing the Node status
    activated = Bool(default_value=False)

    def __init__(self, pipeline, name, inputs, outputs):
        """ Generate a Node

        Parameters
        ----------
        pipeline: Pipeline (mandatory)
            the pipeline object where the node is added
        name: str (mandatory)
            the node name
        inputs: list of dict (mandatory)
            a list of input parameters containing a dictionary with default
            values (mandatory key: name)
        outputs: dict (mandatory)
            a list of output parameters containing a dictionary with default
            values (mandatory key: name)
        """
        super(Node, self).__init__()
        self.pipeline = pipeline
        self.name = name
        self.plugs = SortedDictionary()
        # _callbacks -> (src_plug_name, dest_node, dest_plug_name)
        self._callbacks = {}

        # generate a list with all the inputs and outputs
        # the second parameter (parameter_type) is False for an input,
        # True for an output
        parameters = zip(inputs, [False, ] * len(inputs))
        parameters.extend(zip(outputs, [True, ] * len(outputs)))
        for parameter, parameter_type in parameters:
            # check if parameter is a dictionary as specified in the
            # docstring
            if isinstance(parameter, dict):
                # check if parameter contains a name item
                # as specified in the docstring
                if "name" not in parameter:
                    raise Exception("Can't create parameter with unknown"
                                    "identifier and parameter {0}".format(
                                        parameter))
                plug_name = parameter.pop("name")
                # force the parameter type
                parameter["output"] = parameter_type
                # generate plug with input parameter and identifier name
                plug = Plug(**parameter)
            else:
                raise Exception("Can't create Node. Expect a dict structure "
                                "to initialize the Node, "
                                "got {0}: {1}".format(type(parameter),
                                                      parameter))
            # update plugs list
            self.plugs[plug_name] = plug
            # add an event on plug to validate the pipeline
            plug.on_trait_change(pipeline.update_nodes_and_plugs_activation,
                                 "enabled")

        # add an event on the Node instance traits to validate the pipeline
        self.on_trait_change(pipeline.update_nodes_and_plugs_activation,
                             'enabled')

    def connect(self, source_plug_name, dest_node, dest_plug_name):
        """ Connect linked plugs of two nodes

        Parameters
        ----------
        source_plug_name: str (mandatory)
            the source plug name
        dest_node: Node (mandatory)
            the destination node
        dest_plug_name: str (mandatory)
            the destination plug name
        """
        def value_callback(value):
            """ Spread the source plug value to the destination plug
            """
            if (value is not None and self.plugs[source_plug_name].activated
                    and dest_node.plugs[dest_plug_name].activated):
                dest_node.set_plug_value(dest_plug_name, value)
        # add a callback to spread the source plug value
        self._callbacks[(source_plug_name, dest_node,
                         dest_plug_name)] = value_callback
        self.set_callback_on_plug(source_plug_name, value_callback)

    def set_callback_on_plug(self, plug_name, callback):
        """ Add an event when a plug change

        Parameters
        ----------
        plug_name: str (mandatory)
            a plug name
        callback: @f (mandatory)
            a callback function
        """
        self.on_trait_change(callback, plug_name)

    def get_plug_value(self, plug_name):
        """ Return the plug value

        Parameters
        ----------
        plug_name: str (mandatory)
            a plug name

        Returns
        -------
        output: object
            the plug value
        """
        return getattr(self, plug_name)

    def set_plug_value(self, plug_name, value):
        """ Set the plug value

        Parameters
        ----------
        plug_name: str (mandatory)
            a plug name
        value: object (mandatory)
            the plug value we want to set
        """
        setattr(self, plug_name, value)

    def get_trait(self, trait_name):
        """ Return the desired trait

        Parameters
        ----------
        trait_name: str (mandatory)
            a trait name

        Returns
        -------
        output: trait
            the trait named trait_name
        """
        return self.trait(trait_name)


class ProcessNode(Node):

    def __init__(self, pipeline, name, process, **kwargs):
        self.process = get_process_instance(process, **kwargs)
        self.kwargs = kwargs
        inputs = []
        outputs = []
        for parameter, trait in self.process.user_traits().iteritems():
            if parameter in ('nodes_activation', 'selection_changed'):
                continue
            if trait.output:
                outputs.append(dict(name=parameter,
                                    optional=bool(trait.optional),
                                    output=True))
            else:
                inputs.append(dict(name=parameter,
                                   optional=bool(trait.optional or
                                                 parameter in kwargs)))
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
        from traits.trait_base import _Undefined
        if value in ["", "<undefined>"]:
            value = _Undefined()
        setattr(self.process, plug_name, value)

    def get_trait(self, name):
        return self.process.trait(name)


class PipelineNode(ProcessNode):
    pass


class Switch(Node):
    """ Switch Node to select a specific Process.
    """

    def __init__(self, pipeline, name, inputs, outputs):
        """ Generate a Switch Node

        The input plug names are built according to the following rule:
            <input_name>-<output_name>

        Parameters
        ----------
        pipeline: Pipeline (mandatory)
            the pipeline object where the node is added
        name: str (mandatory)
            the switch node name
        inputs: list (mandatory)
            a list of options
        outputs: list (mandatory)
            a list of output parameters
        """
        # if the user pass a simple element, create a list and add this
        # element
        if not isinstance(outputs, list):
            outputs = [outputs, ]

        # check consistency
        if not isinstance(inputs, list) or not isinstance(outputs, list):
            raise Exception("The Switch node input and output parameters "
                            "are inconsistent: expect list, "
                            "got {0}, {1}".format(type(inputs), type(outputs)))

        # private copy of outputs and inputs
        self._outputs = outputs
        self._switch_values = inputs

        # add switch enum trait to select the process
        self.add_trait('switch', Enum(*inputs))

        # format inputs and outputs to inherit from Node class
        flat_inputs = []
        for switch_name in inputs:
            flat_inputs.extend(["{0}_switch_{1}".format(switch_name, plug_name)
                                for plug_name in outputs])
        node_inputs = ([dict(name="switch"), ] +
                       [dict(name=i, optional=True) for i in flat_inputs])
        node_outputs = [dict(name=i)
                        for i in outputs]
        # inherit from Node class
        super(Switch, self).__init__(pipeline, name, node_inputs,
                                     node_outputs)

        # add a trait for each input and each output
        for i in flat_inputs:
            self.add_trait(i, Any())
        for i in outputs:
            self.add_trait(i, Any(output=True))

        # activate the switch first Process
        for plug_name in flat_inputs[len(outputs):]:
            self.plugs[plug_name].activated = False
            self.plugs[plug_name].enabled = False
        for plug_name in flat_inputs[:len(outputs)]:
            self.plugs[plug_name].activated = True
            self.plugs[plug_name].enabled = True

        # test
        self._switch_changed(self._switch_values[0],
                             self._switch_values[0])

    def _switch_changed(self, old_selection, new_selection):
        """ Add an event to the switch trait that enables us to select
        the desired option.

        Parameters
        ----------
        old_selection: str (mandatory)
            the old option
        new_selection: str (mandatory)
            the new option
        """
        # deactivate the plugs associated with the old option
        old_plug_names = ["{0}_switch_{1}".format(old_selection, plug_name)
                          for plug_name in self._outputs]
        for plug_name in old_plug_names:
            self.plugs[plug_name].activated = False
            self.plugs[plug_name].enabled = False

        # activate the plugs associated with the new option
        new_plug_names = ["{0}_switch_{1}".format(new_selection, plug_name)
                          for plug_name in self._outputs]
        for plug_name in new_plug_names:
            self.plugs[plug_name].activated = True
            self.plugs[plug_name].enabled = True

        # refresh the pipeline
        self.pipeline.update_nodes_and_plugs_activation()

        # refresh the links to the output plugs
        for output_plug_name in self._outputs:
            corresponding_input_plug_name = "{0}_switch_{1}".format(
                new_selection, output_plug_name)
            setattr(self, output_plug_name,
                    getattr(self, corresponding_input_plug_name))

    def _anytrait_changed(self, name, old, new):
        """ Add an event to the switch trait that enables us to select
        the desired option.

        Parameters
        ----------
        name: str (mandatory)
            the trait name
        old: str (mandatory)
            the old value
        new: str (mandatory)
            the new value
        """
        spliter = name.split("_switch_")
        if len(spliter) == 2 and spliter[0] in self._switch_values:
            switch_selection, output_plug_name = spliter
            setattr(self, output_plug_name, new)


class Pipeline(Process):
    """ Pipeline containing Process nodes, and links between node parameters.
    """

    selection_changed = Event()

    def __init__(self, **kwargs):
        super(Pipeline, self).__init__(**kwargs)
        super(Pipeline, self).add_trait('nodes_activation',
                                        Instance(Controller))
        self.list_process_in_pipeline = []
        self.attributes = {}
        self.nodes_activation = Controller()
        self.nodes = SortedDictionary()
        self.node_position = {}
        self.pipeline_node = PipelineNode(self, '', self)
        self.nodes[''] = self.pipeline_node
        self.do_not_export = set()
        self.pipeline_definition()

        self.workflow_repr = ""
        self.workflow_list = []

        for node_name, node in self.nodes.iteritems():
            for parameter_name, plug in node.plugs.iteritems():
                if parameter_name in ('nodes_activation', 'selection_changed'):
                    continue
                if ((node_name, parameter_name) not in self.do_not_export and
                    not plug.links_to and not plug.links_from and not
                   self.nodes[node_name].get_trait(parameter_name).optional):
                    self.export_parameter(node_name, parameter_name)

        self.update_nodes_and_plugs_activation()

    def add_trait(self, name, trait):
        '''
        '''
        super(Pipeline, self).add_trait(name, trait)
        self.get(name)

        if self.is_user_trait(trait):
            # hack
            #output = isinstance(trait, File) and bool(trait.output)
            output = bool(trait.output)
            plug = Plug(output=output)
            self.pipeline_node.plugs[name] = plug

            plug.on_trait_change(self.update_nodes_and_plugs_activation,
                                 'enabled')

    def add_process(self, name, process, do_not_export=None,
                    make_optional=None, **kwargs):
        '''Add a new node in the pipeline

        Parameters
        ----------
        name: str
        process: Process
        do_not_export: bool, optional
        '''
        make_optional = set(make_optional or [])
        do_not_export = set(do_not_export or [])
        do_not_export.update(kwargs)
        if name in self.nodes:
            raise ValueError('Pipeline cannot have two nodes with the'
                             'same name : %s' % name)
        self.nodes[name] = node = ProcessNode(self, name, process, **kwargs)
        for parameter_name in self.nodes[name].plugs:
            if (parameter_name in do_not_export or
                parameter_name in make_optional):
                self.do_not_export.add((name, parameter_name))
            if parameter_name in make_optional:
                # if do_not_export, set plug optional setting to True
                self.nodes[name].plugs[parameter_name].optional = True
        self.nodes_activation.add_trait(name, Bool)
        setattr(self.nodes_activation, name, node.enabled)
        self.nodes_activation.on_trait_change(self._set_node_enabled, name)
        self.list_process_in_pipeline.append(process)

    def add_switch(self, name, inputs, outputs):
        '''Add a switch node in the pipeline

        Parameters
        ----------
        name: str
            name for the switch node
        inputs: list of str
            names for switch inputs. Switch activation will select amongst
            them.
            Inputs names will actually be a combination of input and output,
            in the shape "input-output".
            This behaviour is needed when there are several outputs, and thus
            several input groups.
        outputs: list of str
            names for outputs.

        Examples
        --------
        >>> pipeline.add_switch('group_switch', ['in1', 'in2'],
            ['out1', 'out2'])

        will create a switch with 4 inputs and 2 outputs:
        inputs: "in1-out1", "in2-out1", "in1-out2", "in2-out2"
        outputs: "out1", "out2"
        '''
        if name in self.nodes:
            raise ValueError('Pipeline cannot have two nodes with the same '
                             'name : %s' % name)
        node = Switch(self, name, inputs, outputs)
        self.nodes[name] = node
        self.export_parameter(name, 'switch', name)

    def parse_link(self, link):
        source, dest = link.split('->')
        source_node_name, source_parameter, source_node, source_plug = \
            self.parse_parameter(source)
        dest_node_name, dest_parameter, dest_node, dest_plug = \
            self.parse_parameter(dest)
        return (source_node_name, source_parameter, source_node, source_plug,
                dest_node_name, dest_parameter, dest_node, dest_plug)

    def parse_parameter(self, name):
        dot = name.find('.')
        if dot < 0:
            node_name = ''
            node = self.pipeline_node
            parameter_name = name
        else:
            node_name = name[:dot]
            node = self.nodes.get(node_name)
            if node is None:
                raise ValueError('%s is not a valid node name' % node_name)
            parameter_name = name[dot + 1:]
        if parameter_name not in node.plugs:
            raise ValueError('%s is not a valid parameter name for node %s' %
                             (parameter_name, (node_name if node_name else
                                               'pipeline')))
        return node_name, parameter_name, node, node.plugs[parameter_name]

    def add_link(self, link, weak_link=False):
        '''Add a link between pipeline nodes

        Parameters
        ----------
        link: str
          link description. Its shape should be:
          "node.output->other_node.input".
          If no node is specified, the pipeline itself is assumed.
        '''
        source, dest = link.split('->')
        source_node_name, source_parameter, source_node, source_plug = \
            self.parse_parameter(source)
        dest_node_name, dest_parameter, dest_node, dest_plug = \
            self.parse_parameter(dest)
        if not source_plug.output and source_node is not self.pipeline_node:
            raise ValueError('Cannot link from an input plug : %s' % link)
        # hack: cant link output parameters
        if dest_plug.output and dest_node is not self.pipeline_node:
            raise ValueError('Cannot link to an output plug : %s' % link)

        # Check for link weakness
        # A weak node is ignored when setting plugs and nodes activations with
        # update_nodes_and_plugs_activation.
#        weak_link = False
#        if not isinstance(source_node, PipelineNode):
#            if isinstance(dest_node, Switch):
#                # Creating a link to a Switch make all links not connected
#                # to the Switch become weak links unless it is connected to the
#                # pipeline node
#                for plug_name, plug in source_node.plugs.iteritems():
#                    for nn, pn, n, p, wl in plug.links_to.copy():
#                        if not wl and not isinstance(n, (Switch,PipelineNode)):
#                            plug.links_to.remove((nn, pn, n, p, wl))
#                            p.links_from.remove((source_node_name, plug_name, source_node, plug, wl))
#                            plug.links_to.add((nn, pn, n, p, True))
#                            p.links_from.add((source_node_name, plug_name, source_node, plug, True))
#            else:
#                # A new link is a weak link if it is not connected to a
#                # Switch node and if there exists an output plug in
#                # source_node that is connected to a Switch node.
#                for plug in source_node.plugs.itervalues():
#                    for nn, pn, n, p, wl in plug.links_to:
#                        if isinstance(n, Switch):
#                            weak_link = True
#                            break
#                    if weak_link:
#                        break
#            if isinstance(dest_node, PipelineNode):
#                # If a plug linked to the PipelineNode (i.e. exported),
#                # the new link is weak if there is already a link on that
#                # plug.
#                if source_plug.links_to:
#                    weak_link = True
#            else:
#                # If a link to a non-Pipeline node is created, all links
#                # from the same plug to a Pipeline node become weak
#                for nn, pn, n, p, wl in dest_plug.links_to.copy():
#                    if not wl and isinstance(n, PipelineNode):
#                        source_plug.links_to.remove((nn, pn, n, p, wl))
#                        p.links_from.remove((source_node_name,
#                                             source_parameter, source_node,
#                                             source_plug, wl))
#                        source_plug.links_to.add((nn, pn, n, p, True))
#                        p.links_from.add((source_node_name, source_parameter,
#                                          source_node, source_plug, True))

        source_plug.links_to.add((dest_node_name, dest_parameter, dest_node,
                                  dest_plug, weak_link))
        dest_plug.links_from.add((source_node_name, source_parameter,
                                  source_node, source_plug, weak_link))
        if (isinstance(dest_node, ProcessNode) and
            isinstance(source_node, ProcessNode)):

            source_trait = source_node.process.trait(source_parameter)
            dest_trait = dest_node.process.trait(dest_parameter)
            if source_trait.output and not dest_trait.output:
                dest_trait.connected_output = True
        source_node.connect(source_parameter, dest_node, dest_parameter)
        dest_node.connect(dest_parameter, source_node, source_parameter)

    def export_parameter(self, node_name, parameter_name,
                         pipeline_parameter=None, weak_link=False):
        '''Exports one of the nodes parameters at the level of the pipeline.
        '''
        node = self.nodes[node_name]
        trait = node.get_trait(parameter_name)
        if trait is None:
            raise ValueError('Node %(n)s (%(nn)s) has no parameter %(p)s' %
                             dict(n=node_name, nn=node.name, p=parameter_name))
        if not pipeline_parameter:
            pipeline_parameter = parameter_name
        if pipeline_parameter in self.user_traits():
            raise ValueError('Parameter %(pn)s of node %(nn)s cannot be '
                             'exported to pipeline parameter %(pp)s' %
                             dict(nn=node_name, pn=parameter_name,
                                  pp=pipeline_parameter))
        self.add_trait(pipeline_parameter, trait)

        if trait.output:
            self.add_link('%s.%s->%s' % (node_name, parameter_name,
                                         pipeline_parameter), weak_link)
        else:
            self.add_link('%s->%s.%s' % (pipeline_parameter,
                                         node_name, parameter_name), weak_link)

    def _set_node_enabled(self, node_name, value):
        node = self.nodes.get(node_name)
        if node:
            node.enabled = value

    def update_nodes_and_plugs_activation(self):

        # Activate the pipeline node and all its plugs (if they are enabled)
        # Activate the Switch Node and its connection with the Pipeline Node
        # Desactivate all other nodes (and their plugs).
        pipeline_node = None
        for node in self.nodes.itervalues():
            if isinstance(node, (PipelineNode)):
                pipeline_node = node
                node.activated = node.enabled
                for plug in node.plugs.itervalues():
                    plug.activated = node.activated and plug.enabled
            elif isinstance(node, (Switch)):
                node.activated = False
                for plug in node.plugs.itervalues():
                    for nn, pn, n, p, weak_link in plug.links_from:
                        if (isinstance(n, (PipelineNode)) and plug.enabled):
                            plug.activated = True
            else:
                node.activated = False
                for plug in node.plugs.itervalues():
                    plug.activated = False

        def backward_activation(node):
            """ Activate node and its plugs according output links
            Plugs and Nodes are activated if enabled.
            Nodes and plugs are supposed to be deactivated when this
            function is called.
            """
            # Browse all node plugs
            for plug_name, plug in node.plugs.iteritems():
                # Case input plug
                if not plug.output:
                    # If the node is a Switch, follow the selcted way
                    if isinstance(node, Switch):
                        if plug.activated:
                            for nn, pn, n, p, weak_link in plug.links_from:
                                p.activated = p.enabled
                                n.activated = n.enabled
                                backward_activation(n)
                    # Otherwise browse all node plugs
                    else:
                        # First activate the input plug if connected
                        plug.activated = plug.enabled
                        # Get the linked plugs
                        for nn, pn, n, p, weak_link in plug.links_from:
                            # Stop criterion: Pipeline input plug reached
                            if isinstance(n, (PipelineNode)):
                                continue
                            # Go through the pipeline nodes
                            else:
                                p.activated = p.enabled
                                # Stop going through the pipeline if the node
                                # has already been activated
                                if not n.activated:
                                    n.activated = n.enabled
                                    backward_activation(n)
                # Case output plug
                else:
                    # Activate weak links
                    for nn, pn, n, p, weak_link in plug.links_to:
                        if weak_link:
                            p.activated = p.enabled

        # Follow each link that is not weak from the output plugs
        for plug_name, plug in pipeline_node.plugs.iteritems():
            # Check if the pipeline plug is an output
            if plug.output:
                # Get the linked plugs
                for nn, pn, n, p, weak_link in plug.links_from:
                    if not weak_link:
                        p.activated = p.enabled
                        n.activated = n.enabled
                        backward_activation(n)
                    else:
                        plug.activated = False

        self.selection_changed = True

    def update_nodes_and_plugs_activation_bis(self):
        """Reset all nodes and plugs activations according to the current state
        of the pipeline (i.e. switch selection, nodes disabled, etc.).
        """

        # Remember all links that are inactive (i.e. at least one of the two
        # plugs is inactive) in order to execute a callback if they become
        # active (see at the end of this method)
        inactive_links = []
        for node in self.nodes.itervalues():
            for source_plug_name, source_plug in node.plugs.iteritems():
                for nn, pn, n, p, weak_link in source_plug.links_to:
                    if not source_plug.activated or not p.activated:
                        inactive_links.append((node, source_plug_name,
                                               source_plug, n, pn, p))

        # Activate the pipeline node and all its plugs (if they are enabled)
        # and desactivate all other nodes (and their plugs).
        for node in self.nodes.itervalues():
            if isinstance(node, (Switch, PipelineNode)):
                node.activated = node.enabled
                for plug in node.plugs.itervalues():
                    plug.activated = node.activated and plug.enabled
            else:
                node.activated = False
                for plug in node.plugs.itervalues():
                    plug.activated = False

        def forward_activation(node):
            # Activate node and its plug according only to links to its input
            # plugs. If node is activated, its output plugs are activted (if
            # enabled) and the plugs of activated nodes connected to these
            # outputs are activated. node and its plugs are supposed to be
            # deactivated when this function is called.

            # Node have to be enabled to be activated
            if node.enabled:
                node.activated = True
                for plug_name, plug in node.plugs.iteritems():
                    if plug.output:
                        continue
                    if plug.enabled:
                        # Look for a non weak link connected to an activated
                        # plug in order to activate the plug
                        for nn, pn, n, p, weak_link in plug.links_from:
                            if not weak_link and p.activated:
                                plug.activated = True
                                break
                    # If the plug is not activated, is mandatory and must be
                    # exported, the whole node is deactivated
                    if (not plug.activated and not
                           (plug.optional or
                           (node.name, node) in self.do_not_export)):
                        node.activated = False
                        break
            else:
                node.activated = False
            if not node.activated:
                # If node is not activated, all plugs must be desactivated
                for plug in node.plugs.itervalues():
                    plug.activated = False
            else:
                # If node is activated, activate enabled output plugs and plugs
                # of other nodes that are connected to them
                for plug_name, plug in node.plugs.iteritems():
                    if plug.output and plug.enabled:
                        plug.activated = True
                        for nn, pn, n, p, weak_link in plug.links_to:
                            if n.activated and p.enabled:
                                p.activated = True
            return node.activated

        # Propagate activation from pipeline input plugs towards pipeline
        # output plugs. This will also activate (and propagate activation)
        # nodes that are not connected to pipeline to input plugs but that have
        # no mandatory input plugs.
        stack = self.nodes.values()
        while stack:
            new_stack = set()
            for node in stack:
                if isinstance(node, PipelineNode):
                    continue
                if forward_activation(node):
                    for plug in node.plugs.itervalues():
                        if not plug.activated:
                            continue
                        for nn, pn, n, p, weak_link in plug.links_to:
                            if not weak_link and p.enabled and not n.activated:
                                new_stack.add(n)
            stack = new_stack

        def backward_desactivation(node):
            # Desactivate node (and its plugs) according only to links to its
            # output plugs. Node is supposed to be activated when this
            # function is called.
            for plug_name, plug in node.plugs.iteritems():
                if plug.output:
                    links = plug.links_to
                else:
                    links = plug.links_from
                if plug.activated:
                    plug_activated = None
                    weak_activation = False
                    for nn, pn, n, p, weak_link in links:
                        if weak_link:
                            weak_activation = weak_activation or p.activated
                        else:
                            if p.activated:
                                plug_activated = True
                                break
                            else:
                                plug_activated = False
                    if plug_activated is None:
                        # plug is connected only with weak links
                        plug.activated = weak_activation
                    else:
                        # Non weak links takes priority over weak links
                        plug.activated = plug_activated
                    if not plug.activated and not\
                            (plug.optional or
                             (node.name, node) in self.do_not_export):
                        node.activated = False
                        break
                    else:
                        plug.activated = True
            if not node.activated:
                for plug in node.plugs.itervalues():
                    plug.activated = False

            return node.activated

        # Propagate deactivation from output plugs towards input plugs.
        stack = set(node for node in self.nodes.itervalues() if
                    node.activated)
        while stack:
            new_stack = set()
            for node in stack:
                if isinstance(node, PipelineNode):
                    continue
                if not backward_desactivation(node):
                    for plug in node.plugs.itervalues():
                        for nn, pn, n, p, weak_link in \
                                plug.links_from.union(plug.links_to):
#                            if not weak_link and n.activated:
                            if n.activated:
                                new_stack.add(n)
            stack = new_stack

        # Update pipeline node plugs activation and hide or show corresponding
        # pipeline traits
        pipeline_node = self.nodes['']
        traits_changed = False
        for plug_name, plug in pipeline_node.plugs.iteritems():
            for nn, pn, n, p, weak_link in\
                    plug.links_to.union(plug.links_from):
                if p.activated:
                    break
            else:
                plug.activated = False
            trait = self.trait(plug_name)
            if plug.activated:
                if getattr(trait, 'hidden', False):
                    trait.hidden = False
                    traits_changed = True
            else:
                if not getattr(trait, 'hidden', False):
                    trait.hidden = True
                    traits_changed = True
        self.selection_changed = True
        if traits_changed:
            self.user_traits_changed = True

        # Execute a callback for all links that have become active.
        for node, source_plug_name, source_plug, n, pn, p in inactive_links:
            if (source_plug.activated and p.activated):
                value = node.get_plug_value(source_plug_name)
                node._callbacks[(source_plug_name, n, pn)](value)

    def workflow_graph(self):
        """ Generate a workflow graph: list of process node to execute

        Returns
        -------
        graph: topological_sort.Graph
            grpah representation of the workflow from the current state of
            the pipeline
        """

        def insert(node_name, plug, dependencies, direct=True):
            """ Browse the plug links and add the correspondings edges
            to the node.
            If direct is set to true, the search looks for successor nodes.
            Otherwise, the search looks for predecessor nodes
            """
            # Get links
            if direct:
                plug_to_treat = plug.links_to
            else:
                plug_to_treat = plug.links_from

            # Main loop
            for item in plug_to_treat:
                # Plug need to be activated and must not be in the pipeline
                if (item[2].activated and not isinstance(item[2],
                                                         PipelineNode)):
                    # If plug links to a switch, we need to address the switch
                    # plugs
                    if not isinstance(item[2], Switch):
                        if direct:
                            dependencies.add((node_name, item[0]))
                        else:
                            dependencies.add((item[0], node_name))
                    else:
                        for switch_plug in item[2].plugs.itervalues():
                            insert(node_name, switch_plug, dependencies,
                                   direct)

        # Create a graph and a list of graph node edges
        graph = Graph()
        dependencies = set()

        # Add activated Process nodes in the graph
        for node_name, node in self.nodes.iteritems():
            # Select only Process nodes
            if (node.activated and not isinstance(node, PipelineNode) and
                    not isinstance(node, Switch)):
                # If Pipeline: meta in node is the workflow (list of
                # Process)
                if isinstance(node.process, Pipeline):
                    graph.add_node(GraphNode(node_name,
                                             node.process.workflow_graph()))
                # If Process: meta in node is a list with one Process
                else:
                    graph.add_node(GraphNode(node_name, [node.process, ]))

                # Add node edges (Successor: direct=True and
                # Predecessor: direct=False)
                for plug_name, plug in node.plugs.iteritems():
                    if plug.activated:
                        insert(node_name, plug, dependencies, direct=False)
                        insert(node_name, plug, dependencies, direct=True)

        # Add edges to the graph
        for d in dependencies:
            graph.add_link(d[0], d[1])

        return graph

    def workflow_ordered_nodes(self):
        """ Generate a workflow: list of process node to execute

        Returns
        -------
        workflow_list: list of Process
            an ordered list of Processes to execute
        """
        # Create a graph and a list of graph node edges
        graph = self.workflow_graph()
        # Start the topologival sort
        ordered_list = graph.topological_sort()
        
        def walk_wokflow(wokflow, workflow_list):
            """ Recursive fonction to go throw pipelines' graphs
            """
            for sub_workflow in wokflow:
                if isinstance(sub_workflow[1], list):
                    workflow_list.extend(sub_workflow[1])
                else:
                    tmp = sub_workflow[1].topological_sort()
                    walk_wokflow(tmp, workflow_list)

        # Generate the output
        self.workflow_repr = "->".join([x[0] for x in ordered_list])
        logging.debug("Workflow: {0}". format(self.workflow_repr))
        self.workflow_list = []
        walk_wokflow(ordered_list, self.workflow_list) 

        return self.workflow_list
