from logging import Logger, Formatter, root as rootLogger, StreamHandler, DEBUG
from logging.handlers import RotatingFileHandler
from importlib import import_module
from common import load_config, get_logger, ensure_path_exists
from bottle import route, static_file, run as bottle_run    # type: ignore

config : dict = load_config(__name__)
log : Logger = get_logger(__name__.strip("_"), "DEBUG")

log_format = Formatter(fmt="%(asctime)s %(name)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
rootLogger.setLevel(DEBUG)

if (config["logToConsole"]):
    stream_handler = StreamHandler()
    stream_handler.setFormatter(log_format)
    stream_handler.setLevel(config["logLevelConsole"])
    rootLogger.addHandler(stream_handler)
if (config["logToFile"]):
    ensure_path_exists(config["logfile"])
    file_handler = RotatingFileHandler(filename=config["logfile"], maxBytes=(1024 * 1024 * 10), backupCount=5, encoding="utf-8")
    file_handler.setFormatter(log_format)
    file_handler.setLevel(config["logLevelFile"])
    rootLogger.addHandler(file_handler)

for module in config["modules"]:
    if(config["modules"][module]):
        log.info(f"Loading module {module}")
        imported_module = import_module(module)
        imported_module.init()
        log.info(f"Finished loading module {module}")

@route("/favicon.ico")
def favicon() -> str:
    return static_file("favicon-32x32.png", "./static")

bottle_run(server="gunicorn", host=config["hostname"], port=config["port"], keyfile=config["keyfile"], certfile=config["certfile"], workers=10, worker_class="gthread", threads=10)
