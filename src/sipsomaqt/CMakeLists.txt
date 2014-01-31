include_directories( ${SIP_INCLUDE_DIRS} )
if( DESIRED_QT_VERSION EQUAL 4 )
  BRAINVISA_ADD_SIP_PYTHON_MODULE( somaqt soma "${CMAKE_CURRENT_SOURCE_DIR}/soma_qt4.sip" 
    SIP_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/soma_qt.sip" SIP_INCLUDE "${PYQT4_SIP_DIR}" )
else()
  BRAINVISA_ADD_SIP_PYTHON_MODULE( sipsomaqtgui soma/qtgui "${CMAKE_CURRENT_SOURCE_DIR}/soma_qt3.sip" 
    SIP_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/soma_qt.sip" SIP_INCLUDE "${PYQT3_SIP_DIR}" )
endif()
target_link_libraries( somaqt "${PYTHON_LIBRARY}" ${QT_LIBRARIES} )
