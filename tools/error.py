###############################################################################
#
# Error management
#
###############################################################################

import sys

def log(*msg): print(*msg)

def log_exception(e): log(e.__class__.__name__ + ":", str(e))

def ERROR(*msg): raise Exception(*msg)

def ERRORIF(cond, *msg):
    if(cond): ERROR(*msg)

