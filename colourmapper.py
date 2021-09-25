#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 11:35:13 2021

@author: ronan
"""

from matplotlib import cm
from PIL import Image
import numpy as np # maybe can just import hstack by itself later
import matplotlib.pyplot as plt

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
        cmap_dict = {}
        with open("cmap_config.txt", "r") as configFile:
            lines = configFile.readlines()
            for line in lines:
                param_list = line.split(":")
                temp_mode = param_list[0]
                # remove extra spaces and newlines
                temp_cmap = param_list[1].strip(" ").strip("\n")
                if temp_mode == "Raw": #will need 2 here
                    temp_cmap = temp_cmap.split(",") #assume comma separated
                cmap_dict[temp_mode] = temp_cmap
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
        if self._mode == "Raw":
            cmap1, cmap2 = self._cmaps["Raw"]
            if img1 is not None and img2 is not None: #use this case 1st as most common!
                cmapped_img1 = self._single_cmap(img1, cmap1)
                cmapped_img2 = self._single_cmap(img2, cmap2)
                mapped = np.hstack((cmapped_img1, cmapped_img2)) #put images 'side-by-side' NB - will this work if diff sizes??
            elif img1 is not None and img2 is None: #single image modes
                mapped = self._single_cmap(img1, cmap1)
            elif img1 is None and img2 is not None:
                mapped = self._single_cmap(img2, cmap2)
            else:
                raise Exception("Must supply at least 1 image!")

        elif self._mode == "g_em":
            cmap = self._cmaps["g_em"]
            g_em = (img1 - img2) / (img1 + img2) #from equation, ignore factor of 2
            # g_em = g_em + 1
            g_em = (g_em + 1) / 2 #rescale from -1,+1 to 0,+1 for cmapping
            mapped = self._single_cmap(g_em, cmap)

        elif self._mode == "DOCP":
            cmap = self._cmaps["DOCP"]
            DOCP = (img1 + img2) / 2
            mapped = self._single_cmap(DOCP, cmap)

        else:
            raise Exception("Invalid mode supplied, check cmap_config file")

        out = Image.fromarray(mapped) #convert to PIL Image
        if debug is True:
            out.show() #see what's going on -get rid of later
        return out

    def _single_cmap(self, img, cmap_string):
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
        out_im = cmap(img, bytes=True) #bytes=True converts array into uint8 for fromarray to use
        return out_im

    def gen_colourbar(self):
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
        if self._mode == "Raw":
            cmap1, cmap2 = self._cmaps["Raw"]
            limits = np.array([[0, 1]])
            cbar1, cbar2 = self._single_colourbar(limits, cmap1), self._single_colourmap(limits, cmap2)
            out = Image.new('RGBA', (cbar1.width + cbar2.width, cbar1.height))
            out.paste(cbar1, (0, 0))
            out.paste(cbar2, (cbar1.width, 0))
        elif self._mode == "DOCP":
            cmap1 = self._cmaps["DOCP"]
            limits = np.array([[0, 1]])
            out = self._single_colourbar(limits, cmap1)
        elif self._mode == "g_em":
            cmap1 = self._cmaps["g_em"]
            limits = np.array([[-2, 2]])
            out = self._single_colourbar(limits, cmap1)
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
        WIDTH = 0.08
        HEIGHT = 0.6
        cmap = cm.get_cmap(cmap_string)

        fig = plt.figure()
        img = plt.imshow(limits, cmap=cmap)
        plt.gca().set_visible(False)
        cax = plt.axes([LEFT, BOTTOM, WIDTH, HEIGHT])
        plt.colorbar(orientation="vertical", cax=cax)

        canvas = fig.canvas
        can_dims = canvas.get_width_height()
        plt.savefig("colorbar.png", transparent=True)
        plt.close()

        offset = (int(can_dims[0] * LEFT) - 10, int(can_dims[1] * BOTTOM) - 30)
        bar_dims = (int(can_dims[0] * WIDTH) * 2.2, int(can_dims[1] * HEIGHT))

        img = Image.open("colorbar.png")
        img = img.crop((offset[0], offset[1], offset[0] + bar_dims[0], offset[1] + bar_dims[1] + 40))
        return img
