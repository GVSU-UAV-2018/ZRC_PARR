# Install script for directory: /home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/python

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
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/collar_detect" TYPE FILE FILES
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/python/__init__.py"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/python/collar_detect.py"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/python/Burst_Detection.py"
    )
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python2.7/dist-packages/collar_detect" TYPE FILE FILES
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/build/python/__init__.pyc"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/build/python/collar_detect.pyc"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/build/python/Burst_Detection.pyc"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/build/python/__init__.pyo"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/build/python/collar_detect.pyo"
    "/home/pi/ZRC_RDF/Pi Codem/gr-collar_detect/build/python/Burst_Detection.pyo"
    )
endif()

