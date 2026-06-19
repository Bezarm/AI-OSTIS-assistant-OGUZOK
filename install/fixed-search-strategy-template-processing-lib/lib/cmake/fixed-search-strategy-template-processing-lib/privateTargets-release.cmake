#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "fixed-search-strategy-template-processing-module" for configuration "Release"
set_property(TARGET fixed-search-strategy-template-processing-module APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(fixed-search-strategy-template-processing-module PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/extensions/libfixed-search-strategy-template-processing-module.so"
  IMPORTED_SONAME_RELEASE "libfixed-search-strategy-template-processing-module.so"
  )

list(APPEND _cmake_import_check_targets fixed-search-strategy-template-processing-module )
list(APPEND _cmake_import_check_files_for_fixed-search-strategy-template-processing-module "${_IMPORT_PREFIX}/lib/extensions/libfixed-search-strategy-template-processing-module.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
