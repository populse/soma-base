SET(PY_SRCS
__init__.py
api.py
automatic.py
designer.py
file_dialog.py
icons.py
list_tree_widgets.py
qt3thread.py
text.py
timered_widgets.py
vscrollframe.py
)

ADD_CUSTOM_TARGET(soma_python_qt3 ALL)
FOREACH(_py_file ${PY_SRCS})
  PYTHON_INSTALL(${_py_file} soma_python_qt3 ${CMAKE_INSTALL_PREFIX}/python/soma/qt3gui) 
ENDFOREACH(_py_file ${PY_SRCS})
