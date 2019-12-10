###############################################################################
#
# MAWE Document Format
#
###############################################################################

import xml.etree.ElementTree as ET
from tools.error import *
import os

#------------------------------------------------------------------------------

class FormatError(Exception):

    def __init__(self, *msg):
        super(FormatError, self).__init__(*msg)
        
#------------------------------------------------------------------------------

class Document:

    def __init__(self, filename = None, tree = None):
        self.filename = filename
        if tree is None:
            if self.filename:
                tree = ET.parse(self.filename)
            else:
                tree = Document.empty()
        self.tree = tree
        self.root = tree.getroot()
        self.name = self.root.find("./body/head/title").text

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

