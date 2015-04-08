cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

find_package( python REQUIRED )
find_package( Epydoc )
find_package( Dot )

BRAINVISA_DEPENDENCY( DEV DEPENDS "${BRAINVISA_PACKAGE_NAME}" RUN "= ${${BRAINVISA_PACKAGE_NAME}_VERSION}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.4;<< 3.0" )

set( SOMA-BASE_DEFINITIONS "-DUSE_SOMA_CONFIG" )

BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                                 ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share" 
                         "share/${PROJECT_NAME}-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}"
                         ${PROJECT_NAME} )
BRAINVISA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share/foms" 
                         "share/foms"
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

find_package( Sphinx )
BRAINVISA_GENERATE_SPHINX_DOC( "doc/sphinx"
  "share/doc/soma-base-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/sphinx" )

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()

# tests
enable_testing()
add_test(soma-base-tests "${CMAKE_BINARY_DIR}/bin/bv_env" "${PYTHON_EXECUTABLE}" "${CMAKE_BINARY_DIR}/python/test/test_soma_base.py")
