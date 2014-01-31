include_directories( ${SIP_INCLUDE_DIRS} )
if( DESIRED_QT_VERSION EQUAL 4 )
  BRAINVISA_ADD_SIP_PYTHON_MODULE( gradwidget soma/qtgui "${CMAKE_CURRENT_SOURCE_DIR}/gradwidget_qt4.sip" 
    SIP_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/gradwidget.sip" SIP_INCLUDE "${PYQT4_SIP_DIR}")
else()
  BRAINVISA_ADD_SIP_PYTHON_MODULE( gradwidget soma/qtgui "${CMAKE_CURRENT_SOURCE_DIR}/gradwidget_qt3.sip" 
    SIP_INCLUDE "${PYQT3_SIP_DIR}" )
endif()
target_link_libraries( gradwidget "${PYTHON_LIBRARY}" somaqtgui )
