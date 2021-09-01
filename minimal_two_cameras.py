#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  1 13:30:17 2021

@author: ronan
"""

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, TLCamera, Frame
import rotator
try:
    #  For python 2.7 tkinter is named Tkinter
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import threading
try:
    #  For Python 2.7 queue is named Queue
    import Queue as queue
except ImportError:
    import queue


def setup_camera(camera):
    camera.image_poll_timeout_ms = 0
    camera.roi = (0, 0, 1024, 1024)
    camera.frames_per_trigger_zero_for_unlimited = 0
    camera.arm(2)
    camera.issue_software_trigger()


def wait_for_image(camera):
    frame = camera.get_pending_frame_or_null()
    if frame is not None:
        print("Success!")
        scaled_image = frame.image_buffer >> (camera.bit_depth - 8)
        normalised_img = scaled_image
    else:
        normalised_img = None
    return normalised_img


img1 = None
img2 = None
done = False

root = tk.Tk()

with TLCameraSDK() as sdk:
    camera_list = sdk.discover_available_cameras()
    print(camera_list)
    with sdk.open_camera(camera_list[0]) as cam1, sdk.open_camera(camera_list[1]) as cam2:
        setup_camera(cam1)
        setup_camera(cam2)
        while done is False:
            latest_img1 = wait_for_image(cam1)
            latest_img2 = wait_for_image(cam2)
            if latest_img1 is not None:
                img1 = latest_img1
            if latest_img2 is not None:
                img2 = latest_img2
            
            if img1 is not None and img2 is not None:
                pil_1 = Image.fromarray(img1)
                pil_2 = Image.fromarray(img2)
                pil_1.show()
                pil_2.show()
                done = True