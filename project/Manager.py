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

projects = {}

def mount(*files):
    requested = []

    for filename in files:
	    if os.path.isdir(filename):
		    _scan(filename)
	    elif os.path.isfile(filename):
		    requested.append(Project.open(os.getcwd(), os.path.abspath(filename), force = True))
	    else:
		    ERROR("%s: Not a file/folder." % filename)

    return requested

#------------------------------------------------------------------------------

def _scan(drive):
    print("Scanning:", drive)

    scanned = []
    links   = []
    
    def _walk(*dirs):
        subdirs = []
        for dir in dirs:
            scanned.append(dir)

            rpath = os.path.relpath(dir, drive)
            
            for file in os.listdir(dir):
                path = os.path.join(dir, file)
                if os.path.islink(path):
	                links.append(path)
                elif os.path.isfile(path):
	                try:
	                    if path not in projects:
	                        project = Project.open(drive, os.path.join(rpath, file))
	                        if project: projects[project.fullname] = project
	                except Exception as e:
	                    log(e.__class__.__name__ + ":", str(e))
	                    pass
                elif os.path.isdir(path):
	                if file not in [".moerc", "epub", "version", "versions"]:
		                subdirs.append(path)

        if subdirs: _walk(*subdirs)

    _walk(drive)

    #for path in links: print("Link:", path)
    #for project in projects.keys(): print("Project:", str(project))
    #for path in scanned:  print("Scanned:", path)
    #for path in pruned:   print("Pruned.:", path)

    print("Scanned.: %d" % (len(scanned)))
    print("Projects: %d" % (len(projects)))

