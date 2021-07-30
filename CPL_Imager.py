#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 10:51:34 2021

@author: ronan
"""

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from cameras import MockCamera, ImageAcquisitionThread
from GUI import CPL_Viewer, LiveViewCanvas
try:
    #  For python 2.7 tkinter is named Tkinter
    import Tkinter as tk
except ImportError:
    import tkinter as tk


class CPL_Imager():
    def __init__(self):
        self._root = tk.Tk()
        self._GUI = CPL_Viewer(master=self._root)
        self._root.title("CPL Imager")
        
    def _gen_image_acquisition_threads(self, cam1, cam2):
        return (ImageAcquisitionThread(cam1), ImageAcquisitionThread(cam2))

    def _gen_widget(self, image_queue1, image_queue2):
        camera_widget = LiveViewCanvas(parent=self._root, iq1=image_queue1,
                                       iq2=image_queue2, mode="Raw")
        return camera_widget

    def _start_camera(self, cam):
        cam.frames_per_trigger_zero_for_unlimited = 0
        cam.arm(2)
        cam.issue_software_trigger()

    def _start_cameras(self, cam1, cam2):
        self._start_camera(cam1)
        self._start_camera(cam2)

    def run(self):
        with TLCameraSDK() as sdk:
            camera_list = sdk.discover_available_cameras()
            with camera_list[0] as cam1, camera_list[1] as cam2:
                self._main_function(cam1, cam2)

    def _main_function(self, cam1, cam2):
        image_acquisition_thread_1, image_acquisition_thread_2 = self._gen_image_acquisition_threads(cam1, cam2)
        camera_widget = self._gen_widget(image_acquisition_thread_1.get_output_queue(),
                                         image_acquisition_thread_2.get_output_queue())
        self._GUI.set_camera_widget(camera_widget)
        self._start_cameras(cam1, cam2)
        image_acquisition_thread_1.start()
        image_acquisition_thread_2.start()

        print("App starting")
        self._root.mainloop()

        print("Waiting for image acquisition thread to finish...")
        image_acquisition_thread_1.stop()
        image_acquisition_thread_1.join()
        image_acquisition_thread_2.stop()
        image_acquisition_thread_2.join()

        print("Closing resources...")

class CPL_Imager_One_Camera(CPL_Imager):
    def _gen_image_acquisition_threads(self, cam1, cam2):
        return (ImageAcquisitionThread(cam1), cam2)

    def _gen_widget(self, image_queue1, image_queue2):
        if self._camera_handedness in ["l", "lcpl", "left"]:
            camera_widget = LiveViewCanvas(parent=self._root, iq1=image_queue1,
                                           iq2=image_queue2, mode="Raw")
        elif self._camera_handedness in ["r", "rcpl", "right"]: #swap image queues
            camera_widget = LiveViewCanvas(parent=self._root, iq1=image_queue2,
                                           iq2=image_queue1, mode="Raw")
        else:
            raise Exception("Please enter which camera is plugged in")
        return camera_widget

    def _start_camera(self, cam):
        cam.frames_per_trigger_zero_for_unlimited = 0
        cam.arm(2)
        cam.issue_software_trigger()

    def _start_cameras(self, cam1, cam2):
        self._start_camera(cam1)

    def run(self):
        self._camera_handedness = input("Which camera is plugged in - LCPL or RCPL?").lower()
        with TLCameraSDK() as sdk:
            camera_list = sdk.discover_available_cameras()
            with camera_list[0] as cam1:
                cam2 = MockCamera(off=True)
                self._main_function(cam1, cam2)

class CPL_Imager_No_Camera(CPL_Imager):
    def _gen_image_acquisition_threads(self, cam1, cam2):
        return (cam1, cam2)

    def _start_cameras(self, cam1, cam2):
        pass

    def run(self):
        cam1 = MockCamera()
        cam2 = MockCamera()
        self._main_function(cam1, cam2)


if __name__ == "__main__":
    imager = CPL_Imager_No_Camera()
    imager.run()
