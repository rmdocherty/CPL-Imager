#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 13:10:19 2021

@author: ronan
"""

#DEPENDENCIES
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm #use 'coolwarm' ?
#seed RNG
np.random.seed(1)

"""
Given two mock np arrays with dtype=np.ushort that represent the images
recieved on the two cameras, colourmap their respective polarisations and 
create combined map. The images recieved from the cameras will be arrays
containing values from 0 to 65,535 so may need to normalise this to 0 to 1
assuming monochrome arrays where maximum value is maximum brightness.
"""

IMG_WIDTH = 100
IMG_HEIGHT = 100

LCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))
#assume RCPL is in 'other direction' 
RCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))

DOCP = (LCPL + RCPL) #magnitude of CPL
g_em = 2 * (LCPL + -1 * RCPL) / DOCP #definition of g_em


fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
axes = [ax1, ax2, ax3, ax4]
data = [LCPL, RCPL, g_em, DOCP]
cmaps = ["Oranges", "Blues", "coolwarm", "plasma"]
titles = ["LCPL", "RCPL", "g_em", "DOCP"]

for i in range(4):
    a = axes[i]
    cmap = cmaps[i]
    title = titles[i]
    d = data[i]
    im = a.imshow(d, cmap=plt.get_cmap(cmap), interpolation='nearest')
    a.axis('off')
    fig.colorbar(im, ax=a)
    a.set_title(title)

plt.show()