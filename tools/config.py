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
    }
}

filename = "local/mawe.json"

#------------------------------------------------------------------------------

def _migrate(config):
    if "OpenView" not in config:
        config["OpenView"] = defaults["OpenView"]
    return config

#------------------------------------------------------------------------------

def config_load():
    global config
    
    try:
        config = _migrate(json.load(open(filename)))
    except:
        config = defaults

config_load()

#------------------------------------------------------------------------------

def config_save():
    #print("Saving config", filename)
    #print(json.dumps(config, indent = 4))
    json.dump(config, open(filename, "w"), indent = 4)

