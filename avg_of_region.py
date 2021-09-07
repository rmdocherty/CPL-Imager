#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 13:32:18 2021

@author: ronan
"""

import numpy as np

array = np.load("photos/g_map_3.npy")
print(array.shape)
half_index = array.shape[1] // 2
LCPL = array[:, half_index:]
RCPL = array[:, :half_index]

g_em = (2 * (LCPL - RCPL) ) / (LCPL + RCPL)

filtered = g_em[50:110, 50:110]
filtered =filtered[~np.isnan(filtered)]
#filtered_no_nan = np.where(g_em.isnan() is False, g_em, 0)
avg = np.mean(filtered)
