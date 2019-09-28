###############################################################################
#
# Project Manager
#
###############################################################################

import os, re

from project.Project import Project

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
#------------------------------------------------------------------------------

def mount(*files):
	for filename in files:
		if os.path.isdir(filename):
			_scandir(filename)
		elif os.path.isfile(filename):
			_addproject(filename)
		else:
			print("%s: Not a file/folder." % filename)

#------------------------------------------------------------------------------

reMawe  = re.compile(r".*\.mawe$")
reMoe   = re.compile(r".*\.moe$")
reLaTeX = re.compile(r"^Makefile$")

def _addproject(filename, dirname = "", drive = ""):
    if reMawe.match(filename):
	    return Project.Mawe(filename, dirname, drive), False
    elif reMoe.match(filename):
	    return Project.Moe(filename, dirname, drive), False
    elif reLaTeX.match(filename):
	    return Project.LaTeX(filename, dirname, drive), True
    else:
        return None, False

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
        isLeaf = False
        
        for f in os.listdir(dir):
            path = os.path.join(dir, f)
            if os.path.islink(path):
	            links.append(path)
            elif os.path.isfile(path):
	            project, leaf = _addproject(f, rpath, drive)
	            if project: projects.append(project)
	            isLeaf = isLeaf or leaf
            elif os.path.isdir(path):
	            if f in ["defaults", "moe", ".moerc", "figures"]:
		            pruned.append(path)
	            elif f in ["epub", "version", "versions"]:
		            pass
	            else:
		            subdirs.append(path)

        #if isLeaf: return []
        return subdirs

    def _walk(*dirs):
        subdirs = []
        for dir in dirs: subdirs = subdirs + _scan(dir)
        if subdirs: _walk(*subdirs)

    _walk(drive)

    #for path in links: print("Link:", path)
    #for path in projects: print("Project:", path)
    #for path in scanned:  print("Scanned:", path)
    #for path in pruned:   print("Pruned.:", path)

    print("Projects: %d" % (len(projects)))
    print("Scanned/pruned: %d / %d" % (len(scanned), len(pruned)))

