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

parser.add_argument(
    "file", help="File or folder", 
    type=str, nargs="*"
)

args = parser.parse_args()

#------------------------------------------------------------------------------
# NOTE: At startup, first load files (command line or config), then start
# scanning directories at background.
#------------------------------------------------------------------------------

import project

#files = project.Manager.mount(*args.file)
#
#if files:
#    doc = files[0].load()
#else:
#    doc = project.Mawe(None, None).load()

#print(str(doc))
#doc.saveas("local/test.xml")

#sys.exit(0)

#------------------------------------------------------------------------------

import gui

gui.run(*args.file)

