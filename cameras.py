#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 12:14:46 2021

@author: ronan
"""
from thorlabs_tsi_sdk.tl_camera import TLCamera, Frame
from PIL import Image
from rotator import Rotator
import threading
try:
    #  For Python 2.7 queue is named Queue
    import Queue as queue
except ImportError:
    import queue
import numpy as np
from time import sleep
np.random.seed(1)
IMG_HEIGHT = 300 # can go at least as high as 1000x1000 - don't know what upper limit is!
IMG_WIDTH = 300


class ImageAcquisitionThread(threading.Thread):
    """
    ImageAcquisitionThread.

    This class derives from threading. Thread and is given a TLCamera instance during initialization. When started, the
    thread continuously acquires frames from the camera and converts them to PIL Image objects. These are placed in a
    queue.Queue object that can be retrieved using get_output_queue(). The thread doesn't do any arming or triggering,
    so users will still need to setup and control the camera from a different thread. Be sure to call stop() when it is
    time for the thread to stop.
    """

    def __init__(self, camera):
        # type: (TLCamera) -> ImageAcquisitionThread
        super().__init__() #pdon't include class inside super as this breaks inheritance for child classes!
        self._camera = camera
        self._previous_timestamp = 0

        self._bit_depth = camera.bit_depth
        self._camera.image_poll_timeout_ms = 0  # Do not want to block for long periods of time
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()

    def get_output_queue(self):
        """Getter for the queue object."""
        # type: (type(None)) -> queue.Queue
        return self._image_queue

    def stop(self):
        """Stop thread object."""
        self._stop_event.set()

    def _get_image(self, frame):
        # type: (Frame) -> Image
        # no coloring, just scale down image to 8 bpp and place into PIL Image object
        # maybe this is where to throw the color mapping - i.e operate on frame.image_buffer then pass as PIL image
        # bit shift by self._bit_depth -8 to right i.e divides image_buffer by 2** (bit_depth - 8)
        scaled_image = frame.image_buffer >> (self._bit_depth - 8)
        return scaled_image / 255  #rescaled from 0 - 1 for colourmap

    def run(self):
        """
        Run.

        While thread is running grab frames from camera, create a PIL image from them
        and put them onto the queue.
        """
        while not self._stop_event.is_set():
            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    pil_image = self._get_image(frame)
                    self._image_queue.put_nowait(pil_image)
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

    def __init__(self, camera):
        # type: (TLCamera) -> ImageAcquisitionThread
        super().__init__(camera)
        self._imaging_LCPl = True
        self._image_queue = queue.Queue(maxsize=1)
        self._image_queue_2 = queue.Queue(maxsize=1)
        self._rotator = Rotator("/dev/ttyUSB0")

    def get_output_queue_2(self):
        """Getter for the queue object."""
        # type: (type(None)) -> queue.Queue
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
            #self._rotator.jog_forward()
            if self._imaging_LCPl is True:
                self._rotate_mount(58) #motor is horizontal by default and offset by a few degrees. Also 45 -> 90 for some reason so 52 is approx. vertical
            else:
                self._rotate_mount(9) # approx horizontal due to offset

            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    pil_image = self._get_image(frame)
                    if self._imaging_LCPl is True:
                        iq = self._image_queue
                        iq.put_nowait(pil_image)
                    else:
                        iq = self._image_queue_2
                        iq.put_nowait(pil_image)
                    self._imaging_LCPl = not self._imaging_LCPl #toggle bool
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
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


class MockCamera(threading.Thread):
    """
    MockCamera.

    Fake class designed to emulate action of the ImageAcquistionThread in
    live_view.py. Generates random array of fixed width and throws it onto a
    queue to be grabbed and decoded by LiveViewCanvas.
    """

    def __init__(self, on=True):
        super().__init__()
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


class MockCompact(MockCamera):
    """Mock version of CompactIAT."""

    def __init__(self, on=True):
        super().__init__()
        self._image_queue_2 = queue.Queue(maxsize=2)
        self._on = on
        self._imaging_LCPl = True

    def get_output_queue_2(self):
        """Getter for the queue object."""
        # type: (type(None)) -> queue.Queue
        return self._image_queue_2

    def _rotate_mount(self, degrees):
        sleep(0.02) #simulate rotating camera - in actual fn. will need to check rotation done before returning

    def run(self):
        """Same as CompactIAT but generates random data rather than taking images."""
        while not self._stop_event.is_set():
            self._rotate_mount(90)
            try:
                pil_image = np.random.random((IMG_HEIGHT, IMG_WIDTH))
                if self._imaging_LCPl is True:
                    iq = self._image_queue
                else:
                    iq = self._image_queue_2
                iq.put_nowait(pil_image)
                self._imaging_LCPl = not self._imaging_LCPl #toggle bool
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")
