###############################################################################
#
# MAWE Document Format
#
###############################################################################

import xml.etree.ElementTree as ET
from tools.error import *

#------------------------------------------------------------------------------

class FormatError(Exception):

    def __init__(self, *msg):
        super(FormatError, self).__init__(*msg)
        
#------------------------------------------------------------------------------

class Document:

    def __init__(self):
        pass

#------------------------------------------------------------------------------
# Adding tails to elements to make files looking prettier
#------------------------------------------------------------------------------

def prettyFormat(elem, level = 0):
    childs = list(elem)
    if len(childs) != 0:
        s = "\n" + "    " * (level+1)
        if elem.text == None:
            elem.text = s
        else:
            elem.text = string.strip(elem.text) + s
        
        for child in elem:
            prettyFormat(child, level + 1)
    elem.tail = "\n" + "    " * level
            
#------------------------------------------------------------------------------

