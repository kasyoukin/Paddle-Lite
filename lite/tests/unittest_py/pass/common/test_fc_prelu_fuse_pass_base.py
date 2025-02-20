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
from functools import partial, reduce
from typing import Optional, List, Callable, Dict, Any, Set
import unittest

import hypothesis
from hypothesis import given, settings, seed, example, assume, reproduce_failure
import hypothesis.strategies as st

def mul(x, y):
    return x*y

def sample_program_configs(draw):
    in_shape=draw(st.lists(st.integers(min_value=5, max_value=64), min_size=2, max_size=4))
    bias_shape=draw(st.lists(st.integers(min_value=1, max_value=64), min_size=1, max_size=2))
    weight_shape=draw(st.lists(st.integers(min_value=5, max_value=64), min_size=2, max_size=2))
    in_num_col_dims_data=draw(st.integers(min_value=1, max_value=len(in_shape)-1))
    padding_weights_data=draw(st.sampled_from([False, True]))
    has_bias=draw(st.sampled_from([True, False]))

    w_dims1=weight_shape[1]
    w_dims0=weight_shape[0] 
    if padding_weights_data==True:
        w_dims1=weight_shape[1]-4
        w_dims0=weight_shape[0]-4
    if has_bias==True:      
        if len(bias_shape)==2:
            assume(bias_shape[0]==1)
        assume(bias_shape[-1]==w_dims1)
    inshape0=reduce(mul, in_shape[0:in_num_col_dims_data])
    inshape1=reduce(mul, in_shape[in_num_col_dims_data:])    
    assume(inshape1==w_dims0)
    fc_out_shape=[]
    for i in range(0, in_num_col_dims_data):
        fc_out_shape.append(in_shape[i])  
    fc_out_shape.append(w_dims1)
    
    Alpha_shape=[]
    mode_data=draw(st.sampled_from(["all", "channel", "element"]))
    if mode_data=="all":
        Alpha_shape=[1]
    elif mode_data=="channel":
        Alpha_shape=[fc_out_shape[1]]
        assume(len(fc_out_shape)>=2)
    elif mode_data=="element":
        Alpha_shape = fc_out_shape    
        assume(len(fc_out_shape)>=1)

    inputs_fc={}
    if has_bias==True:
       inputs_fc = {"Input": ["input_data"],"W":["weight_data"],"Bias":["bias_data"]} 
    else:
       inputs_fc = {"Input": ["input_data"],"W":["weight_data"]}         
    fc_op = OpConfig(
        type = "fc",
        inputs = inputs_fc,
        outputs = {"Out": ["fc_output_data"]},
        attrs = {
            "in_num_col_dims": in_num_col_dims_data,
            "activation_type": "",
            "padding_weights": padding_weights_data,
            "use_mkldnn": False,
        })
    
    prelu_op = OpConfig(
        type = "prelu",
        inputs = {"X": ["fc_output_data"], "Alpha": ["alpha_data"]},
        outputs = {"Out": ["output_data"]},
        attrs = {"mode": mode_data,
                "data_format": "NCHW"}
    )
    
    inputs_={}
    ops = [fc_op, prelu_op]
    program_config = ProgramConfig(
        ops=ops,
        weights={
            "bias_data": TensorConfig(shape=bias_shape)
        },
        inputs={
            "weight_data": TensorConfig(shape=weight_shape),          
            "input_data": TensorConfig(shape=in_shape),
            "alpha_data": TensorConfig(shape=Alpha_shape)
        },
        outputs=["output_data"])
    return program_config
