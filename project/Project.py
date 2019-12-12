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
#
###############################################################################

class Project:

    @staticmethod
    def open(fullname, validonly = False):
        fullname = os.path.abspath(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        
        if os.path.splitext(fullname)[1] in [".moe", ".mawe"]:
            tree = ET.parse(fullname)
            root = tree.getroot()
            
            if root.tag != "story":
                raise FormatError("%s: Not a moe/mawe file." % fullname)
            
            format = root.get("format", "moe")
            if format == "mawe":
                return Mawe(fullname, root)
            elif format == "moe":
                return Moe(fullname, root)

            raise FormatError("%s: Unknown story format '%s'" % (fullname, format))
                
        elif filename == "Makefile":
            content = tools.readfile(fullname)
            mainfile = LaTeX.reMainFile.search(content)
            if not mainfile:
                mainfile = LaTeX.reDocName.search(content)
                if not mainfile: return None
            mainfile = os.path.join(dirname, mainfile.group("filename"))

            mainfile, ext = os.path.splitext(mainfile)
            if os.path.isfile(mainfile + ".moe"): return
            if os.path.isfile(mainfile + ".mawe"): return
            
            return LaTeX(mainfile + ".tex")

        if validonly: return None
        return Text(fullname)

###############################################################################
#
# File loaders. As a result, we need correctly formed XML element tree.
#
###############################################################################

class Base:
    def __init__(self, filename, format = None):
        self.fullname = filename
        
    def __str__(self):
        if self.fullname: return self.fullname
        return "<New Project>"

###############################################################################

class Mawe(Base):

    def __init__(self, filename, root = None):
        super(Mawe, self).__init__(filename, "mawe")
        self.name = root.find("./body/head/title").text

    def load(self):
        if self.fullname: return Document(self.fullname)

###############################################################################
#
# MOE loader: This is very coarse conversion. Sadly, moe gives absolute
# freedom to use nested groups, and I (*blush*) have used that to modify the
# outlook of the exported draft. Here we just divide content to two part:
# visible ones go to draft, invisible ones go to notes, even if they are
# in fact comment blocks between scenes.
#
###############################################################################

class Moe(Base):

    def __init__(self, filename, root):
        super(Moe, self).__init__(filename, "moe")

        self.name = root.find("./TitleItem/title").text
        
    reDblEnter  = re.compile("\n+")
    reSeparator = re.compile("\n\s*\-\s*\-\s*\-[\s\-]*\n")

    def load(self):
        if not self.fullname: return

        root = ET.parse(self.fullname).getroot()

        if root.tag != "story" or root.get("format", "moe") != "moe":
            raise FormatError("%s: Not a valid moe file." % self.fullname)

        #----------------------------------------------------------------------
        
        mawe = Document.empty(root.find("./TitleItem/title").text)

        def create_scene(element, visible):
            if visible:
                return ET.SubElement(mawe.find("./body/part"), "scene")
            else:
                return ET.SubElement(mawe.find("./notes/part"), "scene")

        def get_visible(element, visible):
            if not visible is False: return element.get("included") == "True"
            return False
        
        def lines2tags(scene, tag, *elements):
            for element in elements:
                text = element.text
                if not text: return ""
                text = re.sub(Moe.reDblEnter, "\n", text).strip()
                text = re.sub(Moe.reSeparator, "\n\n", text)
                for line in text.split("\n"):
                    ET.SubElement(scene, tag).text = line

        def parsescene(element, visible = None):
            visible = get_visible(element, visible)
            scene   = create_scene(element, visible)
            scene.set("name", "%s" % element.find("./name").text)
            
            lines2tags(scene, "synopsis",
                *element.findall("synopsis"),
                *element.findall("description"),
            )
            lines2tags(scene, "comment",
                *element.findall("comments"),
                *element.findall("sketch"),
                *element.findall("conflict"),
            )
            lines2tags(scene, "p", *element.findall("content"))

        def parsegroup(element, visible = None):
            visible = get_visible(element, visible)
            scene   = create_scene(element, visible)
            
            scene.set("name", "** %s" % element.find("./name").text)

            lines2tags(scene, "synopsis",
                *element.findall("synopsis"),
                *element.findall("description"),
            )
            lines2tags(scene, "comment",
                *element.findall("comments"),
                *element.findall("sketch"),
                *element.findall("conflict"),
            )

            for child in list(element.find("childs")):
                if   child.tag == "SceneItem": parsescene(child)
                elif child.tag == "GroupItem": parsegroup(child)
                else: tools.log("%s<group>: Unknown child '%s'" % (self.fullname, child.tag))
        
        def parsetitle(element):
            for child in list(element):
                if   child.tag == "title": mawe.find("./body/head/title").text = child.text
                else: tools.log("%s<title>: Unknown child '%s'" % (self.fullname, child.tag))
        
        #----------------------------------------------------------------------
        
        for child in list(root):
            if   child.tag == "TitleItem": parsetitle(child)
            elif child.tag == "SceneItem": parsescene(child)
            elif child.tag == "GroupItem": parsegroup(child)
            elif child.tag == "settings":  pass # Safe to ignore, settings were moved to .moerc
            else: tools.log("%s: <story>: Unknown child '%s'" % (self.fullname, child.tag))

        return Document(tree = mawe, origin = self.fullname)

###############################################################################
#
# NOTE: These are not working!
#
###############################################################################

class Text(Base):

    def __init__(self, filename, format = "text"):
        super(Text, self).__init__(filename, format)
        self.name = os.path.basename(self.fullname)

    def load(self):
        lines = tools.readfile(self.fullname)
        lines = lines.split("\n")

        mawe  = Document.empty(os.path.basename(self.fullname))
        scene = ET.SubElement(mawe.find("./body/part"), "scene")

        for line in lines:
            paragraph = ET.SubElement(scene, "p")
            paragraph.text = line

        return Document(
            tree = mawe,
            origin = self.fullname
        )

###############################################################################

class LaTeX(Text):

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

    def __init__(self, filename):
        super(LaTeX, self).__init__(filename, "latex")

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

