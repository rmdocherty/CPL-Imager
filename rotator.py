#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 14:33:00 2021

@author: ronan
"""

import serial

PULSES_PER_DEGREE = 262144 / 360 #defined in docs


class Rotator():
    """
    Rotator.

    Class to interface with ELL14 Thorlabs piezo rotation mount. Assumes the
    use of an R232 interface over a USB cable so can use pySerial. Docs says to
    just send ASCII strings for commands to use Serial.write().
    """

    def __init__(self, port): #might need to add flushing and setting params
        try:
            self._port = serial.Serial(port) #can set baud rate here, want 9600!
            self.rotate_to_angle(0) #reset pos
        except Exception as error:
            print(f"Error: {error}, please supply a port.")

    def _get_set_angle_string(self, angle):
        """Convert angle to # of pulses and convert that to hex string."""
        pulses = int(angle * PULSES_PER_DEGREE) #should i use floor or ceil?
        hex_string = hex(pulses)
        return hex_string

    def _send_set_angle_string(self, ang_str):
        """Send command to rotator - commands have 3 letter prefix i.e Ama."""
        command = "Ama" + ang_str
        self._port.write(command)

    def _send_get_status(self):
        self._port.write("Ags")

    def _check_angle(self, ang_str):
        """Get device status until it returns the correct code (APO + pos in hex, specified in docs)."""
        rotated = False
        while rotated is False: #block until device says has rotated to specified angle
            self._send_get_status()
            data = self._port.read(11)
            position_command = "APO" + ang_str
            if data == position_command: #might be able to just set if data[:3] == "APO" if this doesn't work
                rotated = True
            else:
                pass
        return 0

    def rotate_to_angle(self, angle):
        """Send rotate command and wait until device rotated."""
        set_angle_str = self._get_set_angle_string(angle)
        self._send_set_angle_string(set_angle_str)
        self._check_angle(set_angle_str)
        return 0
