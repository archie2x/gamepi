cmake_minimum_required(VERSION 3.20)
project(gamepi_waynergy C)

get_filename_component(GAMEPI_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(WAYNERGY_SOURCE "${GAMEPI_ROOT}/sources/waynergy")
set(WAYLAND_SCANNER "${GAMEPI_ROOT}/build/host-tools/wayland-scanner")
find_package(PkgConfig REQUIRED)
pkg_check_modules(DEPS REQUIRED IMPORTED_TARGET wayland-client xkbcommon libtls)

file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/generated")
file(READ "${WAYNERGY_SOURCE}/include/ver.h.in" VERSION_HEADER)
string(REPLACE "@VCS_DESC@" "v0.0.17" VERSION_HEADER "${VERSION_HEADER}")
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/generated/ver.h" "${VERSION_HEADER}")

file(GLOB PROTOCOL_XML "${WAYNERGY_SOURCE}/protocol/*.xml")
set(PROTOCOL_SOURCES)
foreach(XML IN LISTS PROTOCOL_XML)
    get_filename_component(NAME "${XML}" NAME_WE)
    set(CODE "${CMAKE_CURRENT_BINARY_DIR}/generated/${NAME}-protocol.c")
    set(HEADER "${CMAKE_CURRENT_BINARY_DIR}/generated/${NAME}-client-protocol.h")
    add_custom_command(OUTPUT "${CODE}" "${HEADER}"
        COMMAND "${WAYLAND_SCANNER}" private-code "${XML}" "${CODE}"
        COMMAND "${WAYLAND_SCANNER}" client-header "${XML}" "${HEADER}"
        DEPENDS "${XML}" "${WAYLAND_SCANNER}" VERBATIM)
    list(APPEND PROTOCOL_SOURCES "${CODE}" "${HEADER}")
endforeach()

file(GLOB CLIENT_SOURCES "${WAYNERGY_SOURCE}/src/*.c")
list(FILTER CLIENT_SOURCES EXCLUDE REGEX "/(mapper|clip-update)\\.c$")
add_executable(waynergy ${CLIENT_SOURCES} ${PROTOCOL_SOURCES})
target_include_directories(waynergy PRIVATE
    "${WAYNERGY_SOURCE}/include" "${CMAKE_CURRENT_BINARY_DIR}/generated")
target_compile_definitions(waynergy PRIVATE _GNU_SOURCE USYNERGY_LITTLE_ENDIAN)
target_link_libraries(waynergy PRIVATE PkgConfig::DEPS m)
