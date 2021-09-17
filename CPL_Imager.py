#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 10:51:34 2021

@author: ronan
"""
#TODO: consider how it works on Windows by looking at Thorlabs examples
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from cameras import ImageAcquisitionThread, CompactImageAcquisitionThread, MockCamera
from GUI import CPL_Viewer, LiveViewCanvas
from time import sleep
try:
    #  For python 2.7 tkinter is named Tkinter
    import Tkinter as tk
except ImportError:
    import tkinter as tk


class CPL_Imager():
    """
    CPL_Imager.

    Parent class that encapsulates the general program logic of the imaging system.
    Creates a GUI from GUI.py, grabs two cameras using the SDK, creates a camera_widget
    which is the live view canvas and throws it onto the Tkinter app. Starts (i.e arms)
    the two cameras, then their respective image threads. Once the Tkinter app closes it
    then stops those threads.
    """

    def __init__(self):
        self._root = tk.Tk()
        self._GUI = CPL_Viewer(master=self._root)
        self._root.title("CPL Imager")

    def _gen_image_acquisition_threads(self, cam1, cam2):
        return ImageAcquisitionThread(cam1, label="left"), ImageAcquisitionThread(cam2, label="right")

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

    # def run(self):
    #     """Grab all available cameras and pass them into the main function."""
    #     with TLCameraSDK() as sdk:
    #         camera_list = sdk.discover_available_cameras()
    #         print(camera_list)
    #         with sdk.open_camera(camera_list[0]) as cam1, sdk.open_camera(camera_list[1]) as cam2:
    #             self._main_function(cam1, cam2)

    def run(self): #camera order should be 14358, 14071
        #with TLCameraSDK() as sdk:
        camera_list = sdk.discover_available_cameras()
        print(camera_list)
        with sdk.open_camera(camera_list[1]) as cam1:
            image_acquisition_thread_1 = ImageAcquisitionThread(cam1, label="left")
            self._start_camera(cam1)
            iq1 = image_acquisition_thread_1.get_output_queue()
            with sdk.open_camera(camera_list[0]) as cam2:
                image_acquisition_thread_2 = ImageAcquisitionThread(cam2, label="right")
                self._start_camera(cam2)
                
                iq2 = image_acquisition_thread_2.get_output_queue()
                camera_widget = self._gen_widget(iq1, iq2)
                self._GUI.set_camera_widget(camera_widget)
                image_acquisition_thread_1.start()
                image_acquisition_thread_2.start()
                
        
                print("Viewer starting")
                self._root.mainloop()
        
                image_acquisition_thread_1.stop()
                image_acquisition_thread_1.join()
                image_acquisition_thread_2.stop()
                image_acquisition_thread_2.join()
        return 0

    def _main_function(self, cam1, cam2):

        image_acquisition_thread_1, image_acquisition_thread_2  = self._gen_image_acquisition_threads(cam1, cam2)

        iq1 = image_acquisition_thread_1.get_output_queue()
        iq2 = image_acquisition_thread_2.get_output_queue()
        camera_widget = self._gen_widget(iq1, iq2)
        self._GUI.set_camera_widget(camera_widget)
        self._start_cameras(cam1, cam2)
        #self._GUI.set_control_queue("")
        image_acquisition_thread_1.start()
        image_acquisition_thread_2.start()
        

        print("Viewer starting")
        self._root.mainloop()

        image_acquisition_thread_1.stop()
        image_acquisition_thread_1.join()
        image_acquisition_thread_2.stop()
        image_acquisition_thread_2.join()

        print("Closing resources...")


class CPL_Imager_One_Camera(CPL_Imager):
    """
    CPL_Imager_One_Camera.

    A child class from CPL_Imager intended for use when only one camera is
    connected to the computer. First checks which 'handedness' of camera is
    attached i.e is it the LCPL or RCPL camera and switches the image queues
    accordingly (this is so it will be colourmapped correctly). The second
    camera is replaced by a MockCamera that constantly puts None into the
    queue, which will then be grabbed by the Canvas and processed correctly
    by ColourMapper.
    """

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
            print(camera_list)
            with sdk.open_camera(camera_list[0]) as cam1:
                self._main_function(cam1)

    def _main_function(self, cam):
        image_acquisition_thread = SingleCamera(cam)
        camera_widget = self._gen_widget(image_acquisition_thread.get_output_queue(),
                                         image_acquisition_thread.get_output_queue_2())
        self._GUI.set_camera_widget(camera_widget)
        #self._GUI.set_control_queue("")
        self._start_camera(cam)
        image_acquisition_thread.start()

        print("Viewer starting")
        self._root.mainloop()

        image_acquisition_thread.stop()
        image_acquisition_thread.join()
        print("Closing resources...")


class Compact_CPL_Imager(CPL_Imager_One_Camera):
    """
    Compact_CPL_Imager.

    For use in the compact optical design - i.e a single camera and a linear
    polarizer on a rotating mount. Takes image every 0.2 seconds in alteranting
    polarizations.
    """

    def run(self):
        """Grab all available cameras and pass them into the main function."""
        self._camera_handedness = "LCPL" #assumes it starts w/ LCPL
        with TLCameraSDK() as sdk:
            camera_list = sdk.discover_available_cameras()
            with sdk.open_camera(camera_list[0]) as cam:
                self._main_function(cam)

    def _gen_widget(self, image_queue1, image_queue2):
        camera_widget = LiveViewCanvas(parent=self._root, iq1=image_queue1,
                                       iq2=image_queue2, mode="Raw")
        return camera_widget

    def _gen_compactIAT(self, camera):
        return CompactImageAcquisitionThread(camera)

    def _main_function(self, cam):
        image_acquisition_thread = self._gen_compactIAT(cam)
        camera_widget = self._gen_widget(image_acquisition_thread.get_output_queue(),
                                         image_acquisition_thread.get_output_queue_2())
        self._GUI.set_camera_widget(camera_widget)
        self._GUI.set_control_queue(image_acquisition_thread._control_queue)
        self._start_camera(cam)
        image_acquisition_thread.start()

        print("Viewer starting")
        self._root.mainloop()

        image_acquisition_thread.stop()
        image_acquisition_thread.join()
        print("Closing resources...")


class CPL_Imager_No_Camera(CPL_Imager):
    """
    CPL_Imager_No_Camera.

    Another child class of CPL_Imager, designed for use with no cameras i.e as
    a demo. Reallt just an extension of the ideas of One_Camera.
    """

    def _gen_image_acquisition_threads(self, cam1, cam2):
        return (cam1, cam2)

    def _start_cameras(self, cam1, cam2):
        pass

    def run(self):
        cam1 = MockCamera(label="left")
        cam2 = MockCamera(label="right")
        self._main_function(cam1, cam2)


if __name__ == "__main__":
    with TLCameraSDK() as sdk:
        camera_list = sdk.discover_available_cameras()
        print(f"Operating with {len(camera_list)} cameras!")
        if len(camera_list) == 2: #beamsplitter design
            imager = CPL_Imager()
        elif len(camera_list) == 1: #compact design
            imager = Compact_CPL_Imager()
        elif len(camera_list) == 0:
            #raise Exception("Please plug in at least one camera")
            imager = CPL_Imager_No_Camera()
        else:
            raise Exception("Too many cameras!")
        imager.run()
