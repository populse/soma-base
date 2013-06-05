cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

find_package( python REQUIRED )
find_package( Epydoc )
find_package( Dot )

BRAINVISA_FIND_PACKAGE( brainvisa-share QUIET )
if( BRAINVISA-SHARE_FOUND )
  include( "${BRAINVISA-SHARE_USE_FILE}" )
else()
  message( "WARNING: project brainvisa-share has not been found. Some programs that require access to shared directories may fail to run." )
endif()

BRAINVISA_DEPENDENCY( DEV DEPENDS "${BRAINVISA_PACKAGE_NAME}" RUN "= ${${BRAINVISA_PACKAGE_NAME}_VERSION}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.4;<< 3.0" )

configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/config/config.py.in" "${CMAKE_BINARY_DIR}/python/soma/config.py" @ONLY )
BRAINVISA_INSTALL( FILES "${CMAKE_BINARY_DIR}/python/soma/config.py"
                   DESTINATION "python/soma"
                   COMPONENT ${PROJECT_NAME} )
configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/config/config.h.in" "${CMAKE_BINARY_DIR}/include/soma/config.h" @ONLY )
BRAINVISA_INSTALL( FILES "${CMAKE_BINARY_DIR}/include/soma/config.h"
                   DESTINATION "include/soma"
                   COMPONENT ${PROJECT_NAME}-dev )

set( SOMA-BASE_DEFINITIONS "-DUSE_SOMA_CONFIG" )

BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                                 ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share" 
                         "share/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}"
                         ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/bin"
                          bin
                          ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/examples/soma"
                          "share/doc/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/examples"
                          ${PROJECT_NAME}-doc )
 BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/tests"
                                  ${PROJECT_NAME}
                                  python )
 BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/sandbox/python"
                                  ${PROJECT_NAME}
                                  python/sandbox )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/sandbox/share" 
                          "share/sandbox"
                          ${PROJECT_NAME} )
# BRAINVISA_GENERATE_EPYDOC_DOC( "${CMAKE_BINARY_DIR}/python/soma"
#   "share/doc/soma-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/epydoc"
#   EXCLUDE "soma.aims*" "soma.*.qt3gui" )

find_package( Sphinx )
BRAINVISA_GENERATE_SPHINX_DOC( "doc/sphinx"
  "share/doc/soma-base-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/sphinx" )

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()
