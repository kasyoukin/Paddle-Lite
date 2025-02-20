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
from hypothesis import given, settings, seed, example, assume, reproduce_failure
import hypothesis.strategies as st

def sample_program_configs(draw):
    in_shape = draw(st.lists(st.integers(min_value=1, max_value=20), min_size=2, max_size=5))
    axis=draw(st.integers(min_value=-1, max_value=len(in_shape)-1))
    right=draw(st.integers(min_value=axis, max_value=len(in_shape)-1))

    fill_constant_shape=[]
    if axis==-1:
        fill_constant_shape=in_shape
    else:
        left=axis
        fill_constant_shape=in_shape[left:max(left+1,right)] 

    threshold=draw(st.floats(min_value=0, max_value=1))
    scale=draw(st.floats(min_value=0.5, max_value=5))
    offset=draw(st.floats(min_value=0, max_value=1))

    hard_swish_op = OpConfig(
        type = "hard_swish",
        inputs = {"X" : ["input_data"]},
        outputs = {"Out": ["hard_swish_output_data"]},
        attrs = {
            "threshold" : threshold,
            "scale" : scale,
            "offset" : offset})

    fill_constant_op = OpConfig(
        type = "fill_constant",
        inputs = {},
        outputs = {"Out": ["fill_constant_output_data"]},
        attrs = {"dtype" : 5,
                 "shape" : fill_constant_shape,
                 "value" : 1.,
                 "force_cpu" : False,
                 "place_type" : -1
                 })

    elementwise_mul_op = OpConfig(
        type = "elementwise_mul",
        inputs = {"X": ["hard_swish_output_data"], "Y": ["fill_constant_output_data"]},
        outputs = {"Out": ["elementwise_mul_output_data"]},
        attrs = {"axis": axis})    

    abs_op = OpConfig(
        type = "assign",
        inputs = {"X" : ["elementwise_mul_output_data"]},
        outputs = {"Out": ["output_data"]},
        attrs = {})

    ops = [hard_swish_op, fill_constant_op, elementwise_mul_op, abs_op]
    program_config = ProgramConfig(
        ops=ops,
        weights={},
        inputs={"input_data":TensorConfig(shape=in_shape)},
        outputs=["output_data"])
    return program_config
