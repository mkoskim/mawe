#!/usr/bin/env python3
###############################################################################
###############################################################################
#
# MAWE - My/Markus' Advanced Writer's Editor
#
###############################################################################
###############################################################################

#------------------------------------------------------------------------------

import sys

if sys.version_info < (3, 0):
    print("You need Python 3.0 or higher.")
    sys.exit(-1)

#------------------------------------------------------------------------------
#
# Objectives:
#
# - Integrate project manager to editor
# - Work with draft view
# - Work with multiple files
#
#------------------------------------------------------------------------------

###############################################################################
#
# Command line arguments
#
###############################################################################

import argparse

parser = argparse.ArgumentParser(
    description = "MAWE Advanced Writer's Editor"
)

parser.add_argument("file", type=str, nargs="*", help="File or folder", default=["test/test.mawe"])

args = parser.parse_args()

from storage import ProjectManager
print(args.file)
ProjectManager.mount(*args.file)

#sys.exit(0)

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

