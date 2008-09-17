SET(PY_SRCS
__init__.py
boolean_qt3gui.py
bytes_qt3gui.py
choice_qt3gui.py
fileName_qt3gui.py
number_qt3gui.py
openedchoice_qt3gui.py
sequence_qt3gui.py
signature_qt3gui.py
unicode_qt3gui.py
)


ADD_CUSTOM_TARGET(soma_python_signature_qt3 ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_signature_qt3 ${CMAKE_INSTALL_PREFIX}/python/soma/signature/qt3gui) 
ENDFOREACH(_py_file ${PY_SRCS})
