SET(PY_SRCS
__init__.py
api.py
signature.py
)

ADD_CUSTOM_TARGET(soma_python_signature ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_signature ${CMAKE_INSTALL_PREFIX}/python/soma/signature) 
ENDFOREACH(_py_file ${PY_SRCS})


ADD_SUBDIRECTORY(attributetypes)
ADD_SUBDIRECTORY(qt3gui)
