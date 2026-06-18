#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "fixed-search-strategy-template-processing-lib::fixed-search-strategy-template" for configuration "Release"
set_property(TARGET fixed-search-strategy-template-processing-lib::fixed-search-strategy-template APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(fixed-search-strategy-template-processing-lib::fixed-search-strategy-template PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libfixed-search-strategy-template.so"
  IMPORTED_SONAME_RELEASE "libfixed-search-strategy-template.so"
  )

list(APPEND _cmake_import_check_targets fixed-search-strategy-template-processing-lib::fixed-search-strategy-template )
list(APPEND _cmake_import_check_files_for_fixed-search-strategy-template-processing-lib::fixed-search-strategy-template "${_IMPORT_PREFIX}/lib/libfixed-search-strategy-template.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
