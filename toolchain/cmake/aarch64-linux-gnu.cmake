set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
get_filename_component(_cross_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(CMAKE_SYSROOT "${_cross_root}/sysroot")

# All executables here are native macOS tools. Only their inputs target Linux.
set(CMAKE_C_COMPILER /opt/homebrew/opt/llvm/bin/clang)
set(CMAKE_CXX_COMPILER /opt/homebrew/opt/llvm/bin/clang++)
set(CMAKE_ASM_COMPILER /opt/homebrew/opt/llvm/bin/clang)
set(CMAKE_C_COMPILER_TARGET aarch64-linux-gnu)
set(CMAKE_CXX_COMPILER_TARGET aarch64-linux-gnu)
set(CMAKE_ASM_COMPILER_TARGET aarch64-linux-gnu)
set(CMAKE_AR /opt/homebrew/opt/llvm/bin/llvm-ar)
set(CMAKE_RANLIB /opt/homebrew/opt/llvm/bin/llvm-ranlib)
set(CMAKE_OBJDUMP /opt/homebrew/opt/llvm/bin/llvm-objdump)
set(CMAKE_STRIP /opt/homebrew/opt/llvm/bin/llvm-strip)
set(CMAKE_LINKER /opt/homebrew/bin/ld.lld)

# Homebrew's default Clang config injects a macOS SDK: explicitly disable it.
# Use Debian's target libstdc++/libgcc, rather than macOS's libc++.
set(_target_flags "--no-default-config --gcc-toolchain=${CMAKE_SYSROOT}/usr")
set(CMAKE_C_FLAGS_INIT "${_target_flags}")
set(CMAKE_CXX_FLAGS_INIT "${_target_flags}")
set(CMAKE_ASM_FLAGS_INIT "${_target_flags}")
# ELF segments aligned for Linux's 4K, 16K, and 64K page-size kernels.
set(CMAKE_EXE_LINKER_FLAGS_INIT "--ld-path=${CMAKE_LINKER} -Wl,-z,max-page-size=65536")
set(CMAKE_SHARED_LINKER_FLAGS_INIT "${CMAKE_EXE_LINKER_FLAGS_INIT}")
set(CMAKE_MODULE_LINKER_FLAGS_INIT "${CMAKE_EXE_LINKER_FLAGS_INIT}")

set(CMAKE_FIND_ROOT_PATH "${CMAKE_SYSROOT}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
set(ENV{PKG_CONFIG_PATH} "")
set(ENV{PKG_CONFIG_SYSROOT_DIR} "${CMAKE_SYSROOT}")
set(ENV{PKG_CONFIG_LIBDIR}
    "${CMAKE_SYSROOT}/usr/lib/aarch64-linux-gnu/pkgconfig:${CMAKE_SYSROOT}/usr/share/pkgconfig")
