#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 16:13:52 2021

@author: ronan
"""

from PIL import Image
import numpy as np
from scipy import stats, ndimage
import matplotlib.pyplot as plt


def pretty_subplot(axis, x_label, y_label, title, fontsize):  #formatting graphs
    axis.set_xlabel(x_label, fontsize=fontsize)
    axis.set_title(title, fontsize=fontsize + 2)
    axis.set_ylabel(y_label, fontsize=fontsize)
    axis.tick_params(labelsize=fontsize)
    axis.set_facecolor("#fffcf5")


class CPL_img_analysis():
    def __init__(self, path, name):
        self._pil_image = Image.open(path).convert('LA')
        self._np_arr = np.array(self._pil_image)[:, :, 0]
        self._flattened = self._np_arr
        self._flattened.flatten()
        self._name = name

    def get_stats(self):
        img_arr = self._np_arr
        max_br = np.max(img_arr)
        min_br = np.min(img_arr)
        avg_br = np.mean(img_arr)
        std_br = np.std(img_arr) / np.sqrt(len(img_arr))
        #mode_br = stats.mode(img_arr)
        #median_br = ndimage.median(img_arr)
        print(f"stats for {self._name}: \n Max is {max_br} \n Min is {min_br} \n Avg is {avg_br} +/- {std_br}")
        return max_br, min_br, avg_br, std_br

    def get_non_zero_regions(self):
        w = self._np_arr[self._np_arr != 0]
        return w

    def get_histo(self):
        img_arr = self._np_arr
        histo, edges = np.histogram(img_arr, bins=250, range=(0,250))
        return histo, edges


min_LCPL = CPL_img_analysis("photos/LCPL_min_grey.png", "Min LCPL")
max_LCPL = CPL_img_analysis("photos/LCPL_max_grey.png", "Max LCPL")

min_RCPL = CPL_img_analysis("photos/RCPL_min_grey.png", "Min RCPL")
max_RCPL = CPL_img_analysis("photos/RCPL_max_grey.png", "Max RCPL")

colours = ["red", "red", "cornflowerblue", "cornflowerblue"]
fig, axs = plt.subplots(2, 2)
for index, CPL in enumerate([min_LCPL, max_LCPL, min_RCPL, max_RCPL]):
    ax = axs[index // 2, index % 2]

    stats = CPL.get_stats()
    avg, stderr = stats[2], stats[3]

    histo, edges = CPL.get_histo()

    #ax.set_title(CPL._name)
    ax.hist(x=histo, bins=edges, color=colours[index])
    ax.vlines(x=avg, ymin=0, ymax=35, color="black", ls="--", label=f"Avg={avg:.2f} +/- {stderr:.2f}")
    pretty_subplot(ax, "Pixel value", "Count", CPL._name, 12)
    ax.legend(fontsize=12)
    #ax.set_xlim(0, 250)
    
    