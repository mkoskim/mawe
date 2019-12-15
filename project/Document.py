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
        
        # Inject comments
        name = self.root.find("./body/head/title").text
        self.root.find("./body").insert(0, ET.Comment(Document.comment_head % name))
        self.root.find("./body/head").append(ET.Comment(Document.comment_hr))
        self.root.find("./notes").insert(0, ET.Comment(Document.comment_notes))

        # If doc does not yet have UUID, generate one: docs converted
        # from other formats lack one.
        
        if not "uuid" in self.root.attrib:
            uid = str(uuid.uuid4())
            self.root.set("uuid", uid)
        self.uuid = self.root.get("uuid")

    @staticmethod
    def empty(title = None):
        tree = ET.parse(os.path.join(os.path.dirname(__file__), "Empty.mawe"))
        tree.find("./body/head/title").text = title
        return tree

    def create(self, key):
        path = key.split("/")
        parent = self.root.find("/".join(path[:-1]))
        return ET.SubElement(parent, path[-1])

    def replace(self, key, elem):
        path = key.split("/")
        parent = self.root.find("/".join(path[:-1]))
        child  = self.root.find(key)
        if child: parent.remove(child)
        return parent.append(elem)

    def __str__(self):
        return "<Document %s @ %s>" % (self.title, self.filename)

    #--------------------------------------------------------------------------
    # Try to save in pretty format, it helps debugging possible problems. We
    # do this by modifying the tag tails.
    #--------------------------------------------------------------------------

    def save(self, filename):
        #filename = "output.mawe"
        
        self.filename = filename
        self.origin   = filename

        #print("Saving:", filename)

        # Make saved file bit more readable
        def pretty(root, level = 0):
            for child in root.iter():
                if child.text: child.text = child.text.strip()
                if len(list(child)):
                    if child.text: child.text = "\n" + child.text
                    else: child.text = "\n"
                child.tail = "\n"

        pretty(self.root)

        # We do XML serialization first to string, so if there is errors in the
        # tree, we are not getting corrupted file.
        content = ET.tostring(self.root, encoding="utf-8")

        f = open(filename, "wb")
        f.write(content)
        f.close()

        #self.tree.write(filename, encoding="utf-8")

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
