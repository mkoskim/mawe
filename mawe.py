#!/usr/bin/env python3
###############################################################################
###############################################################################
#
# MAWE - My/Markus' Advanced Writer's Editor
#
###############################################################################
###############################################################################

import sys

print("Python: %d.%d" % (sys.version_info.major, sys.version_info.minor))

if sys.version_info < (3, 5):
    print("You need Python 3.5 or higher.")
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
parser.add_argument("--export", help="Export document")

args = parser.parse_args()

#------------------------------------------------------------------------------
# Exporting files from command line
#------------------------------------------------------------------------------

if not args.export is None:
    ERRORIF(args.export != "rtf", "Invalid export format: %s " % args.export)
    for filename in args.file:
        from project import Project
        project = Project.open(filename, True)
        if project is None:
            log("Invalid project: %s" % filename)
            continue
        doc = project.load()
        doc.export()
    sys.exit()

#------------------------------------------------------------------------------
# Opening files
#------------------------------------------------------------------------------

import project

workset = project.Manager.mount(*args.file)

#------------------------------------------------------------------------------

import gui

gui.run(workset, new = args.new)

