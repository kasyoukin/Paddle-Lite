# Copyright (c) 2019 PaddlePaddle Authors. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

include(driver/configuration.cmake)

include_directories(.)

add_subdirectory(core)
add_subdirectory(utility)
add_subdirectory(optimizer)
add_subdirectory(runtime)
add_subdirectory(driver)

add_library(nnadapter SHARED nnadapter.cc)
target_link_libraries(nnadapter "-Wl,--start-group" ${NNADAPTER_UTILITIES} ${NNADAPTER_OPTIMIZERS} ${NNADAPTER_CORE} ${NNADAPTER_RUNTIME} "-Wl,--end-group")
