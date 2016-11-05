# Install script for directory: /home/pi/ZRC_RDF/Pi Code/gr-autoSNR

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/autoSNR" TYPE FILE FILES "/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/cmake/Modules/autoSNRConfig.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/include/autoSNR/cmake_install.cmake")
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/lib/cmake_install.cmake")
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/swig/cmake_install.cmake")
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/python/cmake_install.cmake")
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/grc/cmake_install.cmake")
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/apps/cmake_install.cmake")
  include("/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/docs/cmake_install.cmake")

endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

file(WRITE "/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/${CMAKE_INSTALL_MANIFEST}" "")
foreach(file ${CMAKE_INSTALL_MANIFEST_FILES})
  file(APPEND "/home/pi/ZRC_RDF/Pi Code/gr-autoSNR/build/${CMAKE_INSTALL_MANIFEST}" "${file}\n")
endforeach()
