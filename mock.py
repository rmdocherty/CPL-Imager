#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 13:10:19 2021

@author: ronan
"""

# DEPENDENCIES
import numpy as np
from live_view import LiveViewCanvas
import queue
import tkinter as tk
import threading

# Seed RNG
np.random.seed(1)
IMG_HEIGHT = 300
IMG_WIDTH = 300
# %%


class MockCamera(threading.Thread):
    """
    MockCamera.

    Fake class designed to emulate action of the ImageAcquistionThread in
    live_view.py. Generates random array of fixed width and throws it onto a
    queue to be grabbed and decoded by LiveViewCanvas.
    """

    def __init__(self, on=True):
        super(MockCamera, self).__init__()
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._on = on

    def get_output_queue(self):
        """Getter method for output queue."""
        # type: (type(None)) -> queue.Queue
        return self._image_queue

    def stop(self):
        """Thread stopping fn."""
        self._stop_event.set()

    def run(self):
        """If on throw random np array into queue, if off throw None into queue."""
        while not self._stop_event.is_set():
            try:
                if self._on is True:
                    LCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))
                    self._image_queue.put_nowait(LCPL)
                else:
                    self._image_queue.put_nowait(None)
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")


# %%

# TKinter button functions - relies on camera_widget being a global variable which is icky
def switch_to_raw():
    camera_widget.set_cmap_mode("Raw")
def switch_to_DOCP():
    camera_widget.set_cmap_mode("DOCP")
def switch_to_g_em():
    camera_widget.set_cmap_mode("g_em")
def take_photo():
    camera_widget.take_photo()


# %%
root = tk.Tk()
root.title("Mock CPL")

# TKinter GUI stuff, shouldn't need anything more complicated
# .grid() aligns the components to LHS of canvas
photo = tk.Button(text="Take Photo", command=take_photo).grid(column=0, row=0, ipadx=8, ipady=8, padx=8, pady=8)
label = tk.Label(text="Modes:").grid(column=0, row=1, ipadx=8, ipady=8, padx=8, pady=8)

raw_btn = tk.Button(text="Raw", command=switch_to_raw).grid(column=0, row=2, ipadx=8, ipady=8, padx=8, pady=8)
DOCP_btn = tk.Button(text="DOCP", command=switch_to_DOCP).grid(column=0, row=3, ipadx=8, ipady=8, padx=8, pady=8)
g_em_btn = tk.Button(text="g_em", command=switch_to_g_em).grid(column=0, row=4, ipadx=8, ipady=8, padx=8, pady=8)

camera1 = MockCamera()
camera2 = MockCamera()
camera_widget = LiveViewCanvas(parent=root, iq1=camera1.get_output_queue(),
                               iq2=camera2.get_output_queue(), mode="Raw")
camera1.start()
camera2.start()

print("App starting")
root.mainloop()

print("Waiting for image acquisition thread to finish...")
camera1.stop()
camera1.join()
camera2.stop()
camera2.join()
