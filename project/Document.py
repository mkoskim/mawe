###############################################################################
#
# MAWE Document Format
#
###############################################################################

import xml.etree.ElementTree as ET
from tools.error import *
import os
import uuid

#------------------------------------------------------------------------------
#
# Some plans. We need a dictionary holding Documents, and they can be
# retrieved by UUID (so that you know if you have one open already).
# Documents need to track the buffers - which buffers are connected to
# what XML element, so that when saving, you can go and grab the
# buffers.
#
# When closing, we need to go through dirty buffers and save them to disk.
#
# REMEMBER: When we add views to other doc buffers, we need to keep track
# where there are open views.
#
#------------------------------------------------------------------------------

class FormatError(Exception):

    def __init__(self, *msg):
        super(FormatError, self).__init__(*msg)
        
#------------------------------------------------------------------------------

class Document:

    def __init__(self, filename = None, tree = None):

        # TODO: Track somehow if the file was really loaded from filename,
        # or if it was created when converting files. If Document was created
        # by conversion, still ask filename when attempting to save (although
        # we have here suggestion for it)
        
        self.filename = filename

        if tree is None:
            if self.filename:
                tree = ET.parse(self.filename)
            else:
                tree = Document.empty()

        self.tree = tree
        self.root = tree.getroot()
        self.name = self.root.find("./body/head/title").text

        # If doc does not yet have UUID, generate one: docs converted
        # from other formats lack one.
        
        if not "uuid" in self.root.attrib:
            uid = str(uuid.uuid4())
            self.root.set("uuid", uid)
            print("New UUID", uid)
        self.uuid = self.root.get("uuid")
        print(self.name, self.uuid)

    @staticmethod
    def empty():
        return ET.parse(os.path.join(os.path.dirname(__file__), "Empty.mawe"))

    def __str__(self):
        return "<Document %s @ %s>" % (self.name, self.filename)

    #--------------------------------------------------------------------------
    # Try to save in pretty format, it helps debugging possible problems. We
    # do this by modifying the tag tails.
    #--------------------------------------------------------------------------

    def saveas(self, filename):
        print("Saving:", filename)

        self.root.find("./body/head").insert(0, ET.Comment(Document.comment_head % self.name))
        self.root.find("./body/head").append(ET.Comment(Document.comment_hr))
        self.root.find("./body").append(ET.Comment(Document.comment_notes))
        self.root.find("./notes").append(ET.Comment(Document.comment_versions))

        Document.prettyFormat(self.root)
        self.tree.write(filename, encoding="utf-8")

    @staticmethod
    def prettyFormat(root, level = 0):
        for child in root.iter():
            if child.text: child.text = child.text.strip()
            if len(list(child)):
                if child.text: child.text = "\n" + child.text
                else: child.text = "\n"
            child.tail = "\n"

    comment_head = """/
===============================================================================

Story: %s

===============================================================================
/"""

    comment_hr = """/
===============================================================================
/"""

    comment_notes = """/
===============================================================================

Notes

===============================================================================
/"""

    comment_versions = """/
===============================================================================

Versions

===============================================================================
/"""
