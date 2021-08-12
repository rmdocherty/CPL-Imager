#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 14:33:00 2021

@author: ronan
"""
from pyftdi.ftdi import Ftdi
import pyftdi.serialext
from time import sleep
import serial
from math import floor

PULSES_PER_DEGREE = 262144 / 360 #defined in docs


class Rotator():
    """
    Rotator.

    Class to interface with ELL14 Thorlabs piezo rotation mount. Assumes the
    use of an R232 interface over a USB cable so can use pySerial. Docs says to
    just send ASCII strings for commands to use Serial.write().
    NB MUST TYPE "sudo chmod 666 /dev/ttyUSB0" to get permission to run.
    """

    def __init__(self, port): #might need to add flushing and setting params
        try:
            self._port = pyftdi.serialext.serial_for_url('ftdi://ftdi:ft-x:DK0AJJZI/1', baudrate=9600)
            sleep(0.05)
            self._port.reset_input_buffer()
            self._port.reset_output_buffer()
            sleep(0.05)
            self._home_motor()
            self.rotate_to_angle(52) #reset pos
        except Exception as error:
            print(f"Error: {error}, please supply a port.")

    def _home_motor(self):
        command_string = "0ho1"
        command_byte = str.encode(command_string)
        self._port.write(command_byte)

    def _get_set_angle_string(self, angle):
        """Convert angle to # of pulses and convert that to hex string."""
        pulses = floor(angle * PULSES_PER_DEGREE) #should i use floor or ceil?
        int_string = hex(pulses)[2:].zfill(8)
        return int_string.upper()

    def _send_set_angle_string(self, ang_str):
        """Send command to rotator - commands have 3 letter prefix i.e Ama."""
        command = "0ma" + ang_str
        command_byte = str.encode(command)
        self._port.write(command_byte)

    def _send_get_status(self):
        command_byte = str.encode("0gs")
        self._port.write(command_byte)

    def _check_angle(self, ang_str):
        """Get device status until it returns the correct code (APO + pos in hex, specified in docs)."""
        rotated = False
        while rotated is False: #block until device says has rotated to specified angle
            data = self._port.readline()
            #print(data)
            if data.decode()[:3] == "0PO": #might be able to just set if data[:3] == "APO" if this doesn't work
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
