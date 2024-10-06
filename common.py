from pathlib import Path
from logging import Logger, getLogger
from json import dump as json_dump, load as json_load

def ensure_path_exists(path : str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def save_config(config : str, name : str) -> None:
    with open("config/" + name.strip("_") + ".conf", "w", encoding="utf_8") as config_file:
	    json_dump(config, config_file, indent=4)
    
def load_config(name : str) -> dict:
    with open("config/" + name.strip("_") + ".conf", "r", encoding="utf_8") as config_file:
	    return json_load(config_file)
    
def get_logger(name : str, level : str) -> Logger:
    log : Logger = getLogger(name)
    log.setLevel(level)
    return log