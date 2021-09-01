#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 11:52:28 2021

@author: ronan
"""
import tkinter as tk
from colourmapper import ColourMapper
from helper import clearQueue
from PIL import ImageTk
import numpy as np
try:
    #  For Python 2.7 queue is named Queue
    import Queue as queue
except ImportError:
    import queue
from datetime import datetime
from time import sleep


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
        self._live = True

    def set_camera_widget(self, camera_widget_object):
        self._camera_widget = camera_widget_object
        self._createWidgets()

    def set_control_queue(self, cq):
        self._CQ = cq

    def _switch_to_raw(self):
        self._camera_widget.set_cmap_mode("Raw")

    def _switch_to_DOCP(self):
        self._camera_widget.set_cmap_mode("DOCP")

    def _switch_to_g_em(self):
        self._camera_widget.set_cmap_mode("g_em")

    def _take_photo(self):
        if self._live is False:
            clearQueue(self._CQ)
            print("Taking static photo")
            self._CQ.put_nowait("Photo")#put("Photo", block=True, timeout=0.)
            self._camera_widget._get_image()
            #self._CQ.put_nowait("Off")
        self._camera_widget.take_photo()
        
    def _toggle_live(self):
        clearQueue(self._CQ)
        if self._live is True:
            self._live = False
            print("Live view off")
            self._CQ.put_nowait("Off")##put("Off", block=True, timeout=0.01)
        else:
            self._live = True
            print("Live view on")
            self._CQ.put_nowait("Live")##put("Live", block=True, timeout=0.01)

    def _cmap_window(self):
        self._cmap_menu = tk.Toplevel()
        self._cmap_menu.title("Colour map selector")
        LCPL = tk.Text(self._cmap_menu, height=2, width=30)
        LCPL_text = tk.Label(self._cmap_menu, text="LCPL:")
        RCPL = tk.Text(self._cmap_menu, height=2, width=30)
        RCPL_text = tk.Label(self._cmap_menu, text="RCPL:")
        DOCP = tk.Text(self._cmap_menu, height=2, width=30)
        DOCPL_text = tk.Label(self._cmap_menu, text="DOCP:")
        g_em = tk.Text(self._cmap_menu, height=2, width=30)
        g_em_text = tk.Label(self._cmap_menu, text="g_em:")

        self._cmap_menu_fields = [LCPL, RCPL, DOCP, g_em]

        set_cmaps = tk.Button(self._cmap_menu, text="Done", command=self._submit_cmaps)
        for i, lbl in enumerate([LCPL_text, RCPL_text, DOCPL_text, g_em_text]):
            lbl.grid(column=0, row=i)
        for i, txt in enumerate([LCPL, RCPL, DOCP, g_em]):
            txt.grid(column=1, row=i)
        set_cmaps.grid(column=0, row=4, columnspan=2)

    def _submit_cmaps(self):
        cmap_list = []
        for txt_field in self._cmap_menu_fields:
            text = txt_field.get("1.0", "end-1c")
            print(text)
            cmap_list.append(text)
        try:
            self._camera_widget.set_cmaps(cmap_list)
        except Exception:
            print("Invalid cmaps supplied, check you've entered correctly!")
        self._cmap_menu.destroy()

    def _calibrate_window(self):
        self._calibrate_menu = tk.Toplevel()
        self._calibrate_menu.title("Calibration")

        LCPL_uniform = tk.Text(self._calibrate_menu, height=2, width=30)
        LCPL_uniform.grid(column=1, row=0)
        LCPL_text = tk.Label(self._calibrate_menu, text="LCPL in RPS:").grid(column=0, row=0)
        RCPL_uniform = tk.Text(self._calibrate_menu, height=2, width=30)
        RCPL_uniform.grid(column=1, row=1)
        RCPL_text = tk.Label(self._calibrate_menu, text="RCPL in RPS:").grid(column=0, row=1)
        correction_map = tk.Button(self._calibrate_menu, text="Generate correction", command=self._gen_correction).grid(column=0, row=2, columnspan=2)

        finish_calibrate = tk.Button(self._calibrate_menu, text="Finish", command=self._finish_calibrate).grid(column=0, row=3, columnspan=2)
        self._calibrate_menu_text_fields = [LCPL_uniform, RCPL_uniform]
    
    def _gen_correction(self):
        data = self._camera_widget._np_array
        LCPL_btn = self._calibrate_menu_text_fields[0]
        RCPL_btn = self._calibrate_menu_text_fields[1]
        zero_thresh = 0.2
        try:
            ref_LCPL_intensity = float(LCPL_btn.get("1.0", "end-1c"))
            ref_RCPL_intensity = float(RCPL_btn.get("1.0", "end-1c"))
        except (ValueError, AttributeError): #assume a 50/50 split state (45 deg)
            ref_LCPL_intensity = 0.5
            ref_RCPL_intensity = 0.5
        half_index = data.shape[1] // 2
        LCPL_data = data[:, :half_index]
        RCPL_data = data[:, half_index:]
        LCPL_mask = np.where(LCPL_data > zero_thresh, ref_LCPL_intensity / LCPL_data, 0)
        RCPL_mask = np.where(RCPL_data > zero_thresh, ref_RCPL_intensity / RCPL_data, 0)
        self._camera_widget.set_masks(LCPL_mask, RCPL_mask)

    def _finish_calibrate(self):
        self._calibrate_menu.destroy()

    def _createWidgets(self):
        photo = tk.Button(text="Take Photo", command=self._take_photo)
        live = tk.Button(text="Toggle Video", command=self._toggle_live)
        calibrate = tk.Button(text="Calibrate", command=self._calibrate_window)
        cmap_btn = tk.Button(text="Set Cmaps", command=self._cmap_window)
        label = tk.Label(text="Modes:")

        raw_btn = tk.Button(text="Raw", command=self._switch_to_raw)
        DOCP_btn = tk.Button(text="DOCP", command=self._switch_to_DOCP)
        g_em_btn = tk.Button(text="g_em", command=self._switch_to_g_em)
        btns = [photo, live, calibrate, cmap_btn, label, raw_btn, DOCP_btn, g_em_btn]
        pad = 1
        for index, b in enumerate(btns):
            b.grid(column=0, row=index, ipadx=pad, ipady=pad, padx=pad, pady=pad)


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

        self._cmap = ColourMapper(mode)
        self._img_data = [] # need variable to store image in as can't seem to save directly from a ImageTk.PhotoImage Object

        self._LCPL_mask = np.array([1])
        self._RCPL_mask = np.array([1])

        self._mode = "Raw"
        self._sizes = {"Raw": (360, 180), "DOCP": (180, 180), "g_em": (180, 180)}

        tk.Canvas.__init__(self, parent)
        #sleep(1)
        # need the columnspan and row span to make alignment nice
        self.grid(column=1, row=0, columnspan=5, rowspan=5)
        self._get_image()

    def set_masks(self, LCPL, RCPL):
        self._LCPL_mask = LCPL
        self._RCPL_mask = RCPL

    def set_cmap_mode(self, mode):
        """Setter for the Cmap mode."""
        self._mode = mode
        self._cmap.set_mode(mode)

    def set_cmaps(self, cmap_list):
        self._cmap.set_cmaps(cmap_list)

    def _get_image(self):
        iq1 = self.image_queue1
        iq2 = self.image_queue2
        #print(f"L queue size: {iq1.qsize()} & R queue size: {iq2.qsize()}")
        try:
            image1 = iq1.get_nowait()
            image2 = iq2.get_nowait()
            image1 = image1 * self._LCPL_mask
            image2 = image2 * self._RCPL_mask
            self._np_array = np.hstack((image1, image2))
            unrotated_img = self._cmap.colour_map(image1, image2)
            self._img_data = unrotated_img
            resized = unrotated_img.resize(self._sizes[self._mode]) #(w, h)
            #self._img_data = unrotated_img.rotate(270) #image right way up - but it does end up stacking vertically rather than horizontally for 2 img setups
            self._image = ImageTk.PhotoImage(master=self, image=resized) # self._img_data
            if (self._image.width() != self._image_width) or (self._image.height() != self._image_height):
                # resize the canvas to match the new image size
                self._image_width = self._image.width()
                self._image_height = self._image.height()  #remove this scaling later!
                self.config(width=self._image_width, height=self._image_height)
            self.create_image(0, 0, image=self._image, anchor='nw')
        except queue.Empty:
            pass
        self.after(20, self._get_image)

    def take_photo(self):
        """Take snapshot of current image by using the _img_data image."""
        timestamp = datetime.now()
        timestamp_string = timestamp.strftime("%d-%m-%y_%H:%M:%S_%f")
        self._img_data.save("photos/" + timestamp_string, format="bmp")
        np.save("photos/" + timestamp_string + ".bmp", self._np_array)
