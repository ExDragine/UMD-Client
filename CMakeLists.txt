cmake_minimum_required(VERSION 3.10)
project(SensorHub)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# 查找需要的包
find_package(CURL REQUIRED)
find_package(jsoncpp REQUIRED)

# 手动设置libserialport路径
find_path(LIBSERIALPORT_INCLUDE_DIR libserialport.h)
find_library(LIBSERIALPORT_LIBRARY NAMES libserialport)

# 包含目录
include_directories(${LIBSERIALPORT_INCLUDE_DIR})
include_directories(${CURL_INCLUDE_DIRS})
include_directories(${JSONCPP_INCLUDE_DIRS})

# 添加可执行文件
add_executable(SensorHub main.cpp)

# 链接库
target_link_libraries(SensorHub ${LIBSERIALPORT_LIBRARY})
target_link_libraries(SensorHub CURL::libcurl)
target_link_libraries(SensorHub jsoncpp_lib)
