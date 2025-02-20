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

from numpy.core.fromnumeric import reshape
sys.path.append('..')

from program_config import TensorConfig, ProgramConfig, OpConfig, CxxConfig, TargetType, PrecisionType, DataLayoutType, Place
import numpy as np
from functools import partial, reduce
from typing import Optional, List, Callable, Dict, Any, Set
import unittest

import hypothesis
from hypothesis import given, settings, seed, example, assume, reproduce_failure
import hypothesis.strategies as st

def sample_program_configs(draw):
    pick_test=draw(st.sampled_from(["RemoveReshape2Pattern"]))
    if pick_test=="RemoveReshape2Pattern":
        in_shape = draw(st.lists(
            st.integers(
                min_value=2, max_value=30), min_size=2, max_size=5))
        input_axis = draw(st.sampled_from([0, 1, 2, 3, -1]))
        assume(input_axis < len(in_shape))

        softmax_config = OpConfig(
            type = "softmax",
            inputs = {
                "X": ["input_data"]
            },
            outputs = {
                "Out": ["softmax_data"]
            },
            attrs = {
                "axis": input_axis
            }
        )

        reshape2_config = OpConfig(
            type = "reshape2",
            inputs = {
                "X" : ["softmax_data"]
            },
            outputs = {
                "Out": ["output_data"],
                "XShape": ["x_shape"]
            },
            attrs = {
                "shape": in_shape,
            }
        )

        ops = [softmax_config, reshape2_config]
        program_config = ProgramConfig(
            ops=ops,
            weights={},
            inputs={"input_data": TensorConfig(shape=in_shape)},
            outputs=["output_data"])
        return program_config
    else:
        batch=draw(st.integers(min_value=2, max_value=8))
        in_shape=[batch, 1001, 1, 1]
        input_axis = draw(st.sampled_from([0, 1, 2, 3, -1]))
        assume(input_axis < len(in_shape))

        squeeze2_config = OpConfig(
            type = "squeeze2",
            inputs = {
                "X":["input_data"]
            },
            outputs = {
                "Out": ["squeeze2_output_data"],
                "XShape":["squeeze2_xshape"]
            },
            attrs = {
                "axes": []
            }
        )

        reshape2_config = OpConfig(
            type = "reshape2",
            inputs = {
                "X" : ["squeeze2_output_data"],
            },
            outputs = {
                "Out": ["reshape2_output_data"],
                "XShape": ["squeeze2_xshape"],
            },
            attrs = {
                "shape": [batch, 1001]
            }
        )

        softmax_config = OpConfig(
            type = "softmax",
            inputs = {
                "X": ["reshape2_output_data"]
            },
            outputs = {
                "Out": ["output_data"]
            },
            attrs = {
                "axis": input_axis
            }
        )

        ops = [squeeze2_config, reshape2_config, softmax_config]
        program_config = ProgramConfig(
            ops=ops,
            weights={},
            inputs={"input_data": TensorConfig(shape=in_shape)},
            outputs=["output_data"])
        return program_config
