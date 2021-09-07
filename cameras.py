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
from time import sleep

np.random.seed(1)
IMG_HEIGHT = 300 # can go at least as high as 1000x1000 - don't know what upper limit is!
IMG_WIDTH = 300


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
        self._camera.image_poll_timeout_ms = 0  # Do not want to block for long periods of time. was 0!!!
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._get_roi_from_file()

    def _get_roi_from_file(self):
        try:
            print(f"roi_config_{self._label}.txt")
            f = open(f"roi_config_{self._label}.txt")
            
            coords = [int(i.strip('\n')) for i in f.readlines()]
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
        self._rotator = rotator.Rotator("/dev/ttyUSB0")
        self._mode = "Live"
        self._control_queue = queue.Queue(maxsize=2)

    def get_output_queue_2(self):
        """Getter for the queue object."""
        return self._image_queue_2

    def _rotate_mount(self, degrees):
        self._rotator.rotate_to_angle(degrees)

    def run(self):
        """
        Run.

        Rotate camera & take image. Each time image is taken and put onto queue,
        switch which queue is being used.
        """
        while not self._stop_event.is_set():
            try:
                self._mode = self._control_queue.get_nowait()
            except queue.Empty:
                pass
            if self._mode == "Live":
                if self._imaging_LCPl is True:
                    self._rotate_mount(rotator.HORIZONTAL) #motor is horizontal by default and offset by a few degrees. Also 45 -> 90 for some reason so 52 is approx. vertical
                    iq = self._image_queue
                else:
                    self._rotate_mount(rotator.VERTICAL) # approx horizontal due to offset
                    iq = self._image_queue_2
                try:
                    frame = self._camera.get_pending_frame_or_null()
                    if frame is not None:
                        pil_image = self._get_image(frame)
                        iq.put_nowait(pil_image)
                        self._imaging_LCPl = not self._imaging_LCPl #toggle bool
                except queue.Full:
                    # No point in keeping this image around when the queue is full, let's skip to the next one
                    pass
                except Exception as error:
                    print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                    break
            elif self._mode == "Photo": #take single snapshot - delete this?
                iq1 = self._image_queue
                iq2 = self._image_queue_2

                #clearQueue(iq1)
                #clearQueue(iq2) clearing queue breaks image updating
         
                self._rotate_mount(rotator.HORIZONTAL)
                frame = None
                while frame is None:
                    frame = self._camera.get_pending_frame_or_null() #block till img
                pil_image = self._get_image(frame)
                iq1.put(pil_image, block=True, timeout=0.1)

                self._rotate_mount(rotator.VERTICAL)
                frame2 = None
                while frame2 is None:
                    frame2 = self._camera.get_pending_frame_or_null() #block till img
                pil_image2 = self._get_image(frame2)
                iq2.put(pil_image2, block=True, timeout=0.1)
                print("taken photo")

                self._control_queue.put("Off", block=True, timeout=0.01)

            else:
                pass
        print("Image acquisition has stopped")
        self._camera.disarm()
        self._camera.dispose()

    def stop(self):
        """Stop thread object."""
        self._stop_event.set()


class SingleCamera(CompactImageAcquisitionThread):

    def run(self):
        """
        Run.

        Rotate camera & take image. Each time image is taken and put onto queue,
        switch which queue is being used.
        """
        while not self._stop_event.is_set():
            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    pil_image = self._get_image(frame)
                    self._image_queue.put_nowait(pil_image)
                    self._image_queue_2.put_nowait(None)
            except queue.Full: #maybe this is problem
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")
        self._camera.disarm()
        self._camera.dispose()
