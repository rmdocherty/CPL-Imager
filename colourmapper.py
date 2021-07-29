#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 11:35:13 2021

@author: ronan
"""

from matplotlib import cm
from PIL import Image


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
            for l in lines:
                param_list = l.split(":")
                temp_mode = param_list[0]
                # remove extra spaces and newlines
                temp_cmap = param_list[1].strip(" ").strip("\n")
                if temp_mode == "Raw": #will need 2 here
                    temp_cmap = temp_cmap.split(",") # assume comma separated
                cmap_dict[temp_mode] = temp_cmap
        return cmap_dict

    def colour_map(self, img1, img2, mode):
        """
        colour_map.

        Given the two images from the camera and the mode, perform the mapping
        process. If in Raw mode, cmap both images separately and return tuple
        of images. If in g_em mode, combine both arrays using g_em formula
        before cmapping and returning single image. If in DOCP mode, calc. the
        DOCP by adding magnitudes then cmap and return single image.

        Parameters
        ----------
        img1 : NP ARRAY
            LCPL image from camera 1. Don't know dtype, may need to rescale
            before cmapping
        img2 : NP ARRAY
            Same as img1 but RCPL from camera 2
        mode : STR
            String that determines which mode the cmapper works in. Determined
            by control thread.

        Returns
        -------
        Either:
            1) In raw mode, a TUPLE of PIL IMAGES
            2) A single PIL IMAGE

        """
        if mode == "Raw":
            cmap1, cmap2 = self._cmaps["Raw"] # unpack
            cmapped_img1 = self._single_cmap(img1, cmap1)
            cmapped_img2 = self._single_cmap(img2, cmap2)
            out = [cmapped_img1, cmapped_img2]
        elif mode == "g_em":
            cmap = self._cmaps["g_em"]
            g_em = 2 * (img1 - img2) / (img1 + img2)
            out = self._single_cmap(g_em, cmap)
        elif mode == "DOCP":
            cmap = self._cmaps["DOCP"]
            DOCP = (img1 + img2)
            out = self._single_cmap(DOCP, cmap)
        else:
            raise Exception("Invalid mode supplied, check cmap_config file")
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
        cmap = cm.get_cmap(cmap_string) # grab cmap object from string
        out_im = Image.fromarray(cmap(img, bytes=True)) # bytes=True converts array into uint8 for fromarray to use
        return out_im



c = ColourMapper("test")
