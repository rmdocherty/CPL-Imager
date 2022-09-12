#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 11:35:13 2021

@author: ronan
"""

from matplotlib import cm, colors
from PIL import Image
import numpy as np # maybe can just import hstack by itself later
import matplotlib.pyplot as plt
import json


def dA(LCPL, RCPL):
    div = np.divide(RCPL, LCPL, out=np.ones_like(RCPL), where=LCPL*RCPL!=0)
    return np.log10(div)

def CD(dA): #in mdeg
    return np.arctan(np.tanh( (np.log(10)*dA) /4 )) * (180*10**3) / np.pi

def get_json_obj():
    with open("config.json", "r") as config_file:
        config_json = json.load(config_file)
    return config_json

def read_from_json(field):
    config_json = get_json_obj()
    try:
        out = config_json[field]
    except:
        raise Exception("Wrong key for config JSON!")
    return out

def write_to_json(field, value):
    config_json = get_json_obj()
    config_json[field] = value
    with open("config.json", "w") as config_file:
        json.dump(config_json, config_file)
    return 0

class ColourMapper():
    """
    ColourMapper.

    Given a RCPL and an LCPL np array of brightnesses from their respective
    queues and an operating mode, colour map them based on a config file and
    return the output PIL image(s) for Tkinter to use.
    """

    def __init__(self, mode):
        self._mode = mode
        try: # grab user configs
            self._cmaps = self._get_cmaps_from_config()
        except (NameError, IOError, RuntimeError): # use defaults
            self._cmaps = {"Raw": ["Oranges", "Blues"], "g_em": "coolwarm", "DOCP": "plasma"}

    def set_mode(self, mode): # so can set mode w/o re-initialising
        self._mode = mode

    def set_cmaps(self, list_cmaps):
        """Given list of strings referring to mpl cmaps, set the cap mode """
        self._cmaps = {"Raw": [list_cmaps[0], list_cmaps[1]], "DOCP": list_cmaps[2], "g_em": list_cmaps[3]} #need reverse in here due to r/l cpl defintions

    def _get_cmaps_from_config(self):
        """
        get_cmaps_from_config.

        Generate DICT from config txt file that lets users map desired
        matplotlib cmaps to the operating mode. Probably shouldn't let
        users be able to change the mode names in the config file but que sera.

        Returns
        -------
        cmap_dict : DICT
            Dictionary mapping mode strings to chosen matplotlib colourmap
            strings.
        """
        cmap_dict = read_from_json("cmaps")
        return cmap_dict

    def colour_map(self, img1, img2, debug=False):
        """
        colour_map.

        Given the two images from the camera and the mode, perform the mapping
        process. If in Raw mode, cmap both images separately, combine and then
        return image. If in g_em mode, combine both arrays using g_em formula
        before cmapping and returning single image. If in DOCP mode, calc. the
        DOCP by adding magnitudes then cmap and return single image.

        Parameters
        ----------
        img1 : NP ARRAY
            LCPL image from camera 1. Don't know dtype, may need to rescale
            before cmapping
        img2 : NP ARRAY
            Same as img1 but RCPL from camera 2

        Returns
        -------
            A PIL Image Object

        """
        
        cmap1, cmap2 = self._cmaps["Raw"]
        cmap3, cmap4 = self._cmaps["DOCP"], self._cmaps["g_em"]
        cmapped_img1 = self._single_cmap(img1, cmap1)
        cmapped_img2 = self._single_cmap(img2, cmap2)
        
        delta_A = dA(img1, img2) # np.log10(img1/img2)#(img1 - img2)
        test = img2 - img1
        cmapped_img3 = self._single_cmap(delta_A, cmap3, symm=True)
        theta_mdeg = CD(delta_A) # np.arctan(np.tanh( (np.log(10)*dA) /4 )) * (180*10**3) / np.pi
        cmapped_img4 = self._single_cmap(theta_mdeg, cmap4, symm=True)
        print(np.mean(theta_mdeg))
        top = np.hstack((cmapped_img1, cmapped_img2))
        bot = np.hstack((cmapped_img3, cmapped_img4))
        mapped = np.vstack((top, bot))

        out = Image.fromarray(mapped) #convert to PIL Image
        if debug is True:
            out.show() #see what's going on -get rid of later
        return out

    def _single_cmap(self, img, cmap_string, symm=False):
        """
        single_cmap.

        Colour maps a single image.

        Parameters
        ----------
        img : NP ARRAY
            Must be normalised from 0-1.0.
        cmap_string : STR
            String that corresponds to the desired matplotlib colourmap.

        Returns
        -------
        out_im : PIL IMAGE
            Colour mapped PIL image for use in the tkinter widget.
        """
        cmap = cm.get_cmap(cmap_string) #grab cmap object from string
        if symm == True:
            vmax = max(np.abs(np.amax(img)), np.abs(np.amin(img)))
            norm = colors.Normalize(vmin=-vmax,vmax=vmax)
            out_im = cmap(norm(img), bytes=True)
        else:
            out_im = cmap(img, bytes=True)
        return out_im

    def gen_colourbar(self, limits=[]):
        """
        gen_colourbar.

        Given the mode of the cmapper, get the colourbar responding to the mode's
        colourmap in the form of a PIL image. For the 'Raw' this obviously needs
        to be two colourbars stacked next to each other.

        Returns
        -------
        out : PIL IMAGE
            Colourbar(s) corresponding to the cmap mode.

        """

        cmap1, cmap2 = self._cmaps["Raw"]
        cmap3, cmap4 = self._cmaps["DOCP"], self._cmaps["g_em"]
        raw_lims = np.array([[0, 1]])
        
        cbar1, cbar2 = self._single_colourbar(raw_lims, cmap1), self._single_colourbar(raw_lims, cmap2)
        cbar3, cbar4 = self._single_colourbar(limits[0], cmap3), self._single_colourbar(limits[1], cmap4)
        out = Image.new('RGBA', (cbar1.width + cbar2.width, cbar1.height + cbar2.height))
        out.paste(cbar1, (0, 0))
        out.paste(cbar2, (cbar1.width, 0))
        out.paste(cbar3, (0, cbar1.height))
        out.paste(cbar4, (cbar1.width, cbar1.height))
        
        return out

    def _single_colourbar(self, limits, cmap_string):
        """
        single_colourbar.

        Given limits and colourmap string, generate PIL image of the colourbar
        and return it. This unfortunately involves creating a matplotlib plot
        of just the colourbar, grabbing the renderer data as bytes and feeding
        it into a new PIL image, casuing an ugly popup whenever modes are
        switched (sorry!).

        Parameters
        ----------
        limits : np.array
            np.array of the limits of the colourmap (0-1 for raw/DOCP and
            -2-+2 for g_em).
        cmap_string : STR
            String corresponding to a matplotlib colourmap.

        Returns
        -------
        img : PIL IMAGE
            Colourbar(s) corresponding to the cmap mode..

        """
        LEFT = 0.05
        BOTTOM = 0.2
        WIDTH = 0.1#0.08
        HEIGHT = 0.6
        cmap = cm.get_cmap(cmap_string)

        fig = plt.figure()
        img = plt.imshow(limits, cmap=cmap)
        plt.gca().set_visible(False)
        cax = plt.axes([LEFT, BOTTOM, WIDTH, HEIGHT])
        plt.colorbar(orientation="vertical", cax=cax)

        canvas = fig.canvas
        can_dims = canvas.get_width_height()
        plt.savefig("photos/colorbar.png", transparent=True)
        plt.close()

        offset = (int(can_dims[0] * LEFT) - 10, int(can_dims[1] * BOTTOM) - 30)
        bar_dims = (int(can_dims[0] * WIDTH) * 2.2, int(can_dims[1] * HEIGHT))

        img = Image.open("photos/colorbar.png")
        img = img.crop((offset[0], offset[1], offset[0] + bar_dims[0], offset[1] + bar_dims[1] + 40))
        return img
