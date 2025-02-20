# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
sys.path.append('..')

from program_config import TensorConfig, ProgramConfig, OpConfig, CxxConfig, TargetType, PrecisionType, DataLayoutType, Place
import numpy as np
from functools import partial
from typing import Optional, List, Callable, Dict, Any, Set
import unittest
import hypothesis
import hypothesis.strategies as st

def sample_program_configs(draw):
    in_shape = draw(st.lists(st.integers(min_value=4, max_value=8), min_size=3, max_size=4))
    axis = draw(st.integers(min_value=0, max_value=len(in_shape) -1))
    index = draw(st.sampled_from([[0],[2], [3], [1, 2], [1, 2, 3], [in_shape[axis] -1], [in_shape[axis] - 2, in_shape[axis] - 1]]))
    axis_type  = draw(st.sampled_from(["int32", "int64"]))
    index_type = draw(st.sampled_from(["int32", "int64"]))
    with_tenor_axis = draw(st.sampled_from([True, False]))

    def generate_axis(*args, **kwargs):
        if axis_type == "int32":
            return np.array([axis]).astype(np.int32)
        else:
            return np.array([axis]).astype(np.int64)

    def generate_index(*args, **kwargs):
        if index_type == "int32":
            return np.array(index).astype(np.int32)
        else:
            return np.array(index).astype(np.int64)

    def generate_input_int32(*args, **kwargs):
        return np.random.random(in_shape).astype(np.int32) 

    def generate_input_int64(*args, **kwargs):
        return np.random.random(in_shape).astype(np.int64) 

    def generate_input_float32(*args, **kwargs):
        return np.random.random(in_shape).astype(np.float32) 

    generate_input = draw(st.sampled_from([generate_input_int32, generate_input_int64, generate_input_float32]))

    op_inputs = {}
    program_inputs = {}
    if(with_tenor_axis):
        op_inputs = {
                  "X" : ["input_data"], 
                  "Index" : ["index_data"],
                  "Axis" : ["axis_data"]
        }
        program_inputs={
            "input_data" : TensorConfig(data_gen=partial(generate_input)),
            "index_data" : TensorConfig(data_gen=partial(generate_index)),
            "axis_data" : TensorConfig(data_gen=partial(generate_axis))
        }
    else:
        op_inputs = {
                  "X" : ["input_data"], 
                  "Index" : ["index_data"]
        }
        program_inputs={
            "input_data" : TensorConfig(data_gen=partial(generate_input)),
            "index_data" : TensorConfig(data_gen=partial(generate_index))
        }

    gather_op = OpConfig(
        type = "gather",
        inputs = op_inputs,
        outputs = {"Out": ["output_data"]},
        attrs = {"axis" : axis})
    program_config = ProgramConfig(
        ops=[gather_op],
        weights={},
        inputs=program_inputs,
        outputs=["output_data"])
    return program_config
