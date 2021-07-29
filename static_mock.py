#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 16:33:35 2021

@author: ronan
"""
from colourmapper import ColourMapper
import numpy as np

c = ColourMapper("test")

np.random.seed(1)

IMG_WIDTH = 200
IMG_HEIGHT = 200

LCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))
RCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))

c = ColourMapper("Raw")
c.colour_map(LCPL, RCPL, debug=False)
