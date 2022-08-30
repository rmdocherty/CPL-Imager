#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 12:14:46 2021

@author: ronan
"""
#from thorlabs_tsi_sdk.tl_camera import TLCamera, Frame
import rotator
#from helper import clearQueue
import threading

import queue
import numpy as np
from sys import platform
import json
from time import sleep
from skimage import draw
import random
from colourmapper import read_from_json
from time import sleep

np.random.seed(1)
IMG_HEIGHT = 360 # can go at least as high as 1000x1000 - don't know what upper limit is!
IMG_WIDTH = 360

def clearQueue(queue):
    while not queue.empty():
        queue.get()
    return 0

class ImageAcquisitionThread(threading.Thread):
    """
    ImageAcquisitionThread.

    This class derives from threading.Thread and is given a TLCamera instance during initialization. When started, the
    thread continuously acquires frames from the camera and converts them to 8 bit np array image. These are placed in a
    queue.Queue object that can be retrieved using get_output_queue(). The thread doesn't do any arming or triggering,
    so users will still need to setup and control the camera from a different thread. Be sure to call stop() when it is
    time for the thread to stop.
    """

    def __init__(self, camera, label="left"):
        super().__init__() #pdon't include class inside super as this breaks inheritance for child classes!
        self._camera = camera
        self._camera.roi = (0, 0, 1500, 1500)
        self._previous_timestamp = 0
        self._label = label

        self._bit_depth = camera.bit_depth
        self._camera.image_poll_timeout_ms = 10  # Do not want to block for long periods of time. was 0!!!
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._camera.exposure_time_us = 10100 #was 11000 
        self._get_roi_from_file()

    def _get_roi_from_file(self):
        """Grab corresponding (left or right) ROI config from the file, else
        use defaults."""
        try:
            """with open("config.json", "r") as config_file:
                config_json = json.load(config_file)
                coords = config_json["roi_"+self._label]"""
            coords = read_from_json("roi_"+self._label)
            ROI = (coords[0], coords[1], coords[2], coords[3])
            print(f"Setting ROI as {ROI}")
            self._camera.roi = ROI
        except (IOError, ValueError):
            print("Error generating ROI from file, falling back to default")
            pass

    def get_output_queue(self):
        """Getter for the queue object."""
        return self._image_queue

    def stop(self):
        """Stop thread object."""
        self._stop_event.set()

    def _get_image(self, frame):
        # no coloring, just scale down image to 8 bpp
        # bit shift by self._bit_depth -8 to right i.e divides image_buffer by 2** (bit_depth - 8)
        scaled_image = frame.image_buffer >> (self._bit_depth - 8)
        return scaled_image / 255  #rescaled from 0 - 1 for colourmap

    def run(self):
        """
        Run.

        While thread is running grab frames from camera, create a 8 bit image from them
        and put them onto the queue.
        """
        while not self._stop_event.is_set():
            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    np_image = self._get_image(frame)
                    self._image_queue.put_nowait(np_image)
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")
        self._camera.disarm()
        self._camera.dispose()


class CompactImageAcquisitionThread(ImageAcquisitionThread):
    """
    CompactImageAcquisitionThread.

    This class derives from IAT. Has 2 queues, one for each polarization.
    Does the same stuff as IAT but each time it takes a photo it rotates the
    piezo motor 90 degrees and swaps which queue to put the image into.
    """

    def __init__(self, camera, align=True):
        super().__init__(camera)
        self._imaging_LCPl = True
        self._image_queue = queue.Queue(maxsize=1)
        self._image_queue_2 = queue.Queue(maxsize=1)
        if platform == "linux" or platform == "linux2":
            port = "/dev/ttyUSB0"
        else:
            port = "COM3"
        self._rotator = rotator.Rotator(port) #was /dev/ttyUSB0
        self._mode = "Both"#"Live"
        self._control_queue = queue.Queue(maxsize=2)

    def get_output_queue_2(self):
        """Getter for the queue object."""
        return self._image_queue_2

    def _rotate_mount(self, degrees):
        self._rotator.rotate_to_angle(degrees)
    
    def change_cam_settings(self, ROI=None, exposure_time_us=None):
        self._camera.disarm()
        if ROI is not None:
            self._camera.roi = ROI
        if exposure_time_us is not None:
            self._camera.exposure_time_us = exposure_time_us()
        self._camera.frames_per_trigger_zero_for_unlimited = 0
        self._camera.arm(2)
        self._camera.issue_software_trigger()

    def get_camera_image_old(self, iq, toggle=True, iq2=None):
        try:
            frame = self._camera.get_pending_frame_or_null()
            if frame is not None:
                pil_image = self._get_image(frame)
                iq.put_nowait(pil_image)
                if toggle:
                    self._imaging_LCPl = not self._imaging_LCPl  # toggle bool
                if iq2 is not None:
                    null = np.zeros_like(pil_image)
                    iq2.put_nowait(null)
        except queue.Full:
            pass
        except Exception as error:
            print("Encountered error: {error}, image acquisition will stop.".format(error=error))
    
    def get_camera_image(self, iq, toggle=True, iq2=None, NUM_FRAMES=20):
        try:
            
            images = []
            for i in range(NUM_FRAMES):
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    pil_image = self._get_image(frame)
                    images.append(np.copy(pil_image))
            averaged = np.mean(images, axis=0)
            """
            frame = self._camera.get_pending_frame_or_null()
            if frame is not None:
                averaged = self._get_image(frame)
            """
            iq.put(averaged, block=True, timeout=0.05)#iq.put_nowait(averaged)
            if toggle:
                self._imaging_LCPl = not self._imaging_LCPl  # toggle bool
            if iq2 is not None:
                null = np.zeros_like(averaged)
                iq2.put_nowait(null)
        except queue.Full:
            pass
        except Exception as error:
            print("Encountered error: {error}, image acquisition will stop.".format(error=error))

    def run(self):
        """
        Run.

        Rotate camera & take image. Each time image is taken and put onto queue,
        switch which queue is being used.
        """
        jog_count = 0
        while not self._stop_event.is_set():
            try:
                self._mode = self._control_queue.get_nowait()
            except queue.Empty:
                pass
            if self._mode == "Both":
                if self._imaging_LCPl is True:
                    self._rotator.rotate_to_0()
                    iq = self._image_queue
                else:
                    self._rotator.rotate_to_90()
                    iq = self._image_queue_2
                self.get_camera_image(iq, toggle=True)
                """
                if jog_count == 4:
                    self._rotator._home_motor()
                    jog_count = 0
                else:
                    self._rotator.jog_forward()
                    jog_count += 1
                """
            elif self._mode == "LCPL" or self._mode == "RCPL":
                if self._mode == "LCPL":
                    self._rotator.rotate_to_0()
                    iq_main = self._image_queue
                    iq_null = self._image_queue_2
                else:
                    self._rotator.rotate_to_90()
                    iq_main = self._image_queue_2
                    iq_null = self._image_queue
                self.get_camera_image(iq_main, toggle=False, iq2=iq_null)
            elif self._mode == "Snap":
                self._rotator.rotate_to_0()
                iq, iq2 = self._image_queue, self._image_queue_2
                self.get_camera_image(iq, toggle=False, iq2=None)
                self._rotator.rotate_to_90()
                self.get_camera_image(iq2, toggle=False, iq2=None)
                #self._mode = "Pause" #reset mode
            elif self._mode[:3] == "ROI":
                roi_strs = self._mode[4:].split(',')
                ROI = [int(x) for x in roi_strs]
                clearQueue(self._image_queue)
                clearQueue(self._image_queue_2)
                self.change_cam_settings(ROI=ROI)
                self._mode = self._prev_mode
            elif self._mode == "Pause":
                pass
            else:
                pass
            self._prev_mode = self._mode
        print("Image acquisition has stopped")
        #self._rotator._home_motor()
        self._camera.disarm()
        self._camera.dispose()

    def stop(self):
        """Stop thread object."""
        self._stop_event.set()


def make_circle(arr, radius=120, val=0.5):
    x, y = arr.shape[0] // 2, arr.shape[1] // 2
    for i in range(x - radius // 2, x + radius // 2):
        for j in range(y - radius // 2, x + radius // 2):
            dist = np.sqrt((i-x)**2 + (j-y) ** 2)
            if dist <= radius:
                arr[y, x] = val #- 0.1 * np.exp(dist - radius) #decrease around edge
    return arr

def make_noise(arr, pos, radius=60, max_noise=0.2, repeats=50):
    for i in range(repeats):
        sign = random.choice([-1, 1])
        y, x = pos[1], pos[0]
        new_x = random.randint(x - radius, x + radius)
        new_y = random.randint(y - radius, y + radius)
        dist = np.sqrt((new_x - x)**2 + (new_x - y) ** 2)
        if dist > radius:
            pass
        else:
            value = sign * random.random() * max_noise
            rr, cc = draw.disk((new_x, new_y), 3)
            arr[rr, cc] += value
    return arr
    


class MockCamera(threading.Thread):
    """
    MockCamera.

    Fake class designed to emulate action of the ImageAcquistionThread in
    live_view.py. Generates random array of fixed width and throws it onto a
    queue to be grabbed and decoded by LiveViewCanvas.
    """

    def __init__(self, label="left"):
        super().__init__()
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._label = label
        self._control_queue = queue.Queue(maxsize=2)

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
                if self._label == "left":
                    val = 0.4
                    offset_x = 12
                    dx = 0.01
                else:
                    val = 1 #0.8 #have a +0.3 differential 
                    offset_x = 0
                    dx = 0.01
                LCPL = np.zeros((IMG_HEIGHT, IMG_WIDTH)) + dx
                rr, cc = draw.disk((IMG_HEIGHT // 2, offset_x + IMG_WIDTH // 2), 60)
                LCPL[rr, cc] = val
                if self._label == "right":
                    rr, cc = draw.disk((IMG_HEIGHT // 2, 20 + IMG_WIDTH // 2), 20)
                    LCPL[rr, cc] -= 0.2

                self._image_queue.put_nowait(LCPL)
                sleep(0.02)
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")

