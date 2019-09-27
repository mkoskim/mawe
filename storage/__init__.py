###############################################################################
#
# Handling storage - load, save, import, export
#
###############################################################################

import sys
#import ProjectManager

#------------------------------------------------------------------------------
# XML parser; use C parser, if available.
#------------------------------------------------------------------------------

try:
    import cElementTree as ET
    class ExpatError(Exception): pass
    print("Using: cElementTree", file=sys.stderr)
except ImportError:
    import xml.etree.ElementTree as ET
    from xml.parsers.expat import ExpatError 
    print("Using: xml.etree.ElementTree", file=sys.stderr)

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
            

