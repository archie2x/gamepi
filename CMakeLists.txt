cmake_minimum_required(VERSION 3.25)
project(Gamepi LANGUAGES C CXX)

# The initial build verifies the native macOS -> Linux ARM64 toolchain.
# ES-DE will be integrated separately as the frontend work begins.
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
add_subdirectory(toolchain)
