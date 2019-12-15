###############################################################################
#
# Tools for configuration management
#
###############################################################################

import os, json

config = None

defaults = {
    "ConfigVersion": 1,
    "Window": {
        "Size": { "X": 800, "Y": 900 },
    },
    "DocView": {
        "Pane": -1
    },
    "OpenView": {
        "Directory": os.getcwd(),
    },
    "DocNotebook": {
        "Files": []
    },
    "ProjectDir": "",
}

# This does not work for system wide installations, but for user-only
# installations it is just fine.

filename = os.path.join(os.path.dirname(__file__), "../local/mawe.json")

#------------------------------------------------------------------------------

def config_load():
    global config
    
    try:
        config = _migrate(json.load(open(filename)))
    except:
        config = defaults

def config_save():
    global config

    json.dump(config, open(filename, "w"), indent = 4)

#------------------------------------------------------------------------------

def _migrate(config):
    global defaults

    def get_default(key): config[key] = defaults[key]

    if "OpenView" not in config:    get_default("OpenView")
    if "DocNotebook" not in config: get_default("DocNotebook")
    if "ProjectDir" not in config:  get_default("ProjectDir")
    return config

#------------------------------------------------------------------------------

config_load()

