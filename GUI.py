#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 11:52:28 2021

@author: ronan
"""
import tkinter as tk
import csv
from colourmapper import ColourMapper, json, read_from_json, write_to_json, dA, CD
from PIL import ImageTk
import numpy as np
import queue
from datetime import datetime
from os import mkdir, path, getcwd
from sys import platform
if platform == "linux" or platform == "linux2":
    file_sep = "/"
else:
    file_sep = "\\"

def clearQueue(queue):
    while not queue.empty():
        queue.get()
    return 0

class Traffic_light(tk.Canvas):
    def __init__(self, parent):
        tk.Canvas.__init__(self, parent, width=30, height=30)
        self.on()
    def on(self):
        self.delete('all')
        self.create_circle(12, 19, 10, fill="#2cfc03", outline="#7bff61", width=1)
    def pause(self):
        self.delete('all')
        self.create_circle(12, 19, 10, fill="#ffa733", outline="#fcba62", width=1)
    def create_circle(self, x, y, r, **kwargs):
        return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)

class CPL_Viewer(tk.Frame):
    """
    CPL_Viewer.

    GUI object for the viewer, basically a menu of buttons on the left hand
    side of the liveCanvas. Before creating any widgets it needs a camera_widget
    ( == a liveCanvas) that it can bind functions to. This is because all the
    buttons are are wrappers for the liveCanvas functions anway. Widgets laid
    out according to grid system as this produces nicest results.
    """

    def __init__(self, master=None):
        mkdir("photos") if not path.exists("photos") else None #create photos folder if doesn't already exist
        tk.Frame.__init__(self, master)
        self._live = True
        self.master=master

    def set_camera_widget(self, camera_widget_object):
        self._camera_widget = camera_widget_object
        #self._camera_widget._mode = "Both"
        self._createWidgets()

    def set_control_queue(self, cq):
        self._CQ = cq
    
    def _createWidgets(self):
        """Add menu buttons to GUI and bind functions to them."""
        photo = tk.Button(text="Take Photo", command=self._take_photo, width=9)
        live = tk.Label(text="Acquire:")
        calibrate = tk.Button(text="Calibrate", command=self._calibrate_window, width=9)
        cmap_btn = tk.Button(text="Overlays", command=self.settings_window, width=9)
        label = tk.Label(text="Modes:")
        
        toggle = ("LCPL", "RCPL", "Both", "Pause")
        toggle_default = tk.StringVar(self.master)
        toggle_default.set("Both")
        toggle_dropdown = tk.OptionMenu(self.master, toggle_default, toggle[0], *toggle[1:], command=self._toggle_live)
        
        camera = tk.Label(text="Camera:")
        self.camera_icon = Traffic_light(self.master)
        rotator = tk.Label(master=self.master, text="Rotator:")
        self.rotator_icon = Traffic_light(self.master)
        
        options = ("raw", "DOCP", "dA")
        default = tk.StringVar(self.master)
        default.set("raw")
        dropdown = tk.OptionMenu(self.master, default, options[0], *options[1:], command=self.switch)
        
        btns = [photo, live, camera, rotator, calibrate, cmap_btn] #raw_btn, DOCP_btn, g_em_btn
        pad = 3 #1
        for index, b in enumerate(btns):
            colspan = 2 if index in [0, 4, 5] else 1
            b.grid(column=0, row=index, ipadx=pad, ipady=pad, padx=pad, pady=pad, columnspan=colspan)
        #dropdown.grid(column=1, row=2,  sticky=tk.W, padx=5, pady=5)
        toggle_dropdown.grid(column=1, row=1,  sticky=tk.W, padx=3, pady=3, ipadx=3, ipady=3)
        self.camera_icon.grid(column=1, row=2, ipadx=pad, padx=pad)
        self.rotator_icon.grid(column=1, row=3, ipadx=pad, padx=pad)
    def _switch_to_raw(self):
        self._camera_widget.set_cmap_mode("Raw")
    def _switch_to_DOCP(self):
        self._camera_widget.set_cmap_mode("DOCP")
    def _switch_to_g_em(self):
        self._camera_widget.set_cmap_mode("g_em") #was g_em
    def switch(self, mode):
        if mode == "raw":
            self._switch_to_raw()
        elif mode == "DOCP":
            self._switch_to_DOCP()
        else:
            self._switch_to_g_em()
    def _take_photo(self):
        if self._live is False:
            clearQueue(self._CQ)
            print("Taking static photo")
            self._CQ.put_nowait("Photo")
            self._camera_widget._get_image()
        self._camera_widget.take_photo()
    def _toggle_live(self, mode):
        """Pause the live view - used for compact setup to avoid overusing the
        rotation motor."""
        if mode == "LCPL" or mode == "RCPL":
            self.rotator_icon.pause()
            self.camera_icon.on()
        elif mode == "Pause":
            self.rotator_icon.pause()
            self.camera_icon.pause()
        elif mode == "Both":
            self.rotator_icon.on()
            self.camera_icon.on()
        clearQueue(self._CQ)
        self._CQ.put(mode)

    def settings_window(self):
        pad = 3
        self.settings_menu = tk.Toplevel()
        self.settings_menu.iconbitmap(f'photos{file_sep}CPL.ico')
        #self.settings_menu.geometry("240x220")
        self.settings_menu.title("Overlays")
        
        cmap_btn = tk.Button(self.settings_menu, text="Change cmaps", command=self._cmap_window)
        cmap_btn.grid( column=0, row=0, padx=pad, pady=pad)
        
        intensity_check = tk.Checkbutton(self.settings_menu, text="Intensity", width=9, command=self.toggle_intensity)
        intensity_check.grid(column=0, row=1, padx=pad, pady=pad)
    
        labels_check = tk.Checkbutton(self.settings_menu, text="Label", width=9, command=self.toggle_labels)
        labels_check.grid(column=0, row=2, padx=pad, pady=pad)
        
        calibrate_warning = tk.Label(self.settings_menu, text="Spatial calibration needed for following:")
        calibrate_warning.grid(column=0, row=3, padx=pad, pady=pad)
        
        tick_check = tk.Checkbutton(self.settings_menu, text= "Tick", width=9, command=self.toggle_tick)
        tick_check.grid(column=0, row=4, padx=pad, pady=pad)
        
        axes_check = tk.Checkbutton(self.settings_menu, text= "Axes", width=9, command=self.toggle_axes)
        axes_check.grid(column=0, row=5, padx=pad, pady=pad)
        
        grid_check = tk.Checkbutton(self.settings_menu, text= "Grid", width=9, command=self.toggle_grid)
        grid_check.grid(column=0, row=6, padx=pad, pady=pad)
    def toggle_intensity(self):
        self._camera_widget.show_intensity = not self._camera_widget.show_intensity
    def toggle_labels(self):
        self._camera_widget.show_labels = not self._camera_widget.show_labels
    def toggle_grid(self):
        self._camera_widget.show_grid = not self._camera_widget.show_grid
    def toggle_tick(self):
        self._camera_widget.show_tick_bar = not self._camera_widget.show_tick_bar
    def toggle_axes(self):
        self._camera_widget.show_tick_axes = not self._camera_widget.show_tick_axes

    def _cmap_window(self):
        """Popup window to set colourmaps during operation."""
        self._cmap_menu = tk.Toplevel()
        self._cmap_menu.iconbitmap(f'photos{file_sep}CPL.ico')
        self._cmap_menu.title("Colour map selector")
        LCPL = tk.Text(self._cmap_menu, height=2, width=30)
        LCPL_text = tk.Label(self._cmap_menu, text="LCPL:")
        RCPL = tk.Text(self._cmap_menu, height=2, width=30)
        RCPL_text = tk.Label(self._cmap_menu, text="RCPL:")
        DOCP = tk.Text(self._cmap_menu, height=2, width=30)
        DOCPL_text = tk.Label(self._cmap_menu, text="DOCP:")
        g_em = tk.Text(self._cmap_menu, height=2, width=30)
        g_em_text = tk.Label(self._cmap_menu, text="dA:")

        self._cmap_menu_fields = [LCPL, RCPL, DOCP, g_em]

        set_cmaps = tk.Button(self._cmap_menu, text="Done", command=self._submit_cmaps)
        for i, lbl in enumerate([LCPL_text, RCPL_text, DOCPL_text, g_em_text]):
            lbl.grid(column=0, row=i)
        for i, txt in enumerate([LCPL, RCPL, DOCP, g_em]):
            txt.grid(column=1, row=i)
        set_cmaps.grid(column=0, row=4, columnspan=2)
    def _submit_cmaps(self):
        cmap_list = []
        for txt_field in self._cmap_menu_fields:
            text = txt_field.get("1.0", "end-1c")
            cmap_list.append(text)
        try:
            self._camera_widget.set_cmaps(cmap_list)
        except Exception:
            print("Invalid cmaps supplied, check you've entered correctly!")
        self._cmap_menu.destroy()

    def _calibrate_window(self):
        """Popup window to generate multiplicative correction map for cameras."""
        self._calibrate_menu = tk.Toplevel()
        self._calibrate_menu.iconbitmap(f'photos{file_sep}CPL.ico')
        #self._calibrate_menu.geometry("220x150")
        self._calibrate_menu.title("Calibration")

        correction_map = tk.Button(self._calibrate_menu, text="RPS correction", command=self.rps_window, width=14).grid(column=0, row=1, padx=3, pady=2) #, columnspan=2
        spatial_calibrate = tk.Button(self._calibrate_menu, text="Spatial calibration", command=self.start_spatial_calibrate, width=14).grid(column=0, row=2, padx=3, pady=2)
        roi_reset = tk.Button(self._calibrate_menu, text="Reset ROI", command=self.reset_roi, width=14).grid(column=0, row=3, padx=3, pady=2)
        roi_calibrate = tk.Button(self._calibrate_menu, text="ROI calibration", command=self.start_roi_calibrate, width=14).grid(column=0, row=4, padx=3, pady=2)
        intensity_calibrate =  tk.Button(self._calibrate_menu, text="Intensity calibration", command=self.start_intensity_calibration, width=14).grid(column=0, row=5, padx=3, pady=2)
        threshold_calibrate =  tk.Button(self._calibrate_menu, text="Set threshold", command=self.threshold_window, width=14).grid(column=0, row=6, padx=3, pady=2)
        dummy = tk.Label(self._calibrate_menu, text="                                                                        ").grid(column=0, row=7, padx=3, pady=2)
    def start_spatial_calibrate(self):
        self._camera_widget.roi_calibrate_on = False
        self._camera_widget.spatial_calibrate_on = True
        self._calibrate_menu.destroy()
    def start_roi_calibrate(self):
        self._camera_widget.roi_calibrate_on = True
        self._camera_widget.spatial_calibrate_on = False
        self._calibrate_menu.destroy()
        self._camera_widget.roi_calibrate()
    def start_intensity_calibration(self):
        self._calibrate_menu.destroy()
        self._camera_widget.intensity_calibrate()
        
    def reset_roi(self):
        ROI = (0, 0, 1024, 1024)
        write_to_json("roi_left", ROI)
        write_to_json("roi_right", ROI)
        try:
            self._camera.roi = ROI
        except:
            print("Failed to set camera ROI")
        self._camera_widget.roi_window("ROI reset")
    def _finish_calibrate(self):
        self._calibrate_menu.destroy()
    
    def rps_window(self):
        self.rps_menu = tk.Toplevel()
        self.rps_menu.iconbitmap(f'photos{file_sep}CPL.ico')
        self.rps_menu.title("RPS Calibration")
        #self.rps_menu.geometry("220x100")

        LCPL_uniform = tk.Text(self.rps_menu, height=1, width=7)
        LCPL_uniform.grid(column=1, row=0)
        LCPL_text = tk.Label(self.rps_menu, text="LCPL in RPS:").grid(column=0, row=0)
        RCPL_uniform = tk.Text(self.rps_menu, height=1, width=7)
        RCPL_uniform.grid(column=1, row=1)
        RCPL_text = tk.Label(self.rps_menu, text="RCPL in RPS:").grid(column=0, row=1)
        finish_rps = tk.Button(self.rps_menu, text="Finish", command=self.finish_rps).grid(column=1, row=3)
        self.rps_menu_text_fields = [LCPL_uniform, RCPL_uniform]
    def _gen_correction(self):
        """Given expected intensity of Reference Polarization State (RPS), create
        correction map."""
        data = self._camera_widget._np_array
        LCPL_btn = self.rps_menu_text_fields[0]
        RCPL_btn = self.rps_menu_text_fields[1]
        zero_thresh = 0.2
        try:
            ref_LCPL_intensity = float(LCPL_btn.get("1.0", "end-1c"))
            ref_RCPL_intensity = float(RCPL_btn.get("1.0", "end-1c"))
        except (ValueError, AttributeError): #assume a 50/50 split state (45 deg)
            ref_LCPL_intensity = 0.5
            ref_RCPL_intensity = 0.5
        half_index = data.shape[1] // 2
        LCPL_data = data[:, :half_index]
        RCPL_data = data[:, half_index:]
        LCPL_mask = np.where(LCPL_data > zero_thresh, ref_LCPL_intensity / LCPL_data, 0)
        RCPL_mask = np.where(RCPL_data > zero_thresh, ref_RCPL_intensity / RCPL_data, 0)
        self._camera_widget.set_masks(LCPL_mask, RCPL_mask)    
    def finish_rps(self):
        self._gen_correction()
        self.rps_menu.destroy()
    
    def threshold_window(self):
        self.threshold_menu = tk.Toplevel()
        self.threshold_menu.iconbitmap(f'photos{file_sep}CPL.ico')
        self.threshold_menu.title("Threshold Calibration")
        self.threshold_input = tk.Text(self.threshold_menu, height=1, width=7)
        self.threshold_input.grid(column=1, row=0)
        threshold_text = tk.Label(self.threshold_menu, text="Intensity threshold:").grid(column=0, row=0)
        finish_threshold = tk.Button(self.threshold_menu, text="Finish", command=self.finish_threshold).grid(column=1, row=3)
    def finish_threshold(self):
        try:
            self._camera_widget.threshold = float(self.threshold_input.get("1.0", "end-1c"))
        except (ValueError, AttributeError):
            self._camera_widget.threshold = 0
        self.threshold_menu.destroy()
    
            

class LiveViewCanvas(tk.Canvas):
    """LiveViewCanvas.

    This is a Tkinter Canvas object that can be reused in custom programs. The Canvas expects a parent Tkinter object and
    an image queue. The image queue is a queue.Queue that it will pull images from, and is expected to hold PIL Image
    objects that will be displayed to the canvas. It automatically adjusts its size based on the incoming image dimensions.
    Has been modified from default, now expects and grabs from two image queues
    desgined to relfect the two-camera nature of project. The grabbed images are
    then fed into the ColourMapping object which performs the right mapping given
    the mode and spits out a PIL image to be thrown onto the canvas.
    """

    def __init__(self, parent, iq1, iq2, img_type="default"):
        self.image_queue1 = iq1
        self.image_queue2 = iq2
        self._image_width = 0
        self._image_height = 0
        self._type = img_type

        self._cmap = ColourMapper("Raw")
        self._img_data = [] # need variable to store image in as can't seem to save directly from a ImageTk.PhotoImage Object

        self._LCPL_mask = np.array([1])
        self._RCPL_mask = np.array([1])

        tk.Canvas.__init__(self, parent)

        self._intensity = 0
        self.threshold = 0
        self.bind_all('<Motion>', self._get_intensity_at_cursor)
        
        self.roi_calibrate_on = False
        self.spatial_calibrate_on = False
        self.intensity_calibrate_on = False
        self.bind("<ButtonPress-1>", self.add_click)
        self.clicks = []

        self.pixels_per_mm = read_from_json("pixels_per_mm") #config_json["pixels_per_mm"]
        self.tick_dist = read_from_json("tick_dist") #config_json["tick_dist"]
        self.tick_spacing_px = self.pixels_per_mm * self.tick_dist
        self.show_tick_bar = False
        self.show_tick_axes = False
        self.show_grid = False
        self.show_intensity = False
        self.show_labels = False
        
        # need the columnspan and row span to make alignment nice
        self.grid(column=2, row=0, columnspan=5, rowspan=5)
        
        self.cbar_initialised = False
        self._cbar_canv = tk.Canvas(parent)#parent
        self._cbar_canv.grid(column=7, row=0, rowspan=5, columnspan=1, padx=16, pady=16)
        self._mode = "Raw"

        
        self._sizes = {"Raw": (720, 720), "DOCP": (360, 360), "g_em": (360, 360), "CD": (360, 360)}

        self._get_image()

    def set_masks(self, LCPL, RCPL):
        self._LCPL_mask = LCPL
        self._RCPL_mask = RCPL
    def initialise_cbar(self, img1, img2):
        delta_A = dA(img1, img2) # dA = np.log10(img1/img2) #img1 - img2#np.log10(img2/img1)
        theta_mdeg = CD(delta_A)#theta_mdeg = np.arctan( np.tanh( (np.log(10)*dA)/4 )) * (180*10**3) / np.pi
        vmax_dA = max(np.abs(np.amax(delta_A)), np.abs(np.amin(delta_A)))
        vmax_theta_mdeg = max(np.abs(np.amax(theta_mdeg)), np.abs(np.amin(theta_mdeg)))
        cbar_img = self._cmap.gen_colourbar(limits=[np.array([[-vmax_dA, vmax_dA]]), np.array([[-vmax_theta_mdeg, vmax_theta_mdeg]])])
        self._pack_cbar_img(cbar_img)
        self.cbar_initialised = True
    def _pack_cbar_img(self, cbar_img):
        """Given PIL image of colorbar, add it to tkinter canvas and pack
        canavs to RHS of image. The TkPhotoImage is saved to an attribute as
        config needs a permanent reference to image otherwise won't display."""
        self._cbar_img_pil = cbar_img
        self._cbar_img = ImageTk.PhotoImage(master=self._cbar_canv, image=cbar_img)
        self._cbar_canv.config(width=self._cbar_img.width(), height=self._cbar_img.height())
        self._cbar_canv.create_image(0, 0, image=self._cbar_img, anchor='nw')
    def set_cmap_mode(self, mode):
        """Setter for the Cmap mode."""
        self._mode = mode
        self._cmap.set_mode(mode)
        #print(self._img_data)
    def set_cmaps(self, cmap_list):
        self._cmap.set_cmaps(cmap_list)
    
    def _get_image(self):
        """Grab the two images (LCPL & RCPL) from their two queues, apply
        correction (if it exist) then combine the iumage data into one array
        and colourmap it. Next resize these images and draw them onto the canvas.
        If either queue is empty, pass."""
        iq1 = self.image_queue1
        iq2 = self.image_queue2
        try:
            image1 = iq1.get_nowait()
            image2 = iq2.get_nowait()
            #check these later!
            image1 = np.where(image1 > self.threshold, image1, 0)
            image2 = np.where(image2 > self.threshold, image2, 0)
            image1 = image1 * self._LCPL_mask
            image2 = image2 * self._RCPL_mask
            
            
            if self._type == "2cam": #when second camera added, beamsplitter means you need to flip the second image so LCPL and RCPl right way up
                image2 = image2[::-1]

            self._np_array = np.hstack((image1, image2))
            unrotated_img = self._cmap.colour_map(image1, image2)
            self._img_data = unrotated_img
            resized = unrotated_img.resize(self._sizes[self._mode]) #(w, h)
            self._resized = resized

            self._image = ImageTk.PhotoImage(master=self, image=resized) # self._img_data
            if (self._image.width() != self._image_width) or (self._image.height() != self._image_height):
                # resize the canvas to match the new image size
                self._image_width = self._image.width()
                self._image_height = self._image.height()  #remove this scaling later!
                self.config(width=self._image_width, height=self._image_height)
            # DRAWING STUFF
            self.delete('all') #need to garbage collect old canvas objects (not deleted automatically)
            self.create_image(0, 0, image=self._image, anchor='nw')
            self.draw_overlays()
            if self.cbar_initialised is False:
                self.initialise_cbar(image1, image2)
            
        except queue.Empty:
            pass
        self.after(20, self._get_image) #repeat this function every 20ms

    def take_photo(self):
        """Take snapshot of current image on the canvas and save as bitmap.
        Creates a new folder in the the photos directory that contains the
        colourmapped image in bmp form, the original image data in csv, txt and
        npy form, an image of the colorbar used and the mask data.
        
        TODO: also use imageGrab to get image of canvas including overlays?
        """
        timestamp = datetime.now()
        timestamp_string = timestamp.strftime("%d-%m-%y_%H_%M_%S_%f")
        if platform == "linux" or platform == "linux2":
            file_sep = "/"
        else:
            file_sep = "\\"
        directory = getcwd() + file_sep + "photos" + file_sep + timestamp_string
        mkdir(directory)
        file_path = directory + file_sep + timestamp_string

        self._img_data.save(file_path + ".bmp", format="bmp") #save photo
        self._cbar_img_pil.save(file_path + "_colorbar.bmp", format="bmp") #save colorbar
        np.save(file_path, self._np_array) #save np array of raw wdata
        with open(file_path + ".txt", 'w') as txt_f, open(file_path + ".csv", 'w') as csv_f:
            writer = csv.writer(csv_f)
            for row in self._np_array:
                writer.writerow(row)
                txt_f.write(", ".join([str(col) for col in row]) + "\n")
        with open(file_path + "_metadata.txt", 'w') as txt:
            txt.write(f"{timestamp_string} \n")
            txt.write(self._mode + "\n")
            txt.write("LCPL mask: \n")
            for row in self._LCPL_mask:
                try:
                    txt.write(", ".join([str(col) for col in row]) + "\n")
                except TypeError:
                    txt.write("1 \n")
            txt.write("RCPL mask: \n")
            for row in self._RCPL_mask:
                try:
                    txt.write(", ".join([str(col) for col in row]) + "\n")
                except TypeError:
                    txt.write("1 \n")
            txt.write(f"{str(self.pixels_per_mm)} pixels per mm \n" )
    
    def draw_overlays(self):
        calibrated = ((self.tick_dist > 0) and (self.tick_spacing_px > 0))
        if self.show_grid and calibrated:
            self.draw_grid()
        if self.show_tick_axes and calibrated:
            self.draw_tick_axes()
        if self.show_tick_bar and calibrated:
            self.draw_tick_bar()
        
        if self.show_intensity:
            self._draw_intensity()
        if self.roi_calibrate_on and len(self.clicks) == 1:
            self.draw_rect()
        if self.show_labels:
            self.draw_labels()
        if self.intensity_calibrate_on:
            LCPL_i, RCPL_i = self.check_saturation()
            self.LCPL_live_intensity_text['text'] = f"{LCPL_i:.2f}"#(str(LCPL_i))
            self.RCPL_live_intensity_text['text'] = f"{RCPL_i:.2f}"#(str(RCPL_i))
        crosses = [self.draw_crosses(c) for c in self.clicks]
    def _draw_intensity(self):
        """Draw the current intensity to the screen."""
        x, y = self.mouse_pos
        quad_x, quad_y = x // 360, y // 360
        names = [["LCPL", "RCPL"], ["dA", "CD"]]
        positions = [[(260, 350), (620, 350)], [(270, 710), (620, 710)]]
        mode = names[quad_y][quad_x]
        pos = positions[quad_y][quad_x]
        self.create_text(pos[0], pos[1], anchor=tk.W, fill="Black", font=("Arial", 12), text=f"{mode}:{self._intensity:.4f}")
    def draw_crosses(self, c):
        self.create_text(c[0]-3, c[1], anchor=tk.W, font=("Arial", 8), text="X", fill="Orange")
    def draw_line(self, offset_x=0, offset_y=360, max_px=360, orient="x",
                  size=7, color="black", text=True):
        o1, o2 = (1, 0) if orient == "y" else (0, 1)
        i = 0
        while i*self.tick_spacing_px < max_px:
            x1, x2 = offset_x+o1*i*self.tick_spacing_px, offset_x+o1*i*self.tick_spacing_px+o2*size  
            y1, y2 = offset_y-o2*i*self.tick_spacing_px, offset_y-o2*i*self.tick_spacing_px-o1*size  
            if text:
                text = f"{i*self.tick_dist:.2f}"
                self.create_text(x2+3*o1, y2+5*o2, width=0.1, anchor=tk.W, fill=color, font=("Arial", 6), text=text)
            self.create_line(x1, y1, x2, y2, fill=color)
            i += 1
    def draw_tick_axes(self):
        positions = [(0, 360), (0, 720), (360, 360), (360, 720)]
        for p in positions:
            self.draw_line(orient="x", offset_x=p[0], offset_y=p[1])
            self.draw_line(orient="y", offset_x=p[0], offset_y=p[1])
    def draw_grid(self):
        positions = [(0, 360), (0, 720), (360, 360), (360, 720)]
        for p in positions:
            self.draw_line(orient="x", color="Gray", size=360, text=False, offset_x=p[0], offset_y=p[1])
            self.draw_line(orient="y", color="Gray", size=360, text=False, offset_x=p[0], offset_y=p[1])
    def draw_tick_bar(self):
        positions = [(10, 320), (10, 680), (370, 320), (370, 680)]
        for p in positions:
            x1, y1, x2, y2 = p[0], p[1], p[0] + self.tick_spacing_px, p[1] #10, 320, 10 + self.tick_spacing_px, 320
            self.create_line(x1, y1, x2, y2)
            self.create_line(x1, y1 + 4, x1, y1-4)
            self.create_line(x2, y1 + 4, x2, y1-4)
            self.create_text(x1 + ((x2 - x1) / 5), y1 + 14, width=0.1, anchor=tk.W, fill="Black", font=("Arial", 10), text=f"{self.tick_dist:.3f}mm")
    def draw_rect(self):
        click = self.clicks[0]
        mouse = self.mouse
        self.create_rectangle(click[0], click[1], mouse[0], mouse[1], outline="Orange")
    def draw_labels(self):
        self.create_text(10, 10, width=0.1, anchor=tk.W, fill="Black", font=("Arial", 12), text="LCPL")
        self.create_text(370, 10, width=0.1, anchor=tk.W, fill="Black", font=("Arial", 12), text="RCPL")
        self.create_text(10, 370, width=0.1, anchor=tk.W, fill="Black", font=("Arial", 12), text="dA")
        self.create_text(370, 370, width=0.1, anchor=tk.W, fill="Black", font=("Arial", 12), text="CD (mdeg)")
    
    def add_click(self, event):
        if self.spatial_calibrate_on or self.roi_calibrate_on:
            self.clicks.append((event.x, event.y))
        if len(self.clicks) == 2 and self.spatial_calibrate_on:
            self.spatial_calibrate()
        elif len(self.clicks) == 2 and self.roi_calibrate_on:
            self.finish_roi_calibrate()
    def _get_intensity_at_cursor(self, event):
        """Get intensity of image at the location of the mouse cursor. However
        the image on screen is resized from the original data so must scale the
        cursor position based on the size ratios and get intesnity at that
        rescaled position. Intensity depends on which mode we're in so need to
        recalculate the metric each time."""
        try:
            x, y = event.x, event.y

            data = self._np_array
            arr_x, arr_y = data.shape[1] // 2, data.shape[0]
            scale_factor_x = arr_x / self._sizes[self._mode][0]
            scale_factor_y = arr_y / self._sizes[self._mode][1]
            LCPL = self._np_array[:, :arr_x]
            RCPL = self._np_array[:, arr_x:]
            delta_A = dA(LCPL, RCPL)#dA = np.log10(LCPL/RCPL) #LCPL - RCPL#np.log10(RCPL/LCPL)
            theta_mdeg = CD(delta_A) #np.arctan(np.tanh( (np.log(10)*dA) /4 )) * (180*10**3) / np.pi
            bot = np.hstack((delta_A, theta_mdeg))
            data = np.vstack((data, bot))

            scale_factor_x *= 2
            scale_factor_y *= 2
            x_prime, y_prime = int(x * scale_factor_x), int(y * scale_factor_y)
            self._intensity = data[y_prime, x_prime]
            self.mouse_pos = (x, y)

        except IndexError: #if out of bounds then pass
            x, y = 0, 0
    def track_mouse(self, event):
        self.mouse = (event.x, event.y)

    def roi_calibrate(self):
        self.bind_all('<Motion>', self.track_mouse)
    def roi_window(self, text):
        tk.messagebox.showinfo("ROI setting complete", f"{text}, restart program to take effect.")
    def finish_roi_calibrate(self):
        self.bind_all('<Motion>', self._get_intensity_at_cursor)
        x1, y1 = self.clicks[0]
        x2, y2 = self.clicks[1]
        ROI = [x1, y1, x2, y2]
        write_to_json("roi_left", ROI) #[] = [x1, y1, x2, y2]
        write_to_json("roi_right", ROI)
        try:
            self._camera.roi = ROI
        except:
            print("Failed to set camera ROI")
        self.clicks = []
        self.roi_calibrate_on = False
        self.roi_window(text="ROI calibrated")

    def spatial_calibrate(self):
        clicks = self.clicks
        dx = np.abs(clicks[0][0] - clicks[1][0])
        dy = np.abs(clicks[0][1] - clicks[1][1])
        self.click_dist = np.sqrt(dx**2 + dy**2)
        
        self.spatial_menu = tk.Toplevel()
        self.spatial_menu.iconbitmap(f'photos{file_sep}CPL.ico')
        self.spatial_menu.title("Spatial Calibration")
        #self.spatial_menu.geometry("220x100")
        enter_dist = tk.Text(self.spatial_menu, height=1, width=8)
        enter_dist.grid(column=1, row=1)
        query = tk.Label(self.spatial_menu, text="Reference distance (mm): ").grid(column=0, row=1)
        finish_spatial = tk.Button(self.spatial_menu, text="Finish", command=self.finish_spatial).grid(column=1, row=3)
        self.spatial_menu_text_field = enter_dist
    def calculate_tick_spacing(self, axes_length):
        total_ticks = 11
        total_dist = axes_length / self.pixels_per_mm
        order_of_magnitude = np.floor(np.log10(total_dist))
        leading_val = 10**order_of_magnitude
        tick_spacing = 0
        for i in [leading_val, leading_val / 2, leading_val / 4, leading_val / 5, leading_val / 10]:
            if total_dist / i < total_ticks:
                tick_spacing = i
        return self.pixels_per_mm * tick_spacing, tick_spacing
        
    def set_tick_bar(self, tick_spacing_px, tick_spacing_mm):
        self.show_tick_bar = True
        self.show_tick_axes = True
        self.show_grid = True
        self.tick_spacing_px = tick_spacing_px
        self.tick_dist = tick_spacing_mm
    def finish_spatial(self):
        field = self.spatial_menu_text_field
        try:
            ref_dist = float(field.get("1.0", "end-1c"))
        except (ValueError, AttributeError): #assume a 50/50 split state (45 deg)
            print("Error in reference distance!")
            ref_dist = 0.5
        self.pixels_per_mm = self.click_dist / ref_dist
        self.clicks = []
        tick_spacing_px, tick_spacing_mm = self.calculate_tick_spacing(360)
        dist_mm = tick_spacing_px / self.pixels_per_mm
        self.tick_spacing_px, self.tick_dist = tick_spacing_px, tick_spacing_mm
        write_to_json("pixels_per_mm", self.pixels_per_mm)
        write_to_json("tick_dist", self.tick_dist)
        self.spatial_calibrate_on = False
        self.spatial_menu.destroy()
        tk.messagebox.showinfo("Spatial complete", f"Pixels per mm: {self.pixels_per_mm:.4f}.\nUse Overlay menu to display ticks, axes and grids")
    
    def intensity_calibrate(self):
        self.intensity_calibration = tk.Toplevel()
        self.intensity_calibration.iconbitmap(f'photos{file_sep}CPL.ico')
        self.intensity_calibrate_on = True
        self.intensity_calibration.title("Intensity Calibration")
        LCPL_intensity_text = tk.Label(self.intensity_calibration, text="LCPL % saturation:").grid(column=0, row=0)
        RCPL_intensity_text = tk.Label(self.intensity_calibration, text="RCPL % saturation:").grid(column=0, row=1)
        self.LCPL_live_intensity_text = tk.Label(self.intensity_calibration, text="0")
        self.RCPL_live_intensity_text = tk.Label(self.intensity_calibration, text="0")
        self.LCPL_live_intensity_text.grid(column=1, row=0)
        self.RCPL_live_intensity_text.grid(column=1, row=1)
        finish_intensity = tk.Button(self.intensity_calibration, text="Finish", command=self.finish_intensity).grid(column=1, row=3)
    def check_saturation(self):
        data = self._np_array
        arr_x, arr_y = data.shape[1] // 2, data.shape[0]
        scale_factor_x = arr_x / self._sizes[self._mode][0]
        scale_factor_y = arr_y / self._sizes[self._mode][1]
        LCPL = self._np_array[:, :arr_x]
        RCPL = self._np_array[:, arr_x:]
        return_percents = []
        for data in [LCPL, RCPL]:
            non_zero = np.where(data > 0.08)[0] #region where intensity isn't zero
            saturated = np.where(data >= 1)[0] #regions where pixel value is 1
            data_length = data.shape[0] * data.shape[1]
            try:
                saturation_percent = 100 * len(saturated) / len(non_zero)
            except ZeroDivisionError:
                saturation_percent = 0
            return_percents.append(saturation_percent)
        return return_percents
    def finish_intensity(self):
        self.intensity_calibrate_on = False
        self.intensity_calibration.destroy()