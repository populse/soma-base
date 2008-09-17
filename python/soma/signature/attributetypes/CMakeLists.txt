SET(PY_SRCS
__init__.py
any.py
boolean.py
bytes.py
choice.py
fileName.py
float.py
integer.py
number.py
openedchoice.py
sequence.py
unicode.py
)

ADD_CUSTOM_TARGET(soma_python_signature_attributetypes ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_signature_attributetypes ${CMAKE_INSTALL_PREFIX}/python/soma/signature/attributetypes) 
ENDFOREACH(_py_file ${PY_SRCS})
