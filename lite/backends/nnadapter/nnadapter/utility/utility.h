// Copyright (c) 2019 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include <sys/time.h>
#include <algorithm>
#include <cmath>
#include <map>
#include <string>
#include <vector>
#include "nnadapter.h"  // NOLINT
#include "utility/logging.h"

namespace nnadapter {

// Check quantization type
bool IsPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsPerChannelQuantType(NNAdapterOperandPrecisionCode type);
bool IsAsymmetricQuantType(NNAdapterOperandPrecisionCode type);
bool IsSymmetricQuantType(NNAdapterOperandPrecisionCode type);
bool IsAsymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsSymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsSymmPerChannelQuantType(NNAdapterOperandPrecisionCode type);
bool IsUInt8AsymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsInt8SymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsInt8SymmPerChannelQuantType(NNAdapterOperandPrecisionCode type);
bool IsUInt16AsymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsInt16SymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsInt16SymmPerChannelQuantType(NNAdapterOperandPrecisionCode type);
bool IsUInt32AsymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsInt32SymmPerLayerQuantType(NNAdapterOperandPrecisionCode type);
bool IsInt32SymmPerChannelQuantType(NNAdapterOperandPrecisionCode type);
int64_t GetOperandPrecisionDataLength(NNAdapterOperandPrecisionCode type);
int64_t GetOperandTypeBufferLength(const NNAdapterOperandType& type);

// Copy operand type under certain conditions
void CopyOperandType(NNAdapterOperandType* dst_type,
                     const NNAdapterOperandType& src_type);
void CopyOperandTypeWithDimensions(NNAdapterOperandType* dst_type,
                                   const NNAdapterOperandType& src_type);
void CopyOperandTypeWithPrecision(NNAdapterOperandType* dst_type,
                                  const NNAdapterOperandType& src_type);
void CopyOperandTypeWithQuantParams(NNAdapterOperandType* dst_type,
                                    const NNAdapterOperandType& src_type);
void CopyOperandTypeExceptQuantParams(NNAdapterOperandType* dst_type,
                                      const NNAdapterOperandType& src_type);

// Caculate the production of the given dimensions
int64_t ProductionOfDimensions(const int32_t* input_dimensions_data,
                               uint32_t input_dimensions_count);
int64_t ProductionOfDimensions(const std::vector<int32_t>& input_dimensions);
// Transpose the given dimensions, similar to numpy.transpose
void TransposeDimensions(int32_t* input_dimensions,
                         const std::vector<int32_t>& permutation,
                         int32_t* output_dimensions_ptr = nullptr);
// Reshape the given dimensions, similar to numpy.reshape
void ReshapeDimensions(int32_t* input_dimensions_data,
                       uint32_t* input_dimensions_count,
                       const std::vector<int32_t>& dimensions,
                       int32_t* output_dimensions_data_ptr = nullptr,
                       uint32_t* output_dimensions_count_ptr = nullptr);

// Initialize an identity dimorder vector from the given rank, such as (0, 1, 2,
// 3) for rank=4
std::vector<int32_t> IdentityPermutation(size_t rank);
// Inverse a dimorder vector, such as we can get (0, 3, 1, 2) when the origin
// one is (0, 2, 3, 1)
std::vector<int32_t> InversePermutation(
    const std::vector<int32_t>& permutation);
// Multipy a dimorder vector, such as we can get (0, 1, 2, 3) when the origin
// one is (0, 2, 3, 1) and multiplier is (0, 3, 1, 2)
std::vector<int32_t> MultiplyPermutation(
    const std::vector<int32_t>& permutation,
    const std::vector<int32_t>& multiplier);
// Is a identity dimorder vector, such as (0, 1), (0, 1, 2), and (0, 1, 2, 3)
bool IsIdentityPermutation(const std::vector<int32_t>& permutation);

// A naive implementation of transpose operation
template <typename T>
void TransposeData(const T* input,
                   T* output,
                   const std::vector<int32_t>& permutation,
                   const int32_t* input_dimensions,
                   int32_t* output_dimensions_ptr = nullptr) {
  auto permutation_count = permutation.size();
  NNADAPTER_CHECK_GE(permutation_count, 2);
  std::vector<int32_t> output_dimensions(permutation_count);
  for (size_t i = 0; i < permutation_count; i++) {
    output_dimensions[i] = input_dimensions[i];
  }
  for (size_t i = 0; i < permutation_count; i++) {
    output_dimensions[i] = input_dimensions[permutation[i]];
  }
  if (!IsIdentityPermutation(permutation)) {
    std::vector<int64_t> input_strides(permutation_count, 1);
    std::vector<int64_t> output_strides(permutation_count, 1);
    for (int i = permutation_count - 2; i >= 0; i--) {
      input_strides[i] = input_strides[i + 1] * input_dimensions[i + 1];
      output_strides[i] = output_strides[i + 1] * output_dimensions[i + 1];
    }
    auto element_count = input_strides[0] * input_dimensions[0];
    for (int64_t i = 0; i < element_count; i++) {
      // Calculate the indexes for input
      int64_t input_offset = i;
      std::vector<int64_t> input_index(permutation_count, 0);
      for (size_t j = 0; j < permutation_count; j++) {
        input_index[j] = input_offset / input_strides[j];
        input_offset %= input_strides[j];
      }
      // Calculate the transposed indexes for output
      std::vector<int64_t> output_index(permutation_count, 0);
      for (size_t j = 0; j < permutation_count; j++) {
        output_index[j] = input_index[permutation[j]];
      }
      // Calculate the element offset for output
      int64_t output_offset = 0;
      for (size_t j = 0; j < permutation_count; j++) {
        output_offset += output_strides[j] * output_index[j];
      }
      output[output_offset] = input[i];
    }
  } else {
    memcpy(
        output, input, sizeof(T) * ProductionOfDimensions(output_dimensions));
  }
  if (output_dimensions_ptr) {
    for (size_t i = 0; i < permutation_count; i++) {
      output_dimensions_ptr[i] = output_dimensions[i];
    }
  }
}

// A naive implementation of quantize and dequantize operation
template <typename T>
void QuantizeData(const float* input_data,
                  size_t input_data_count,
                  float* input_scale,
                  size_t input_scale_count,
                  T* output_data) {
  bool per_layer = input_scale_count == 1;
  NNADAPTER_CHECK(per_layer || input_data_count == input_scale_count)
      << "Only input_scale_count == 1 and input_scale_count == "
         "input_data_count is supported.";
  int quant_bits = sizeof(T) * 8;
  auto dtype_max = static_cast<int>((1 << (quant_bits - 1)) - 1);
  auto dtype_min = static_cast<int>(0 - dtype_max);
  for (size_t i = 0; i < input_data_count; i++) {
    int scale_index = per_layer ? 0 : i;
    output_data[i] = std::min(
        std::max(static_cast<T>(input_data[i] / input_scale[scale_index]),
                 dtype_min),
        dtype_max);
  }
}

template <typename T>
void DequantizeData(const T* input_data,
                    size_t input_data_count,
                    float* input_scale,
                    size_t input_scale_count,
                    float* output_data) {
  bool per_layer = input_scale_count == 1;
  NNADAPTER_CHECK(per_layer || input_data_count == input_scale_count)
      << "Only input_scale_count == 1 and input_scale_count == "
         "input_data_count is supported.";
  int quant_bits = sizeof(T) * 8;
  auto dtype_max = static_cast<int>((1 << (quant_bits - 1)) - 1);
  auto dtype_min = static_cast<int>(0 - dtype_max);
  for (size_t i = 0; i < input_data_count; i++) {
    int scale_index = per_layer ? 0 : i;
    output_data[i] = std::min(std::max(input_data[i], dtype_min), dtype_max) *
                     input_scale[scale_index];
  }
}

// Convert the symmetric quantization data to the asymmetric quantization data
void Symm2AsymmData(const int8_t* input_data,
                    size_t input_data_count,
                    int32_t zero_point,
                    uint8_t* output_data);
void Asymm2SymmData(const uint8_t* input_data,
                    size_t input_data_count,
                    int32_t zero_point,
                    int8_t* output_data);

// Calculate a new axis according to the given permutation
int32_t TransposeAxis(int32_t axis, const std::vector<int32_t>& permutation);

// Parse and get the key value map from a string
std::map<std::string, std::string> GetKeyValues(
    const char* properties,
    const std::string& delimiter = ";",
    const std::string& assignment = "=");

// A naive implementation of CRC32C
uint32_t CRC32C(const uint8_t* buffer, size_t size);

// Read a file and output the data into an uint8_t array
bool ReadFile(const std::string& path, std::vector<uint8_t>* buffer);

// Write an uint8_t array to a file
bool WriteFile(const std::string& path, const std::vector<uint8_t>& buffer);

inline int64_t GetCurrentUS() {
  struct timeval time;
  gettimeofday(&time, NULL);
  return 1000000LL * (int64_t)time.tv_sec + (int64_t)time.tv_usec;
}

template <typename T>
int64_t GetSpanCount(T start, T end, T step) {
  return std::is_integral<T>::value
             ? ((std::abs(end - start) + std::abs(step) - 1) / std::abs(step))
             : std::ceil(std::abs((end - start) / step));
}

// Read environment variables of string type
std::string GetStringFromEnv(const std::string& str,
                             const std::string& def = "");

// Read environment variables of bool type
bool GetBoolFromEnv(const std::string& str, bool def = false);

// Read environment variables of int type
int GetIntFromEnv(const std::string& str, int def = 0);

// Read environment variables of double type
double GetDoubleFromEnv(const std::string& str, double def = 0.0);

// Read environment variables of int64 type
uint64_t GetUInt64FromEnv(const std::string& str, uint64_t def = 0ul);

}  // namespace nnadapter
