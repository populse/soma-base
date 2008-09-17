SET(PY_SRCS
__init__.py
)

ADD_CUSTOM_TARGET(soma_python_plugin ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_plugin ${CMAKE_INSTALL_PREFIX}/python/soma/plugins) 
ENDFOREACH(_py_file ${PY_SRCS})
