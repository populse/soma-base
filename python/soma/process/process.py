# -*- coding: utf-8 -*-
import os

try:
    import traits.api as traits
    from traits.api import (ListStr, HasTraits, File, Float, Instance,
                            Enum, Str)
    from traits.trait_base import _Undefined
except ImportError:
    import enthought.traits.api as traits
    from enthought.traits.api import (ListStr, HasTraits, File, Float,
                                      Instance, Enum, Str)

from soma.controller import Controller


class Process(Controller):
    """ TODO
    """
    def __init__(self):
        """ Init the process class.

        In a process instance it is possible to define QC process(es)
        that will be used to evaluate the quality of the result.

        It is also possible to add viewers to check the input, output, or
        QC data.
        """
        # inheritance
        super(Process, self).__init__()

        # intern identifiers
        self.name = self.__class__.__name__
        self.id = self.__class__.__module__ + '.' + self.name

        # tools around the current process
        self.viewers = {}
        self.qc_processes = {}

        # runtime information
        self.runtime = None

        # log file name
        self.log_file = None

        # process caller
        #self._caller = _joblib_run_process
        #self._run = None

    #def __call__(self):
        #if "__call__" in dir(self.run):
        #    self.runtime = self._caller(
        #        os.getcwd(),
        #        "{0} {1}".format(self._nipype_class, "node_id"),
        #        self)

    ##############
    # Members    #
    ##############

    def auto_nipype_process_qc(self):
        """ From a nipype process instance call automatically
        quality control tools
        """
        pass
        #interface_name = self._nipype_interface.__class__.__name__
        #qc_id = ("casper.use_cases.qc."
        #         "{0}QualityCheck".format(interface_name))
        #qc_instance = get_instance(qc_id,
        #                      nipype_interface=self._nipype_interface)
        #self.qc_processes["automatic"] = qc_instance

#==============================================================================
#
#     def call_viewer(self, controller_widget, name):
#         viewer, kwargs = self.viewers[name]
#         if not kwargs:
#             liste = []
#             liste.append(getattr(controller_widget.controller, name))
#             p = GlobalNaming().get_object(viewer)(*liste)
#         else:
#             dico_parameter = {}
#             #dico_parameter[name]=value
#             #get all traits name of the process
#             trait_of_process = controller_widget.controller.user_traits(). \
#                                keys()
#             #Get parameters in the kwargs and complete value of traits needed
#             for key, value in kwargs.iteritems():
#                 dico_parameter[key] = value
#                 if value in trait_of_process:
#                     dico_parameter[key] = getattr(
#                         controller_widget.controller,
#                         value)
#             p = GlobalNaming().get_object(viewer)(**dico_parameter)
#         return p()
#==============================================================================

    ##############
    # Properties #
    ##############

    def set_qc(self, name, qc_id, **kwargs):
        """ Create and set a viewer.
        """
        self.qc_processes[name] = (qc_id, kwargs)

    def get_qc(self, name):
        """ Get the viewer identified by name
        """
        return self.qc_processes[name]

    def set_viewer(self, name, viewer_id, **kwargs):
        """ Create and set a viewer.
        """
        self.viewers[name] = (viewer_id, kwargs)

    def get_viewer(self, name):
        """ Get the viewer identified by name
        """
        return self.viewers[name]

    def set_parameter(self, name, value):
        """ Set the parameter name of the process
        instance.
        """
        setattr(self, name, value)

    def get_parameter(self, name):
        """ Get the parameter name of the process
        instance.
        """
        return getattr(self, name)

    def _get_log(self):
        """ Get process execution information
        """
        def get_tool_version(tool):
            """ Get the version of a python tool
            Parameters
            ----------
            tool: str (mandatory)
            a tool name

            Returns
            -------
            version: str (default None)
            the tool version.
            """
            version = None
            try:
                module = __import__(tool)
                version = module.__version__
            except:
                pass
            return version

        def get_nipype_interfaces_versions():
            """
            """
            try:
                nipype_module = __import__("nipype.interfaces")
                sub_modules = ["{0}".format(i)
                                for i in dir(nipype_module)
                                if (not i.startswith("_") and
                                    not i[0].isupper())]
                versions = {}
                for module in sub_modules:
                    try:
                        version = eval("nipype_module.{0}."
                                       "Info.version()".format(module))
                        if version:
                            versions[module] = version
                    except:
                        pass

                return versions
            except:
                return {}

        # get dependencies versions
        versions = {
            "soma": get_tool_version("soma"),
        }
        if "_nipype_interface" in dir(self):
            versions["nipype"] = get_tool_version("nipype")
            interface_name = self._nipype_interface.__module__.split(".")[2]
            versions[interface_name] = self._nipype_interface.version

        # get inputs and outputs
        inputs = {}
        outputs = {}
        for name, trait in self.user_traits().iteritems():
            if trait.output:
                outputs[name] = repr(self.get_parameter(name))
            else:
                inputs[name] = repr(self.get_parameter(name))

        # get execution information
        execution_result = {}
        if self.runtime:
            runtime = self.runtime.runtime
            execution_result["start_time"] = runtime.startTime
            execution_result["end_time"] = runtime.endTime
            execution_result["cmd_line"] = runtime.cmdline
            execution_result["hostname"] = runtime.hostname
            execution_result["stderr"] = runtime.stderr
            execution_result["stdout"] = runtime.stdout
            execution_result["cwd"] = runtime.cwd
            execution_result["environ"] = runtime.environ

            if not self.log_file:
                self.log_file = os.path.join(execution_result["cwd"],
                                             "log.json")

        # generate summary
        log = {
            "process": self.id,
            "versions": versions,
            "inputs": inputs,
            "outputs": outputs,
            "execution_result": execution_result,
        }

        return log

    def save_log(self):
        """ Save the Process meta information in json format
        """
        import json
        json_struct = unicode(json.dumps(self._get_log(), indent=4))
        if self.log_file:
            f = open(self.log_file, 'w')
            print >> f, json_struct
            f.close()

    #def _get_call(self):
    #    """ Process function that will be call.
    #    This function must be defined in derived classes.
    #    """
    #    raise NotImplementedError()

    #run = LateBindingProperty(_get_call, None, None, "Call function")
    log = property(_get_log, None, None, "Process information")


class NipypeProcess(Process):
    """ Dummy class for interfaces.
    """
    def __init__(self, *args, **kwargs):
        """ Init the nipype process class.
        """
        # inheritance
        super(NipypeProcess, self).__init__(*args, **kwargs)