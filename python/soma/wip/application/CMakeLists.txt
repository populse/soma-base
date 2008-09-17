SET(PY_SRCS
__init__.py
api.py
application.py
icons.py
plugins.py
)

ADD_CUSTOM_TARGET(soma_python_wip_application ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_wip_application ${CMAKE_INSTALL_PREFIX}/python/soma/wip/application)
ENDFOREACH(_py_file ${PY_SRCS})
