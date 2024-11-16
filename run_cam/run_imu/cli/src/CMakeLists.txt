cmake_minimum_required(VERSION 3.16)
add_compile_definitions(NOMINMAX=1)
add_compile_definitions(THREADING_ENABLE=true)
add_compile_definitions(__CLI__=true)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../cpp)
set(CPP_PLUGIN_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../cpp/Plugins)
set(CLI_PLUGIN_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../plugins)

add_subdirectory(${CPP_ROOT} oVnSensor)
add_subdirectory(${CPP_PLUGIN_ROOT}/RegisterScan RegisterScanPlugin)
add_subdirectory(${CPP_PLUGIN_ROOT}/FirmwareUpdate FirmwareUpdatePlugin)

set(SOURCES
	AssemblyInfo.cpp
	CLI_Sensor.cpp
)

add_library(${PROJECT_NAME} SHARED ${SOURCES})

target_link_libraries(${PROJECT_NAME} oVnSensor)
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../include)
target_include_directories(${PROJECT_NAME} PRIVATE oVnSensor)

target_include_directories(${PROJECT_NAME} PUBLIC ${CPP_PLUGIN_ROOT}/SimpleLogger)
target_include_directories(${PROJECT_NAME} PUBLIC ${CLI_PLUGIN_ROOT}/SimpleLogger)

target_include_directories(${PROJECT_NAME} PUBLIC ${CPP_PLUGIN_ROOT}/DataExport/include)
target_include_directories(${PROJECT_NAME} PUBLIC ${CLI_PLUGIN_ROOT}/DataExport)

target_include_directories(${PROJECT_NAME} PUBLIC ${CPP_PLUGIN_ROOT}/RegisterScan)
target_include_directories(${PROJECT_NAME} PUBLIC ${CLI_PLUGIN_ROOT}/RegisterScan)
target_link_libraries(${PROJECT_NAME} RegisterScanPlugin)

target_include_directories(${PROJECT_NAME} PUBLIC ${CPP_PLUGIN_ROOT}/FirmwareUpdate/include)
target_include_directories(${PROJECT_NAME} PUBLIC ${CLI_PLUGIN_ROOT}/FirmwareUpdate)
target_link_libraries(${PROJECT_NAME} FirmwareUpdatePlugin)

SET_TARGET_PROPERTIES(${PROJECT_NAME} PROPERTIES COMPILE_FLAGS "/clr")
STRING(REPLACE "/EHsc" "/EHa" CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS})
STRING(REPLACE "/RTC1" "" CMAKE_CXX_FLAGS_DEBUG ${CMAKE_CXX_FLAGS_DEBUG})

# Copy output dll to "net" directory
set(DLL_OUTPUT_DIR ${CPP_ROOT}/../net/)

if(NOT EXISTS "${DLL_OUTPUT_DIR}")
	file(MAKE_DIRECTORY "${DLL_OUTPUT_DIR}")
endif()

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:VnSdk_Net> ${DLL_OUTPUT_DIR})
