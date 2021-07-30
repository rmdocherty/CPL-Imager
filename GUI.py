#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 11:52:28 2021

@author: ronan
"""
import tkinter as tk

class CPL_Viewer(tk.Frame):
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
