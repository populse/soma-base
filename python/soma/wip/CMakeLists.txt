SET(PY_SRCS
__init__.py
configuration.py
configuration_qt3gui.py
io.py
singleton.py
temporary.py
)

ADD_CUSTOM_TARGET(soma_python_wip ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_wip ${CMAKE_INSTALL_PREFIX}/python/soma/wip) 
ENDFOREACH(_py_file ${PY_SRCS})


ADD_SUBDIRECTORY(application)
