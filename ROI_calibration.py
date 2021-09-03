#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 26 14:36:18 2021

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

DEFAULT_THRESHOLD = 0.05 #percent



class LiveViewCanvas(tk.Canvas):

    def __init__(self, parent, image_queue, intensity_threshold=DEFAULT_THRESHOLD):
        self.image_queue = image_queue
        self._image_width = 0
        self._image_height = 0
        self._intensity = intensity_threshold
        self._img_data = None
        self._ROI = []
        self._align = "Horizontal"
        #self._r = rotator.Rotator("/dev/ttyUSB0")

        tk.Canvas.__init__(self, parent)
        self.bind("<Button-1>", self._onclick)
        self.bind_all("<space>", self._rotate) #need to bind_all so whole application listens for keypress
        self.pack()
        self._get_image()

    def _get_image(self):
        try:
            image = self.image_queue.get_nowait()
            self._img_data = image
            pil_image = Image.fromarray(image * 255)
            self._image = ImageTk.PhotoImage(master=self, image=pil_image)
            if (self._image.width() != self._image_width) or (self._image.height() != self._image_height):
                # resize the canvas to match the new image size
                self._image_width = self._image.width()
                self._image_height = self._image.height()
                self.config(width=self._image_width, height=self._image_height)
            self.create_image(0, 0, image=self._image, anchor='nw')
        except queue.Empty:
            pass
        self._draw_crosses(self._ROI)
        if type(self._img_data) == np.ndarray:
            self._draw_saturation_message(self._intensity)
        self._draw_angle()
        self.after(10, self._get_image)

    def _rotate(self, event):
        print(f"Align is {self._align}")
        if self._align == "Horizontal":
            self._r.rotate_to_angle(rotator.VERTICAL)
            self._align = "Vertical"
        elif self._align == "Vertical":
            self._r.rotate_to_angle(rotator.HORIZONTAL)
            self._align = "Horizontal"
        else:
            pass
    
    def _draw_angle(self):
        message = f"{self._align}ly aligned, press space to rotate."
        self.create_text(10, 1000, anchor=tk.W, font="Arial", text=message, fill="Orange")

    def _onclick(self, event):
        if len(self._ROI) == 2:
            self._ROI = []
        self._ROI.append((event.x, event.y))
        print(f"clicked at {event.x}, {event.y}")

    def _draw_crosses(self, points):
        for c in points:
            self.create_text(c[0], c[1], anchor=tk.W, font="Arial", text="X", fill="Orange")

    def _check_intensity(self):
        data = self._img_data
        non_zero = np.where(data > 0.08)[0] #region where intensity isn't zero
        saturated = np.where(data >= 1)[0] #regions where pixel value is 1
        data_length = data.shape[0] * data.shape[1]
        try:
            saturation_percent = 100 * len(saturated) / len(non_zero)
        except ZeroDivisionError:
            saturation_percent = 0
        return saturation_percent

    def _draw_saturation_message(self, threshold):
        try:
            threshold_percent = float(threshold)
        except (ValueError, AttributeError):
            threshold_percent = DEFAULT_THRESHOLD
        saturation = self._check_intensity()
        if saturation < threshold_percent:
            message = f"Saturation is {saturation:.4f}"
            color = "Green"
        else:
            message = f"Saturation is {saturation:.4f} and over threshold"
            color = "Red"
        self.create_text(10, 10, anchor=tk.W, fill=color, font="Arial", text=message)


class ImageAcquisitionThread(threading.Thread):

    def __init__(self, camera):
        # type: (TLCamera) -> ImageAcquisitionThread
        super(ImageAcquisitionThread, self).__init__()
        self._camera = camera
        self._camera.roi = (0, 0, 1024, 1024)#(660, 572, 750, 660) are good values?
        self._previous_timestamp = 0

        self._bit_depth = camera.bit_depth
        self._camera.image_poll_timeout_ms = 0  # Do not want to block for long periods of time
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()

    def get_output_queue(self):
        # type: (type(None)) -> queue.Queue
        return self._image_queue

    def stop(self):
        self._stop_event.set()

    def _get_image(self, frame):
        scaled_image = frame.image_buffer >> (self._bit_depth - 8)
        return scaled_image / 255 #Image.fromarray(scaled_image)

    def run(self):
        while not self._stop_event.is_set():
            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    np_image = self._get_image(frame)
                    self._image_queue.put_nowait(np_image)
            except queue.Full:
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")


labels = {0: "left", 1: "right"}



if __name__ == "__main__":
    sat = float(input("What threshold saturation do you want?"))
    cam = int(input("Open camera 0 or 1?"))
    with TLCameraSDK() as sdk:
        camera_list = sdk.discover_available_cameras()
        with sdk.open_camera(camera_list[cam]) as camera:
            root = tk.Tk()
            root.title("ROI calibration")
            image_acquisition_thread = ImageAcquisitionThread(camera)
            camera_widget = LiveViewCanvas(parent=root, image_queue=image_acquisition_thread.get_output_queue(), intensity_threshold=sat)

            camera.frames_per_trigger_zero_for_unlimited = 0
            camera.arm(2)
            camera.issue_software_trigger()
            
            image_acquisition_thread.start()

            root.mainloop()

            image_acquisition_thread.stop()
            image_acquisition_thread.join()

    ROI_list = camera_widget._ROI
    if len(ROI_list) == 2:
        ROI_tuple = (ROI_list[0][0], ROI_list[0][1], ROI_list[1][0], ROI_list[1][1])
        parsed = [str(i) for i in ROI_tuple]
        print(f"ROI is {parsed}")
        confirm = input("Is ROI acceptable (y/n)?")
        if confirm.lower() in ["y", "yes", "1"]:
            with open(f"roi_config_{labels[cam]}.txt", "w") as f:
                for p in parsed:
                    f.write(f"{p}\n")
            print("Written new ROI to file!")
    else:
        print("ROI not enough points, need 2!")
