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
            # self._port = Ftdi().create_from_url("ftdi://ftdi:ft-x:DK0AJJZI/1") #can set baud rate here, want 9600! serialext.serial_for_url
            # self._port.set_baudrate(9600)
            # self._port.set_line_property(8, 1, "N")
            # sleep(0.05) #pre purge dwell
            # self._port.purge_buffers()
            # self._port.purge_rx_buffer()
            # self._port.purge_tx_buffer()
            # sleep(0.05) #post purge dwell
            # self._port.reset()
            # self._port.set_flowctrl("")
            
            
            #data = self._port.read_data(11)
            #print(data)
            self.rotate_to_angle(0) #reset pos
        except Exception as error:
            print(f"Error: {error}, please supply a port.")

    def _get_set_angle_string(self, angle):
        """Convert angle to # of pulses and convert that to hex string."""
        pulses = int(angle * PULSES_PER_DEGREE) #should i use floor or ceil?
        int_string = hex(pulses)[2:].zfill(8)
        #hex_string = str.encode(int_string) #hex(pulses)
        return int_string

    def _send_set_angle_string(self, ang_str):
        """Send command to rotator - commands have 3 letter prefix i.e Ama."""
        command = "0ma" + ang_str
        command_byte = str.encode(command)
        print(command_byte)
        #self._port.write_data(command_byte)
        self._port.write(command_byte)
        print("sent set angle commnad")

    def _send_get_status(self):
        command_byte = str.encode("0gs")
        #self._port.write_data(command_byte)
        self._port.write(command_byte)
        #print("sent status")

    def _check_angle(self, ang_str):
        """Get device status until it returns the correct code (APO + pos in hex, specified in docs)."""
        rotated = False
        print("checking status")
        while rotated is False: #block until device says has rotated to specified angle
            #self._send_get_status()
            #data = self._port.read_data_bytes(11)
            data = self._port.readline()
            print(data)
            #if data != b'':
            #    print(data)
            #position_command = "0PO" + ang_str
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
        print("Done!")
        return 0

r = Rotator("/dev/ttyUSB0")
sleep(0.002)
r.rotate_to_angle(90)