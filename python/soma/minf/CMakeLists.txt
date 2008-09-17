SET(PY_SRCS
__init__.py
api.py
error.py
reader.py
tree.py
writer.py
xhtml.py
xml_reader.py
xml_tags.py
xml_writer.py
)

ADD_CUSTOM_TARGET(soma_python_minf ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_minf ${CMAKE_INSTALL_PREFIX}/python/soma/minf)
ENDFOREACH(_py_file ${PY_SRCS})
