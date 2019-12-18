###############################################################################
#
# Project
#
###############################################################################

import os, re
from project.Document import ET, FormatError, Document
from tools import *

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
            content = readfile(fullname)
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
        self.title    = root.find("./body/head/title").text
        self.subtitle = root.find("./body/head/subtitle").text
        self.author   = root.find("./body/head/author").text
        self.status   = root.find("./body/head/status").text
        self.deadline = root.find("./body/head/deadline").text
        self.year     = root.find("./body/head/year").text
        self.editor   = "mawe"

        try:
            self.words    = (
                int(root.find("./body/head/words/text").text),
                int(root.find("./body/head/words/comments").text),
                int(root.find("./body/head/words/missing").text),
            )
        except:
            self.words = (0, 0, 0)

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

        self.title    = root.find("./TitleItem/title").text
        self.subtitle = root.find("./TitleItem/subtitle").text
        self.author   = root.find("./TitleItem/author").text
        self.status   = root.find("./TitleItem/status").text
        self.deadline = root.find("./TitleItem/deadline").text
        self.year     = root.find("./TitleItem/year").text
        self.words    = (int(root.find("./TitleItem").get("words")), 0, 0)
        self.editor   = "moe"
        
    reDblEnter  = re.compile(r"\n+")
    reSeparator = re.compile(r"\n\s*\-\s*\-\s*\-[\s\-]*\n")

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
            if visible: return element.get("included") == "True"
            return False
        
        def lines2tags(scene, tag, *elements):
            for element in elements:
                text = element.text
                if not text: return ""
                text = re.sub(Moe.reDblEnter, "\n", text).strip()
                text = re.sub(Moe.reSeparator, "\n\n", text)
                for line in text.split("\n"):
                    ET.SubElement(scene, tag).text = line

        def parsescene(element, visible = True):
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

        def parsegroup(element, visible = True):
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
                if   child.tag == "SceneItem": parsescene(child, visible)
                elif child.tag == "GroupItem": parsegroup(child, visible)
                else: log("%s<group>: Unknown child '%s'" % (self.fullname, child.tag))
        
        def parsetitle(element):
            head = mawe.find("./body/head")
            notehead = mawe.find("./notes/head")
            for child in list(element):
                if   child.tag == "title":      head.find("title").text = child.text
                elif child.tag == "subtitle":   head.find("subtitle").text = child.text
                elif child.tag == "author":     head.find("author").text = child.text
                elif child.tag == "deadline":   head.find("deadline").text = child.text
                elif child.tag == "status":     head.find("status").text = child.text
                elif child.tag == "year":       head.find("year").text = child.text
                elif child.tag == "translated": ET.SubElement(head, "translated").text = child.text
                elif child.tag == "published":  ET.SubElement(head, "published").text = child.text
                elif child.tag == "publisher":  ET.SubElement(head, "publisher").text = child.text
                elif child.tag == "synopsis":   ET.SubElement(head, "covertext").text = child.text
                elif child.tag == "version":    pass
                elif child.tag == "website":    pass
                elif child.tag == "coverpage":  pass
                else: log("%s<title>: Unknown child '%s'" % (self.fullname, child.tag))
        
        #----------------------------------------------------------------------
        
        for child in list(root):
            if   child.tag == "TitleItem": parsetitle(child)
            elif child.tag == "SceneItem": parsescene(child)
            elif child.tag == "GroupItem": parsegroup(child)
            elif child.tag == "settings":  pass # Safe to ignore, settings were moved to .moerc
            else: log("%s: <story>: Unknown child '%s'" % (self.fullname, child.tag))

        return Document(tree = mawe, origin = self.fullname)

###############################################################################
#
# NOTE: These are not working!
#
###############################################################################

class Text(Base):

    def __init__(self, filename, format = "text"):
        super(Text, self).__init__(filename, format)
        self.title = os.path.basename(self.fullname)

    def load(self):
        lines = readfile(self.fullname)
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

        #log(self.fullname)
        content = readfile(self.fullname)

        content = LaTeX.reTEXcomment.sub("", content)
        docinfo = LaTeX.reTEXExtractHeader.search(content)

        if not docinfo:
            docinfo = LaTeX.reTEXExtractResearchHeader.search(content)
            if not docinfo: return

        self.title    = docinfo.group("title")
        self.subtitle = docinfo.group("subtitle")
        self.author   = docinfo.group("author")
        self.status   = docinfo.group("status")
        self.deadline = "-"
        self.year     = docinfo.group("year")
        self.words    = (0, 0, 0)
        self.editor   = "LaTeX"

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

