#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 13:32:18 2021

@author: ronan
"""

import numpy as np
from PIL import Image, ImageDraw


X0, Y0 = 35, 45
X1, Y1 = 115, 120

img = Image.open("photos/g_map3.bmp")
array = np.load("photos/g_map_3.npy")

half_index = array.shape[1] // 2
LCPL = array[:, half_index:]
RCPL = array[:, :half_index]

g_em = (2 * (LCPL - RCPL)) / (LCPL + RCPL) #introduces some nan's from div by 0

#%%
filtered = g_em[Y0:Y1, X0:X1]
filtered = filtered[np.nonzero(filtered)]
filtered = filtered[~np.isnan(filtered)] #get rid of nan's

avg = np.mean(filtered)
max_g, min_g = np.amax(filtered), np.amin(filtered)
std = np.std(filtered) #/ np.sqrt(len(filtered))
print(f"Average g_em: {avg:.5f} +/- {std:.5f}")
print(f"Max is {max_g}, min is {min_g}")
draw = ImageDraw.Draw(img)
draw.rectangle([(X0, Y0), (X1, Y1)], outline="red", fill=None)
img.show()

#%%

polygon = [(45, 26), (100, 24), (102, 34), (115, 50), (147, 82), (147, 94),
           (105, 134), (43, 130), (23, 107), (15, 76), (30, 44)]

polyImg = Image.new('L', (half_index , array.shape[0]), 0)
ImageDraw.Draw(polyImg).polygon(polygon, outline=1, fill=1)
mask = np.array(polyImg)

g_em_cropped = g_em * mask
g_em_cropped = g_em_cropped[np.nonzero(g_em_cropped)]
g_em_cropped = g_em_cropped[~np.isnan(g_em_cropped)] #get rid of nan's

avg = np.mean(g_em_cropped)
max_g, min_g = np.amax(g_em_cropped), np.amin(g_em_cropped)
std = np.std(g_em_cropped) #/ np.sqrt(len(g_em_cropped))
print(f"Average g_em: {avg:.5f} +/- {std:.5f}")
print(f"Max is {max_g}, min is {min_g}")
drawPoly = ImageDraw.Draw(img)
drawPoly.polygon(polygon, outline="red", fill=None)
img.show()