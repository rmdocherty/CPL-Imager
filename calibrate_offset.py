#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  1 17:22:21 2021

@author: ronan
"""
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

THRESH = 0.7

data = np.load("photos/test10.npy")
half_index = data.shape[1] // 2
LCPL_data = data[:, :half_index]
RCPL_data = data[:, half_index:]

def scan_for_above(threshold, array):
    """Get list of points where array > threshold"""
    above = np.where(array >= threshold, array, 0)
    matches = np.argwhere(above)
    return matches

def get_box(array):
    trans = array.T
    print(trans)
    min_x = np.amin(trans[1])
    max_x = np.amax(trans[1])
    min_y = np.amin(trans[0])
    max_y = np.amax(trans[0])
    bounding_box = [min_x, min_y, max_x, max_y]
    return bounding_box


def save_ROI(bbox, label):
    parsed = [str(i) for i in bbox]
    print(f"ROI is {parsed}")
    confirm = input("Is ROI acceptable (y/n)?")
    if confirm.lower() in ["y", "yes", "1"]:
        with open(f"roi_config_{label}.txt", "w") as f:
            for p in parsed:
                f.write(f"{p}\n")
        print("Written new ROI to file!")

def fix_diff(lbox, rbox):
    l_x_width = lbox[2] - lbox[0]
    l_y_width = lbox[3] - lbox[1]
    r_x_width = rbox[2] - rbox[0]
    r_y_width = rbox[3] - rbox[1]
    if l_x_width < r_x_width:
        diff = r_x_width - l_x_width
        lbox[2] += diff
    else:
        diff = l_x_width - r_x_width
        rbox[2] += diff
    if l_y_width < r_y_width:
        diff = r_y_width - l_y_width
        lbox[3] += diff
    else:
        diff = l_y_width - r_y_width
        rbox[3] += diff

def make_square(lbox, rbox):
    l_x_width = lbox[2] - lbox[0]
    l_y_width = lbox[3] - lbox[1]
    if l_x_width > l_y_width:
        lbox[3] += l_x_width - l_y_width
        rbox[3] += l_x_width - l_y_width
    if l_y_width > l_x_width:
        lbox[2] += l_y_width - l_x_width
        rbox[2] += l_y_width - l_x_width
        

filter_L = scan_for_above(THRESH, LCPL_data)
L_box = get_box(filter_L)

filter_R = scan_for_above(THRESH, RCPL_data)
R_box = get_box(filter_R)
R_box_prime = [R_box[0] + half_index, R_box[1], R_box[2] + half_index, R_box[3]]

root = tk.Tk()

canvas = tk.Canvas(master=root)

image = Image.open("photos/test10.bmp").convert('LA')
canvas_img = ImageTk.PhotoImage(master=canvas, image=image) # self._img_data
canvas.config(width=data.shape[1], height=data.shape[0])

canvas.create_image(0, 0, image=canvas_img, anchor='nw')
canvas.create_rectangle(0,0,5,5, fill="red")
canvas.create_rectangle(*L_box, outline="red")
canvas.create_rectangle(*R_box_prime, outline="blue")
canvas.pack()

root.mainloop()

fix_diff(L_box, R_box)
make_square(L_box, R_box)

save_ROI(L_box, "left")
save_ROI(R_box, "right")