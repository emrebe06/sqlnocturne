cmake_minimum_required(VERSION 3.16)
project(sqlnocturne_native VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(sqlnocturne_native SHARED
    c/nocturne_abi.c
    c/nocturne_alloc.c
    c/nocturne_scan.c
    c/nocturne_asm.c
    cpp/engine.cpp
    cpp/json_writer.cpp
    cpp/plan_cache.cpp
)

target_include_directories(sqlnocturne_native PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/c
    ${CMAKE_CURRENT_SOURCE_DIR}/cpp
)

target_compile_definitions(sqlnocturne_native PRIVATE NOCTURNE_BUILD)
