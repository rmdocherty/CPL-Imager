#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 13:32:18 2021

@author: ronan
"""

import numpy as np

array = np.load("photos/g_map.npy")
print(array.shape)
half_index = array.shape[1] // 2
LCPL = array[:, half_index:]
RCPL = array[:, :half_index]

g_em = (2 * (LCPL - RCPL) ) / (LCPL + RCPL)

filtered = g_em[60:100, 60:100]
avg = np.mean(filtered)
