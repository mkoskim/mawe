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

    def __init__(self, filename = None, tree = None, origin = None):

        self.filename = filename
        self.origin   = origin

        # TODO: It would be great if we could have "loopback" device for
        # file save testing.
        
        if tree is None:
            if self.filename:
                tree = ET.parse(self.filename)
                self.origin = self.filename
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
        self.uuid = self.root.get("uuid")

    @staticmethod
    def empty(name = None):
        tree = ET.parse(os.path.join(os.path.dirname(__file__), "Empty.mawe"))
        tree.find("./body/head/title").text = name
        return tree

    def __str__(self):
        return "<Document %s @ %s>" % (self.name, self.filename)

    #--------------------------------------------------------------------------
    # Try to save in pretty format, it helps debugging possible problems. We
    # do this by modifying the tag tails.
    #--------------------------------------------------------------------------

    def saveas(self, filename):
        filename = "output.mawe"
        print("Saving:", filename)

        self.root.find("./body/head").insert(0, ET.Comment(Document.comment_head % self.name))
        self.root.find("./body/head").append(ET.Comment(Document.comment_hr))
        self.root.find("./body").append(ET.Comment(Document.comment_notes))
        self.root.find("./notes").append(ET.Comment(Document.comment_versions))

        Document.prettyFormat(self.root)

        # We do XML serialization first to string, so if there is errors in the
        # tree, we are not getting corrupted file.
        content = ET.tostring(self.root, encoding="utf-8")
        writefile(filename, content)
        #self.tree.write(filename, encoding="utf-8")

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
