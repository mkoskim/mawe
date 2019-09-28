###############################################################################
#
# Error management
#
###############################################################################

import sys

def log(*msg): print(*msg)

def ERROR(*msg): raise Exception(*msg)

def ERRORIF(cond, *msg):
    if(cond): ERROR(*msg)

