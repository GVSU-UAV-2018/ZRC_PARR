INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_AUTOSNR autoSNR)

FIND_PATH(
    AUTOSNR_INCLUDE_DIRS
    NAMES autoSNR/api.h
    HINTS $ENV{AUTOSNR_DIR}/include
        ${PC_AUTOSNR_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    AUTOSNR_LIBRARIES
    NAMES gnuradio-autoSNR
    HINTS $ENV{AUTOSNR_DIR}/lib
        ${PC_AUTOSNR_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(AUTOSNR DEFAULT_MSG AUTOSNR_LIBRARIES AUTOSNR_INCLUDE_DIRS)
MARK_AS_ADVANCED(AUTOSNR_LIBRARIES AUTOSNR_INCLUDE_DIRS)

