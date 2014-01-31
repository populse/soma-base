set( _headers
     spline.h
     gradwidget.h
     gradient.h
)

set( _sources
     gradwidget.cpp
     spline.cpp
     gradient.cpp
)

BRAINVISA_COPY_AND_INSTALL_HEADERS( _headers soma headersTarget )
BRAINVISA_ADD_MOC_FILES( _sources ${_headers} )
add_library( somaqtgui SHARED ${_sources} )
add_dependencies( somaqtgui ${headersTarget} )
set_property( TARGET somaqtgui PROPERTY VERSION ${${PROJECT_NAME}_VERSION} )
target_link_libraries( somaqtgui ${QT_LIBRARIES} )
BRAINVISA_INSTALL( TARGETS somaqtgui
                   DESTINATION lib
                   COMPONENT ${PROJECT_NAME} )
                   
IF ( DOXYGEN_FOUND )
  set( _doxygenInput "${_headers}" )
  set( DOXYFILE_PREDEFINED "${SOMA-QTGUI_DEFINITIONS}")
  BRAINVISA_GENERATE_DOXYGEN_DOC( _doxygenInput  
                                  INPUT_PREFIX "${CMAKE_BINARY_DIR}/include/soma"
                                  COMPONENT soma-qtgui )
ENDIF ( DOXYGEN_FOUND )

