# CPL-Imager

## Introduction:
Welcome to the manual for the CPL-Imager, a low-cost, compact circularly polarised imaging system. This system is designed to be quick to assemble and modular enough that it can be adapted to suit a variety of needs (in situ annealing, translation stages, magnets etc). Its is primarily designed to image chiral thin-films, but can easily be applied to other contexts, like solutions.

The instrument consists of a fresnel rhomb (which converts CPL to linearly polarised light), followed by a linear polariser in a piezoelectric rotation mount and a Thorlabs scientific camera. CPL-Imager controls the rotation of the piezomotor, ensuring subsequent images taken by the camera are of alternating handedness (i.e Left-CPL then Right-CPL then Left-CPL etc.). These LCPL and RCPL images are then combined to calculate differential absorbance and Circular Dichroism and these four quantities are then displayed on a live view in the GUI.

Abbreviations used:
- CPL = Circularly Polarised Light. LCPL = Left-CPL, RCPL = Right-CPL
- dA = delta Absorbance
- CD = Circular Dichroism
- GUI = Graphical User Interface
- FR = Fresnel Rhomb
- TL = ThorLabs

## Assembly:
Detailed assembly instructions (including photos) can be found in "assembly.txt", but the long and short of is as follows:
1) Place the FR into the 30-60mm TL cage adapter, then screw in the 2" rods in. 
2) Place this construction in the 3D printed front body, then screw the setscrews into the ends of rods facing away from the FR.
3) Place the ELL14 piezoelectric rotator on the back of the casing such that the setscrews poke through the holes in the rotator.
4) Place the 3D printed back body case onto the poking out screws.
5) Starting from bottom to top, screw in the 3" rods to the setscrews in the back body casing.
6) Screw the capscrews through the back plate into the camera, then screw more capscrews through the reverse of the plate into the rods so the camera sits enclosed in the casing.
7) Screw the capscrews through the front plate into the rods inside the front body casing.
8) Place the piezorotator board into its space on the bottom of the back body, then plug the USBs from the camera and piezorotator board into either your computer or a Raspberry Pi.

There is an alternate setup with 2 cameras and a polarised beamsplitter (rather than the piezorotator), but this is more expensive and has difficulty in aligning the 2 cameras. However, it has no associated rotator delay so can run with a higher framerate.

## Software:
These following sections refer to the control software of the CPL-Imager. Certain sections are colour coded to refer to sections of the GUI image. A handy quickstart guide is in the "docs" folder under the filename "quickstart.png", which may be sufficient to understand the software.


## Installation:
As with assembly, detailed installation instructions (including automated scripts) can be found in the "install" folder, but to sum up:
- Download the correct Thorlabs SDK from their website (link!) for your system. If using a Raspberry Pi for the setup, email the Thorlabs tech support team at (email!) and ask for their experimental ARM SDK, where the .so files are compiled for the right instruction set. Alternatively, I can provide it upon request.
- Run whatever "THORLABS_SDK_INSTALLATION_INSTRUCTIONS.txt" says to do for your system, and install the Python library in the "Python Toolkit" folder
- Install the required Python libraries (numpy, matplotlib, Pillow, pyserial)
After that, you're all set!

## Panel layouts:
The software has 4 panels which show different data. The top two panels show the last readings of LCPL and RCPL intensity taken from the camera. The bottom two show dA and CD, two measures of the differential absorption of LCPL vs RCPL common in the literature. All 4 are colourmapped based on the colourmaps in "config.json"; the values of these colours can be read off the colourbars on the right hand side of the screen, where the colour bar position corresponds to the same data pane (i.e top left colourbar is LCPL).

## Taking photos:
Pressing the "Take Photo" button will take a photo of whatever is currently on the GUI screen and save it to a timestamped directory in the "photos" folder. This will contain a bitmap of the image, a .txt, .csv and .npy of the raw LCPL and RCPL data and a file describing the image metadata like any corrections applied or the pixels per mm of the images.

## Acquisition modes:
There are 4 possible acquisition modes of the software, available under the "Acquire" dropdown menu:
- Both: the rotator will rotate every 0.2 seconds, taking images of alternating handedness and displaying them on the screen. dA and CD will be calculated automatically and displayed as well. This mode has an associated 0.2s delay, and the rotator will burn out if run continuously for too a time, so be careful.
- LCPL / RCPL: the rotator will move to either the horizontal or vertical position, and the camera will capture images of a single handedness with a high framerate. As there is no rotator delay, the live view is much more responsive, so these modes are good for calibrating the system before taking images.
- Pause: both the rotator and camera will pause and the picture will be static. Useful if you have an image you want to examine or take a photo of.

## Calibration:
Pressing the "Calibrate" button will open a sub-menu with a variety of useful calibration options:
- RPS Correction: remove any samples in the beam path and set up your source to be a Reference Polarization State i.e a state with a 50:50 mix of LCPL and RCPL and where each intensity reading is just barely saturated. Then enter '1' in both forms and press submit then a correction mask will be generated which adjusts any spots that aren't of value 1. This correction then persists, so will apply when imaging a sample. This is intended to correct errors in the setup like optical abberations.
- Spatial Calibration: 

## Overlays:


## Source code:

## Troubleshooting:
