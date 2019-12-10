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
        return str(ET.tostring(self.root))

    def saveas(self, filename):
        self.tree.write(filename)

