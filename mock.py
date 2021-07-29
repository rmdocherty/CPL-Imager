#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 13:10:19 2021

@author: ronan
"""

# DEPENDENCIES
import numpy as np
from colourmapper import ColourMapper
from live_view import LiveViewCanvas
import queue
import tkinter as tk
import threading

# Seed RNG
np.random.seed(1)

# %%


class MockCamera(threading.Thread):
    """
    MockCamera.

    Fake class designed to emulate action of the ImageAcquistionThread in
    live_view.py. Generates random array of fixed width and throws it onto a 
    queue to be grabbed ad decoded by LiveViewCanvas.
    """

    def __init__(self, on=True):
        super(MockCamera, self).__init__()
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._on = on

    def get_output_queue(self):
        # type: (type(None)) -> queue.Queue
        return self._image_queue

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            try:
                if self._on is True:
                    LCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))
                    #pil_image = self._cmapper.colour_map(LCPL, None)
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


# %% Static test of colour mapper ability
c = ColourMapper("test")

np.random.seed(1)

IMG_WIDTH = 200
IMG_HEIGHT = 200

LCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))
RCPL = np.random.random((IMG_HEIGHT, IMG_WIDTH))

c = ColourMapper("Raw")
c.colour_map(LCPL, RCPL, debug=False)

# %%
root = tk.Tk()
root.title("Mock CPL")
camera1 = MockCamera()
camera2 = MockCamera()
camera_widget = LiveViewCanvas(parent=root, iq1=camera1.get_output_queue(),
                               iq2=camera2.get_output_queue(), mode="DOCP")
camera1.start()
camera2.start()

print("App starting")
root.mainloop()

print("Waiting for image acquisition thread to finish...")
camera1.stop()
camera1.join()
camera2.stop()
camera2.join()    
