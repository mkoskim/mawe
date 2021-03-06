###############################################################################
#
# Project Manager
#
###############################################################################

import os, re

from project.Project import Project
from tools.error import *
from tools.config import *

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
        if filename is None:
            pass
        elif os.path.isfile(filename):
            requested.append(os.path.abspath(filename))
        elif os.path.isdir(filename):
            # Directory tree is scanned when ProjectView is opened
            config["Directories"]["Projects"] = filename
            config["Directories"]["Open"] = filename
        else:
            ERROR("%s: Not a file/folder." % filename)

    return requested

#------------------------------------------------------------------------------

def _scan(drive):
    drive = os.path.abspath(drive)
    print("Scanning:", drive)
    
    global projects
    projects = {}
    scanned = []
    links   = []
    
    def _walk(*dirs):
        subdirs = []
        for dir in dirs:
            scanned.append(dir)

            for file in os.listdir(dir):
                path = os.path.join(dir, file)
                if os.path.islink(path):
	                links.append(path)
                elif os.path.isfile(path):
	                try:
	                    if path not in projects:
	                        project = Project.open(path, validonly = True)
	                        if project: projects[project.fullname] = project
	                except Exception as e:
	                    log_exception(e)
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

