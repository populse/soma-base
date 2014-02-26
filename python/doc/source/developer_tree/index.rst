:orphan:

###########################
Contributing Documentation
###########################

Useful information for advanced users.

.. _soma_dev:

:mod:`soma.pipeline`: Pipeline
=====================================

.. automodule:: soma.pipeline
   :no-members:
   :no-inherited-members:

**API:** See the :ref:`soma_ref` section for API details.

.. currentmodule:: soma.pipeline

Workflow Definition
--------------------
.. autosummary::
    :toctree: generated/soma-pipeline/
    :template: class.rst

    topological_sort.GraphNode
    topological_sort.Graph


:mod:`soma.controller`: Controller
=====================================

.. automodule:: soma.controller
   :no-members:
   :no-inherited-members:

.. currentmodule:: soma.controller

Controller Definition
---------------------
.. autosummary::
    :toctree: generated/soma-controller/
    :template: class.rst

    controller.Controller
    controller.MetaController
    controller.ControllerFactories


:mod:`soma.process`: Process
===============================

.. automodule:: soma.process
   :no-members:
   :no-inherited-members:

.. currentmodule:: soma.process

.. autosummary::
    :toctree: generated/soma-process/
    :template: class.rst

    process.NipypeProcess

.. autosummary::
    :toctree: generated/soma-process/
    :template: function.rst

    nipype_process.nipype_factory


:mod:`soma.study_config`: Study Configuration
==============================================

.. automodule:: soma.study_config
   :no-members:
   :no-inherited-members:


.. currentmodule:: soma.study_config

.. autosummary::
    :toctree: generated/soma-studyconfig/
    :template: function.rst

    config_utils.environment
    config_utils.find_spm
    memory._run_process
    memory._joblib_run_process
    spm_memory_utils.local_map
    spm_memory_utils.copy_resources
    spm_memory_utils.last_timestamp








