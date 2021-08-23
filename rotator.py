#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 14:33:00 2021

@author: ronan
"""
#from pyftdi.ftdi import Ftdi
#import pyftdi.serialext
from time import sleep
import serial
from math import floor

PULSES_PER_DEGREE = 262144 / 360 #defined in docs
OFFSET_DEGREES = 1.7578125

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
            self._port = serial.Serial(port, baudrate=9600) #port='ftdi://ftdi:ft-x:DK0AJJZI/1'
            sleep(0.05)
            self._port.reset_input_buffer()
            self._port.reset_output_buffer()
            sleep(0.05)
            self._home_motor()
            #self._optimize_motor()
            #self._freq_search()
            #self._set_jog_size(45)
            self.rotate_to_angle(60.7) #reset pos -should be 52
        except Exception as error:
            print(f"Error: {error}, please supply a port.")
    
    def _send_command(self, command, data=""):
        command_string = command + data
        command_byte = str.encode(command_string, encoding='ASCII')
        self._port.write(command_byte)
    
    def _freq_search(self):
        self._send_command("0s1")
        self._check_status()
        self._send_command("0us")
    
    def _optimize_motor(self):
        self._send_command("0om")
        self._check_status()

    def _home_motor(self):
        self._send_command("0ho0")
        
    def _set_jog_size(self, angle):
        set_angle_string = self._get_set_angle_string(angle)
        self._send_command("0sj", set_angle_string)
    
    def _get_offset(self):
        self._send_command("0go")
        offset_hex = self._port.readline()[2:]
        offset_hex_string = '0x' + str.encode(offset_hex)
        offset_int = int(offset_hex_string, base=16)
        offset_string = str(offset_int)
        print(f"Offset is {offset_string} degrees")

    def _get_set_angle_string(self, angle):
        """Convert angle to # of pulses and convert that to hex string."""
        pulses = floor(angle * PULSES_PER_DEGREE) #should i use floor or ceil?
        int_string = hex(pulses)[2:].zfill(8)
        #print(int_string)
        return int_string.upper()

    def _send_get_status(self):
        self._send_command("0gs")
    
    def _check_status(self):
        done = False
        while done is False:
            self._send_get_status()
            data = self._port.readline()
            #print(data)
            if data.decode()[:5]  == "0GS00":
                done = True
            else:
                pass
        return 0

    def _check_angle(self):
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
        self._send_command("0ma", data=set_angle_str)
        self._check_angle()
        return 0

    def jog_forward(self):
        self._send_command("0fw")
        self._check_angle()
        return 0
    
    def jog_backward(self):
        self._send_command("0bw")
        self._check_angle()
        return 0
    
    def rotate_by_angle(self, angle):
        set_angle_str = self._get_set_angle_string(angle)
        self._send_command("0mr", data=set_angle_str)
        self._check_angle()
        return 0
        
#58 degrees = vertical, 9 = horizontal
# r = Rotator("/dev/ttyUSB0")
# r.rotate_to_angle(0)
# while True:
#     #r.jog_forward()
#     r.rotate_to_angle(60.7)
#     sleep(2)
#     r.rotate_to_angle(11.7)
#     #r.jog_backward()
#     sleep(2)
