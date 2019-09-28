###############################################################################
#
# Project
#
###############################################################################

import os, re
from project.Document import ET, FormatError
import tools
#from tools.error import *

###############################################################################
#
# File loaders. As a result, we need correctly formed XML element tree.
#
###############################################################################

#------------------------------------------------------------------------------

class Project:

    #--------------------------------------------------------------------------

    @staticmethod
    def open(drive, path):
        fullname = os.path.join(drive, path)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        
        if os.path.splitext(path)[1] in [".moe", ".mawe"]:
            tree = ET.parse(fullname)
            root = tree.getroot()
            
            if root.tag != "story":
                raise FormatError("%s: Not a moe/mawe file." % fullname)
            
            format = root.get("format", "moe")
            if format == "mawe":
                return Project.Mawe(drive, path, ET)
            elif format == "moe":
                return Project.Moe(drive, path, ET)

            raise FormatError("%s: Unknown story format '%s'" % (fullname, format))
                
        elif filename == "Makefile":
            content = tools.readfile(fullname)
            mainfile = Project.LaTeX.reMainFile.search(content)
            if not mainfile:
                mainfile = Project.LaTeX.reDocName.search(content)
                if not mainfile: return None
            mainfile = mainfile.group("filename")

            mainfile, ext = os.path.splitext(mainfile)
            if os.path.isfile(os.path.join(dirname, mainfile) + ".moe"): return
            if os.path.isfile(os.path.join(dirname, mainfile) + ".mawe"): return
            
            return Project.LaTeX(
                drive,
                os.path.join(os.path.relpath(dirname, drive), mainfile + ".tex")
            )

        return None

    #--------------------------------------------------------------------------

    class Base:
        def __init__(self, drive, path, format = None):
            self.drive    = drive
            self.path     = path
            self.fullname = os.path.join(drive, path)
            self.format   = format
            
        def __str__(self): return self.fullname

    #--------------------------------------------------------------------------

    class Mawe(Base):

	    def __init__(self, drive, path, ET):
		    super(Project.Mawe, self).__init__(drive, path, "mawe")

    #--------------------------------------------------------------------------

    class Moe(Base):

	    def __init__(self, drive, path, ET):
		    super(Project.Moe, self).__init__(drive, path, "moe")

    #--------------------------------------------------------------------------

    class LaTeX(Base):

        reMainFile = re.compile(r"^MAINFILE=(?P<filename>.*?)$", re.MULTILINE|re.UNICODE)
        reDocName  = re.compile(r"^DOCNAME=(?P<filename>.*?)$", re.MULTILINE|re.UNICODE)

        reTEXcomment = re.compile("\%(.*?)$", re.MULTILINE|re.UNICODE)
        reTEXExtractHeader = re.compile(
            r"\\(?P<type>shortstory|longstory|novel|collection)" +
            r"\s*\{(?P<title>.*?)\}" +
            r"\s*\{(?P<subtitle>.*?)\}" +
            r"\s*\{(?P<status>.*?)\}" +
            r"\s*\{(?P<author>.*?)\}" +
            r"\s*\{(?P<website>.*?)\}" +
            r"\s*\{(?P<year>.*?)\}", re.MULTILINE|re.DOTALL|re.UNICODE
        )

        reTEXExtractResearchHeader = re.compile(
            r"\\(?P<type>research)" +
            r"\s*\{(?P<imag_authors>.*?)\}" +
            r"\s*\{(?P<title>.*?)\}" +
            r"\s*\{(?P<subtitle>.*?)\}" +
            r"\s*\{(?P<imag_published>.*?)\}" +
            r"\s*\{(?P<status>.*?)\}" +
            r"\s*\{(?P<author>.*?)\}" +
            r"\s*\{(?P<website>.*?)\}" +
            r"\s*\{(?P<year>.*?)\}", re.MULTILINE|re.DOTALL|re.UNICODE
        )

        def __init__(self, drive, path):
            super(Project.LaTeX, self).__init__(drive, path, "latex")

            #tools.log(self.fullname)
            content = tools.readfile(self.fullname)

            content = self.reTEXcomment.sub("", content)
            docinfo = self.reTEXExtractHeader.search(content)

            if not docinfo:
                docinfo = self.reTEXExtractResearchHeader.search(content)
                if not docinfo: return

            # wc = extractStats(dirname)

            #year = docinfo.group("year")
            #if year == "": year = "-"

            #return mainfile, Project(
            #    "LaTeX",
            #    docinfo.group("type"),
            #    docinfo.group("title"),
            #    docinfo.group("subtitle"),
            #    year,
            #    docinfo.group("status"),
            #    "-",
            #    wc
            #)

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

