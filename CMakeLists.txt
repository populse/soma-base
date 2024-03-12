cmake_minimum_required( VERSION 3.20 )

find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

find_package( python REQUIRED )

BRAINVISA_DEPENDENCY( DEV DEPENDS "${BRAINVISA_PACKAGE_NAME}" RUN "= ${${BRAINVISA_PACKAGE_NAME}_VERSION}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS python RUN ">= ${PYTHON_SHORT_VERSION}" )
BRAINVISA_DEPENDENCY( DEV DEPENDS python DEV ">= 2.4;<< 4.0" )

set( SOMA-BASE_DEFINITIONS "-DUSE_SOMA_CONFIG" )

BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                                 ${PROJECT_NAME} )

find_package( Sphinx )
BRAINVISA_GENERATE_SPHINX_DOC( "doc/sphinx"
  "share/doc/soma-base-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/sphinx" )

BRAINVISA_CREATE_CMAKE_CONFIG_FILES()

# tests
enable_testing()
brainvisa_add_test( soma-base-tests
          "${PYTHON_EXECUTABLE_NAME}" "-m" "soma.tests.test_soma_base" )
