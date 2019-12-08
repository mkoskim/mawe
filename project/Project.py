###############################################################################
#
# Project
#
###############################################################################

import os, re
from project.Document import ET, FormatError, Document
import tools

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
                return Mawe(drive, path, root)
            elif format == "moe":
                return Moe(drive, path, root)

            raise FormatError("%s: Unknown story format '%s'" % (fullname, format))
                
        elif filename == "Makefile":
            content = tools.readfile(fullname)
            mainfile = LaTeX.reMainFile.search(content)
            if not mainfile:
                mainfile = LaTeX.reDocName.search(content)
                if not mainfile: return None
            mainfile = mainfile.group("filename")

            mainfile, ext = os.path.splitext(mainfile)
            if os.path.isfile(os.path.join(dirname, mainfile) + ".moe"): return
            if os.path.isfile(os.path.join(dirname, mainfile) + ".mawe"): return
            
            return LaTeX(
                drive,
                os.path.join(os.path.relpath(dirname, drive), mainfile + ".tex")
            )

        return None
        #return Text(drive, path)

#------------------------------------------------------------------------------

class Base:
    def __init__(self, drive, path, format = None):
        self.format   = format
        self.drive    = drive
        self.path     = path

        if drive and path:
            self.fullname = os.path.join(drive, path)
        else:
            self.fullname = None
        
    def __str__(self):
        if self.fullname: return self.fullname
        return "<New Project>"

#--------------------------------------------------------------------------

class Mawe(Base):

    def __init__(self, drive, path, root = None):
        super(Mawe, self).__init__(drive, path, "mawe")

    def load(self):
        return ET.parse(self.fullname)

#--------------------------------------------------------------------------

class Moe(Base):

    def __init__(self, drive, path, root):
        super(Moe, self).__init__(drive, path, "moe")

    def load(self):
        if not self.fullname: return

        root = ET.parse(self.fullname).getroot()

        reDblEnter = re.compile("\n+")

        if root.tag != "story":
            raise FormatError("%s: Not a valid moe file." % self.fullname)

        # TODO: Parse title
        # TODO: Parse non-visible parts

        def gettext(element, prefix = ""):
            text = element.text
            if not text: return ""
            text = re.sub(reDblEnter, "\n", text).strip()
            if prefix:
                text = text.split("\n")
                text = (prefix + "\n").join(text)
            return prefix + text + "\n"

        def parsescene(element):
            if element.attrib["included"] != "True": return ""

            name     = "## " + element.find("name").text + "\n"
            synopsis = gettext(element.find("synopsis"), "<<")
            comments = gettext(element.find("comments"), "//")
            content  = gettext(element.find("content"))
            
            return name + synopsis + comments + content + "\n"

        def parsegroup(element):
            if element.attrib["included"] != "True": return ""

            text = "## Group: " + element.find("name").text + "\n"

            for child in list(element.find("childs")):
                if   child.tag == "SceneItem": text = text + parsescene(child)
                elif child.tag == "GroupItem": text = text + parsegroup(child)
                else: log("%s: <story>: Unknown child '%s'" % (self.fullname, child.tag))
            return text
        
        text = ""
        for child in list(root):
            if   child.tag == "TitleItem": continue
            elif child.tag == "SceneItem": text = text + parsescene(child)
            elif child.tag == "GroupItem": text = text + parsegroup(child)
            else: log("%s: <story>: Unknown child '%s'" % (self.fullname, child.tag))
        return text

#--------------------------------------------------------------------------

class Text(Base):

    def __init__(self, drive, path):
        super(Text, self).__init__(drive, path, "latex")

    def load(self):
        return tools.readfile(self.fullname)
    
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
        super(LaTeX, self).__init__(drive, path, "latex")

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

    def load(self):
        # Create new mawe project, and create mawe tree from tex sources
        pass

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

