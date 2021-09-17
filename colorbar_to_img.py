#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 15:07:41 2021

@author: ronan
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

#from matplotlib import rcParams
#rcParams.update({'figure.autolayout': True})

a = np.array([[0,1]])
fig = plt.figure(figsize=(1, 5))
img = plt.imshow(a, cmap="Blues")
plt.gca().set_visible(False)
cax = plt.axes([0.1, 0.2, 0.8, 0.6])
plt.colorbar(orientation="vertical", cax=cax)
plt.tight_layout(pad=1.6)
plt.close()

canvas = fig.canvas
canvas.draw()
pil_image = Image.frombytes('RGB', canvas.get_width_height(), 
                 canvas.tostring_rgb())
pil_image.show()