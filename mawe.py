#!/usr/bin/env python3
###############################################################################
###############################################################################
#
# MAWE - My/Markus' Advanced Writer's Editor
#
###############################################################################
###############################################################################

import sys

if sys.version_info < (3, 5):
    print("You need Python 3.5 or higher.")
    sys.exit(-1)

print("Python: %d.%d" % (sys.version_info.major, sys.version_info.minor))

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
# Get config
#------------------------------------------------------------------------------

from tools.config import *
#config_load()

#------------------------------------------------------------------------------
# Exporting files from command line
#------------------------------------------------------------------------------

if not args.export is None:
    ERRORIF(args.export != "rtf", "Invalid export format: %s " % args.export)
    for filename in args.file:
        from project import *
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

#project.Manager.mount(config["ProjectDir"])
workset = project.Manager.mount(*args.file)

#------------------------------------------------------------------------------

import gui

gui.run(workset, new = args.new)

