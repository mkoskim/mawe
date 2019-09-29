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

    def __init__(self, project, tree = None):
        assert project.format == "mawe"
        self.project = project
        if tree is None:
            tree = ET.ElementTree(ET.fromstring(self.emptydoc))
        self.tree = tree
        self.root = tree.getroot()

    def __str__(self):
        return str(ET.tostring(self.root))

    def saveas(self, filename):
        self.tree.write(filename)

    emptydoc = """
<story format="mawe">
    <body>
        <head>
        </head>
        <part>
        </part>
    </body>
</story>
    """    
