###############################################################################
#
# Project
#
###############################################################################

import os
from project.Document import ET

###############################################################################
#
# File loaders. As a result, we need correctly formed XML element tree.
#
###############################################################################

class Project:

    def __init__(self, filename, drive):
	    self.filename = filename
	    self.drive = drive

    @staticmethod
    def MoeOrMawe(filename, dirname, drive):
        fullname = os.path.join(drive, dirname, filename)
        tree = ET.parse(fullname)
        root = tree.getroot()
        
        if root.tag != "story":
            print("Not a moe/mawe file")
            return None
            
        return fullname
    
    Mawe = MoeOrMawe
    Moe  = MoeOrMawe

    @staticmethod
    def LaTeX(filename, dirname, drive):
        fullname = os.path.join(drive, dirname, filename)
        return fullname

#------------------------------------------------------------------------------
#
# Let's think. There are several different types of projects:
# 
# .mawe: Native format. Files can be loaded and stored without loosing any
# information.
#
# IMPORT formats: These formats can be imported, and are listed in project
# manager. These are mainly aimed
# to load projects and convert them to MAWE format. Conversion includes
# some manual work, so it can not be automatized.
#
# .moe: MOE projects can be imported, but generally we don't want to save
# documents in this format. Instead, we want to convert them to MAWE files.
# MOE editor most probably gets MAWE file importer at some point, and
# probably it starts saving files in MAWE format at some point.
#
# For .moe projects, give writer an option to convert the project type
# (save .mawe file and delete .moe).
#
# .txt, .latex: There are several formats that we like to get
# imported for conversion.
#
# EXTERNAL formats: Then there are projects we want to link to our own work,
# but which can only be edited by external editors. That means, that MAWE
# does not have import feature for these files. Such formats are e.g.
#
# .http: Links to web pages.
#
# .googledoc: These are implemented as HTTP links, but in principle these
# are document formats of their own. At some point we might like to have
# some sort of special support for gdocs.
#
# .doc, .sxw, .docx, .odt: Generic document formats for external editors.
#
# .rtf: Even thought we might have RTF import at some point, we still might
# want to edit RTF files with external editors.
#
#------------------------------------------------------------------------------
#
# EXPORT formats:
#
# .rtf: RTF is generally used format to exchange stories between people.
#
# .epub, .pdf, .html: These are publishing formats.
#
#------------------------------------------------------------------------------

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

