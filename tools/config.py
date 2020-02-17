###############################################################################
#
# Tools for configuration management
#
###############################################################################

import os, json

config = None

defaults = {
    "ConfigVersion": 2,
    "Window": {
        "Size": { "X": 800, "Y": 900 },
    },
    "DocView": {
        "Pane": -1
    },
    "OpenView": {
    },
    "DocNotebook": {
        "Files": []
    },
    "Directories": {
        "Open": os.getcwd(),
        "Projects": None,
    },
    "TextView": {
        "family": "Times New Roman",
        "size": 12,
        "linespacing": 2,
    }
}

# This does not work for system wide installations, but for user-only
# installations it is just fine.

filename = os.path.join(os.path.dirname(__file__), "../local/mawe.json")

#------------------------------------------------------------------------------

def config_load():
    global config
    
    try:
        config = _migrate(json.load(open(filename)))
    except Exception as e:
        config = defaults
    #print(config)

def config_save():
    global config

    json.dump(config, open(filename, "w"), indent = 4)

#------------------------------------------------------------------------------

def _migrate(config):
    global defaults

    def get_default(key): config[key] = defaults[key]

    if "OpenView" not in config:    get_default("OpenView")
    if "DocNotebook" not in config: get_default("DocNotebook")
    if "TextView" not in config:    get_default("TextView")

    # Version 1 --> Version 2
    if config["ConfigVersion"] == 1:
        get_default("Directories")
        config["Directories"]["Open"] = config["OpenView"]["Directory"]
        del config["OpenView"]["Directory"]
        if "ProjectDir" in config:
            config["Directories"]["Projects"] = config["ProjectDir"]
            del config["ProjectDir"]
        config["ConfigVersion"] = 2

    return config

#------------------------------------------------------------------------------

config_load()

