###############################################################################
#
# Tools for configuration management
#
###############################################################################

import json

config = None

defaults = {
    "ConfigVersion": 1,
    "Window": {
        "Size": { "X": 800, "Y": 900 },
    },
    "DocView": {
        "Pane": -1
    }
}

filename = "local/mawe.json"

def config_load():
    global config
    
    try:
        config = json.load(open(filename))
        # Do possible migration
    except:
        config = defaults

def config_save():
    #print("Saving config", filename)
    #print(json.dumps(config, indent = 4))
    json.dump(config, open(filename, "w"), indent = 4)

config_load()
#print(config)
#save_config()

