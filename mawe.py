#!/usr/bin/env python3
###############################################################################
###############################################################################
#
# MAWE - My/Markus' Advanced Writer's Editor
#
###############################################################################
###############################################################################

import sys

if sys.version_info < (3, 0):
    print("You need Python 3.0 or higher.")
    sys.exit(-1)

from tools.error import *

###############################################################################
#
# Command line arguments
#
###############################################################################

import argparse

parser = argparse.ArgumentParser(
    description = "MAWE Advanced Writer's Editor"
)

parser.add_argument(
    "file", help="File or folder", 
    type=str, nargs="*",
    default=["test/test.mawe"]
)

args = parser.parse_args()

#------------------------------------------------------------------------------
# NOTE: At startup, first load files (command line or config), then start
# scanning directories at background.
#------------------------------------------------------------------------------

import project

project.Manager.mount(*args.file)

sys.exit(0)

###############################################################################
#
# Main
#
###############################################################################

import gui

root = gui.Tk()
root.title("mawesome")

def quit(event = None):
    print("Quit")
    global root
    root.destroy()

root.bind("<Control-q>", quit)
root.bind("<Alt-F4>", quit)

st = gui.SceneGroupEditor(root)
st.focus()

root.mainloop()

