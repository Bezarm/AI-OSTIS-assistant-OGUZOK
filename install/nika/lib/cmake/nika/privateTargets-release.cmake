#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "nika" for configuration "Release"
set_property(TARGET nika APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(nika PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/extensions/libnika.so"
  IMPORTED_SONAME_RELEASE "libnika.so"
  )

list(APPEND _cmake_import_check_targets nika )
list(APPEND _cmake_import_check_files_for_nika "${_IMPORT_PREFIX}/lib/extensions/libnika.so" )

# Import target "dialogue-process-module" for configuration "Release"
set_property(TARGET dialogue-process-module APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(dialogue-process-module PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/extensions/libdialogue-process-module.so"
  IMPORTED_SONAME_RELEASE "libdialogue-process-module.so"
  )

list(APPEND _cmake_import_check_targets dialogue-process-module )
list(APPEND _cmake_import_check_files_for_dialogue-process-module "${_IMPORT_PREFIX}/lib/extensions/libdialogue-process-module.so" )

# Import target "message-classify-module" for configuration "Release"
set_property(TARGET message-classify-module APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(message-classify-module PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/extensions/libmessage-classify-module.so"
  IMPORTED_SONAME_RELEASE "libmessage-classify-module.so"
  )

list(APPEND _cmake_import_check_targets message-classify-module )
list(APPEND _cmake_import_check_files_for_message-classify-module "${_IMPORT_PREFIX}/lib/extensions/libmessage-classify-module.so" )

# Import target "message-reply-module" for configuration "Release"
set_property(TARGET message-reply-module APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(message-reply-module PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/extensions/libmessage-reply-module.so"
  IMPORTED_SONAME_RELEASE "libmessage-reply-module.so"
  )

list(APPEND _cmake_import_check_targets message-reply-module )
list(APPEND _cmake_import_check_files_for_message-reply-module "${_IMPORT_PREFIX}/lib/extensions/libmessage-reply-module.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
