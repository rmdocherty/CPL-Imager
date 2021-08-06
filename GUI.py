#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 11:52:28 2021

@author: ronan
"""
import tkinter as tk
from colourmapper import ColourMapper
from PIL import ImageTk
try:
    #  For Python 2.7 queue is named Queue
    import Queue as queue
except ImportError:
    import queue
from datetime import datetime


class CPL_Viewer(tk.Frame):
    """
    CPL_Viewer.

    GUI object for the viewer, basically a menu of buttons on the left hand
    side of the liveCanvas. Before creating any widgets it needs a camera_widget
    ( == a liveCanvas) that it can bind functions to. This is because all the
    buttons are are wrappers for the liveCanvas functions anway. Widgets laid
    out according to grid system as this produces nicest results.
    """

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

    def set_camera_widget(self, camera_widget_object):
        self._camera_widget = camera_widget_object
        self._createWidgets()

    def _switch_to_raw(self):
        self._camera_widget.set_cmap_mode("Raw")

    def _switch_to_DOCP(self):

        self._camera_widget.set_cmap_mode("DOCP")

    def _switch_to_g_em(self):
        self._camera_widget.set_cmap_mode("g_em")

    def _take_photo(self):
        self._camera_widget.take_photo()

    def _createWidgets(self):
        photo = tk.Button(text="Take Photo", command=self._take_photo).grid(column=0, row=0, ipadx=8, ipady=8, padx=8, pady=8)
        label = tk.Label(text="Modes:").grid(column=0, row=1, ipadx=8, ipady=8, padx=8, pady=8)
        
        raw_btn = tk.Button(text="Raw", command=self._switch_to_raw).grid(column=0, row=2, ipadx=8, ipady=8, padx=8, pady=8)
        DOCP_btn = tk.Button(text="DOCP", command=self._switch_to_DOCP).grid(column=0, row=3, ipadx=8, ipady=8, padx=8, pady=8)
        g_em_btn = tk.Button(text="g_em", command=self._switch_to_g_em).grid(column=0, row=4, ipadx=8, ipady=8, padx=8, pady=8)


class LiveViewCanvas(tk.Canvas):
    """LiveViewCanvas.

    This is a Tkinter Canvas object that can be reused in custom programs. The Canvas expects a parent Tkinter object and
    an image queue. The image queue is a queue.Queue that it will pull images from, and is expected to hold PIL Image
    objects that will be displayed to the canvas. It automatically adjusts its size based on the incoming image dimensions.
    Has been modified from default, now expects and grabs from two image queues
    desgined to relfect the two-camera nature of project. The grabbed images are
    then fed into the ColourMapping object which performs the right mapping given
    the mode and spits out a PIL image to be thrown onto the canvas.
    """

    def __init__(self, parent, iq1, iq2, mode="Raw"):
        self.image_queue1 = iq1
        self.image_queue2 = iq2
        self._image_width = 0
        self._image_height = 0
        tk.Canvas.__init__(self, parent)
        # need the columnspan and row span to make alignment nice
        self.grid(column=1, row=0, columnspan=5, rowspan=5)
        self._cmap = ColourMapper(mode)
        self._img_data = [] # need variable to store image in as can't seem to save directly from a ImageTk.PhotoImage Object
        self._get_image()

    def set_cmap_mode(self, mode):
        """Setter for the Cmap mode."""
        self._cmap.set_mode(mode)

    def _get_image(self):
        try:
            image1 = self.image_queue1.get_nowait()
            image2 = self.image_queue2.get_nowait()
            unrotated_img = self._cmap.colour_map(image1, image2)
            self._img_data = unrotated_img.rotate(270) #image right way up
            self._image = ImageTk.PhotoImage(master=self, image=self._img_data)
            if (self._image.width() != self._image_width) or (self._image.height() != self._image_height):
                # resize the canvas to match the new image size
                self._image_width = self._image.width() / 1.25
                self._image_height = self._image.height() / 1.25  #remove this scaling later!
                self.config(width=self._image_width, height=self._image_height)
            self.create_image(0, 0, image=self._image, anchor='nw')
        except queue.Empty:
            pass
        self.after(10, self._get_image)

    def take_photo(self):
        """Take snapshot of current image by using the _img_data image."""
        timestamp = datetime.now()
        timestamp_string = timestamp.strftime("%d-%m-%y_%H:%M:%S_%f")
        self._img_data.save("photos/" + timestamp_string, format="bmp")
