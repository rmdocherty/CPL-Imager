#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 14:33:00 2021

@author: ronan
"""

import serial

PULSES_PER_DEGREE = 262144 / 360


class Rotator():
    def __init__(self, port): #might need to add flushing and setting params
        try:
            self._port = serial.Serial(port) #can set baud rate here, want 9600!
        except Exception as error:
            print(f"Error: {error}, please supply a port.")

    def _get_set_angle_string(self, angle):
        pulses = int(angle * PULSES_PER_DEGREE) #should i use floor or ceil?
        hex_string = hex(pulses)
        return hex_string

    def _send_set_angle_string(self, ang_str):
        command = "Ama" + ang_str
        self._port.write(command)

    def _send_get_status(self):
        self._port.write("Ags")

    def _check_angle(self, ang_str): #should block wwhile rotating
        rotated = False
        while rotated is False: #block until device says has rotated to specified angle
            self._send_get_status()
            data = self._port.read(11)
            position_command = "APO" + ang_str
            if data == position_command: #might be able to just set if data[:3] == "APO" if this doesn't work
                rotated = True
                return 0
            else:
                pass

    def rotate_to_angle(self, angle):
        set_angle_str = self._get_set_angle_string(angle)
        self._send_set_angle_string(set_angle_str)
        self._check_angle(set_angle_str)
        return 0
