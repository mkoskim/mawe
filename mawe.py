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

#------------------------------------------------------------------------------
# Parse command line arguments
#------------------------------------------------------------------------------

import argparse

parser = argparse.ArgumentParser(
    description = "MAWE Advanced Writer's Editor"
)

parser.add_argument("file", help="File or folder", type=str, nargs="*")
parser.add_argument("--new", help="Open new document", action="store_true")

args = parser.parse_args()

#------------------------------------------------------------------------------

import project

workset = project.Manager.mount(*args.file)

#------------------------------------------------------------------------------

import gui

gui.run(workset, new = args.new)

