###############################################################################
#
# Project Manager
#
###############################################################################

import os, re

from project.Project import Project
from tools.error import *

#------------------------------------------------------------------------------
#
# Some planned features:
#
# - Keep track of recently opened files
#
# - Make work lists: Possibly keep track of opened files and such, so
#   that when starting to work with work list, it opens the same files
#
# - Load files at startup so that you can continue where you left
#
# - Feature: Scan folders for other types (.txt, .rtf, .doc) and choose
#   projects from those. That is, we need a list of files that where
#   manually added as projects by user.
#
#------------------------------------------------------------------------------

def mount(*files):
	for filename in files:
		if os.path.isdir(filename):
			_scandir(filename)
		elif os.path.isfile(filename):
			Project.open(os.getcwd(), filename)
		else:
			ERROR("%s: Not a file/folder." % filename)

#------------------------------------------------------------------------------

def _scandir(drive):
    print("Scanning:", drive)

    projects = []
    scanned = []
    pruned  = []
    links   = []
    
    def _scan(dir):
        scanned.append(dir)

        rpath = os.path.relpath(dir, drive)
        subdirs = []
        
        for f in os.listdir(dir):
            path = os.path.join(dir, f)
            if os.path.islink(path):
	            links.append(path)
            elif os.path.isfile(path):
	            try:
	                project = Project.open(drive, os.path.join(rpath, f))
	                if project: projects.append(project)
	            except Exception as e:
	                log(e.__class__.__name__ + ":", str(e))
	                pass
            elif os.path.isdir(path):
	            if f in ["defaults", "moe", ".moerc", "figures"]:
		            pruned.append(path)
	            elif f in ["epub", "version", "versions"]:
		            pass
	            else:
		            subdirs.append(path)

        return subdirs

    def _walk(*dirs):
        subdirs = []
        for dir in dirs: subdirs = subdirs + _scan(dir)
        if subdirs: _walk(*subdirs)

    _walk(drive)

    #for path in links: print("Link:", path)
    for project in projects: print("Project:", str(project))
    #for path in scanned:  print("Scanned:", path)
    #for path in pruned:   print("Pruned.:", path)

    print("Projects: %d" % (len(projects)))
    print("Scanned/pruned: %d / %d" % (len(scanned), len(pruned)))

