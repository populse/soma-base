cmake_minimum_required( VERSION 2.6 )

SOMA_PROJECT()

find_package( PythonInterp REQUIRED )
find_package( Epydoc )
find_package( Dot )

SOMA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/python"
                            ${PROJECT_NAME} )
SOMA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/share" 
                      "share/${PROJECT_NAME}-${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}"
                      ${PROJECT_NAME} )
SOMA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/bin"
                      bin
                      ${PROJECT_NAME} )
SOMA_COPY_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/examples/soma"
                     "share/doc/${PROJECT_NAME}-${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}/examples"
                     ${PROJECT_NAME}-doc )
SOMA_GENERATE_EPYDOC_DOC( "${CMAKE_CURRENT_SOURCE_DIR}/python"
  "share/doc/${PROJECT_NAME}-${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}/epydoc/html" ) 

SOMA_CREATE_CMAKE_CONFIG_FILES()
