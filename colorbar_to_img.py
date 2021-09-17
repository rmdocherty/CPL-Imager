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
LEFT = 0.05
BOTTOM = 0.2
WIDTH = 0.08
HEIGHT = 0.6


a = np.array([[0,1]])
fig = plt.figure()
img = plt.imshow(a, cmap="Blues")
plt.gca().set_visible(False)
cax = plt.axes([LEFT, BOTTOM, WIDTH, HEIGHT])
plt.colorbar(orientation="vertical", cax=cax)

canvas = fig.canvas

can_dims = canvas.get_width_height()
offset = (int(can_dims[0] * LEFT) - 10, int(can_dims[1] * BOTTOM) - 30)
bar_dims = (int(can_dims[0] * WIDTH) * 1.9, int(can_dims[1] * HEIGHT))
canvas.draw()
pil_image = Image.frombytes('RGB', can_dims, 
                 canvas.tostring_rgb())
pil_image = pil_image.crop((offset[0], offset[1], offset[0] + bar_dims[0], offset[1] + bar_dims[1] + 40))
pil_image.show()

#%%
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib as mpl

fig = plt.figure()#figsize=(1, 5)
ax = fig.add_axes([0.9, 0.10, 0.05, 0.85])

cmap = cm.get_cmap('RdBu')

cb = mpl.colorbar.ColorbarBase(ax, orientation='vertical', 
                               cmap=cmap)
plt.tight_layout(pad=1.6)
plt.savefig('just_colorbar', bbox_inches='tight')

#%%

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image

fig, ax = plt.subplots(1, 1)

fraction = 1  # .05

norm = mpl.colors.Normalize(vmin=-3, vmax=99)
cbar = ax.figure.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap='Blues'),
            ax=ax, pad=.05, extend='both', fraction=fraction)

ax.axis('off')
#plt.show()
canvas = fig.canvas

pil_image = Image.frombytes('RGB', canvas.get_width_height(), 
                 canvas.tostring_rgb())
pil_image.show()

#%%

LEFT = 0.05
BOTTOM = 0.2
WIDTH = 0.08
HEIGHT = 0.6


a = np.array([[-2,2]])
fig = plt.figure()
img = plt.imshow(a, cmap="Blues")
plt.gca().set_visible(False)
cax = plt.axes([LEFT, BOTTOM, WIDTH, HEIGHT])
plt.colorbar(orientation="vertical", cax=cax)
plt.savefig("colorbar.png", transparent=True)
plt.close()

img = Image.open("colorbar.png")
img = img.crop((offset[0], offset[1], offset[0] + bar_dims[0], offset[1] + bar_dims[1] + 40))
img.show()