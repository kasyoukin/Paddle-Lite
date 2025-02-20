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
from hypothesis import given, settings, seed, example, assume
import hypothesis.strategies as st

def sample_program_configs(draw):
    length = draw(st.lists(
        st.integers(
            min_value=1, max_value=5), min_size=4, max_size=10))
    in_shape = draw(st.lists(
        st.integers(
            min_value=5, max_value=10), min_size=1, max_size=3))
    in_shape.insert(0, len(length))

    def generate_input(*args, **kwargs):
        return np.random.uniform(0.1, 1, in_shape).astype('float32')

    def generate_length(*args, **kwargs):
        return np.array(length).astype('int64')

    ops_config = OpConfig(
        type = "sequence_unpad",
        inputs = {
            "X": ["input_data"],
            "Length": ["length_data"],
        },
        outputs = {
            "Out": ["output_data"]
        },
        attrs = {}
        )

    program_config = ProgramConfig(
        ops=[ops_config],
        weights={},
        inputs={
            "input_data": 
            TensorConfig(data_gen=partial(generate_input)),
            "length_data":
            TensorConfig(data_gen=partial(generate_length))
        },
        outputs=["output_data"])

    return program_config
