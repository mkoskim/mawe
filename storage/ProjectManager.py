###############################################################################
#
# Project Manager
#
###############################################################################

import os
import re

def mount(*files):
	for filename in files:
		if os.path.isdir(filename):
			_scandir(filename)
		elif os.path.isfile(filename):
			_loadfile(filename)
		else:
			print("%s: Not a file/folder." % filename)

#------------------------------------------------------------------------------

def _scandir(drive):
	print("Scanning:", drive)

	scanned = []
	pruned  = []

	def _walk(*dirs):
		subdirs = []
		for dir in dirs:
			scanned.append(dir)
			rpath = os.path.relpath(dir, drive)
			#print(dir)
			files = os.listdir(dir)
			#print(files)
			for f in files:
				path = os.path.join(dir, f)
				if os.path.islink(path):
					print("Link:", path)
				elif os.path.isfile(path):
					_loadfile(f, rpath, drive)
				elif os.path.isdir(path):
					if f in ["defaults", "moe", ".moerc", "figures"]:
						pruned.append(path)
					elif f in ["epub", "version", "versions"]:
						pass
					else:
						subdirs.append(path)

		if subdirs: _walk(*subdirs)

	_walk(drive)

	for path in scanned: print("Scanned:", path)
	for path in pruned:  print("Pruned.:", path)

	print("Scanned/pruned: %d / %d" % (len(scanned), len(pruned)))

reMoeMawe   = re.compile(r".*\.((moe)|(mawe))$")
reLaTeX     = re.compile(r"^Makefile$")

def _loadfile(filename, dirname = "", drive = ""):
	if reMoeMawe.match(filename):
		_loadMoeMawe(filename, dirname, drive)
	elif reLaTeX.match(filename):
		_loadLaTeX(filename, dirname, drive)

def _loadMoeMawe(filename, dirname, drive):
	#print("Loading Moe/Mawe:", os.path.join(drive, dirname, filename))
	pass

def _loadLaTeX(filename, dirname, drive):
	#print("Loading LaTeX:", os.path.join(drive, dirname, filename))
	pass

###############################################################################
#
# Project
#
###############################################################################

class Project:

	def __init__(self, filename, drive):
		self.filename = filename
		self.drive = drive

#------------------------------------------------------------------------------

class ProjectMawe(Project):

	def __init__(self, filename, drive):
		super(ProjectMawe, self).__init__(filename, drive)

#------------------------------------------------------------------------------

class ProjectMoe(Project):

	def __init__(self, filename, drive):
		super(ProjectMoe, self).__init__(filename, drive)

#------------------------------------------------------------------------------

class ProjectLaTeX(Project):

	def __init__(self, filename, drive):
		super(ProjectMawe, self).__init__(filename, drive)

