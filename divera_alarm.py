from logging import Logger
from common import load_config, get_logger
from bottle import route, request, HTTPError, HTTPResponse, template	# type: ignore
from threading import Timer
from typing import Optional
from simplejson.errors import JSONDecodeError	# type: ignore
from datetime import datetime
import cec	# type: ignore

config : dict = load_config(__name__)
log : Logger = get_logger(__name__, config["logLevel"])
screen_shutoff_timer : Optional[Timer] = None
screen_previously_on: Optional[bool] = None
cec_controller : cec.ICECAdapter = None
last_action : str = "Started"
last_action_source : str = "Startup"
last_action_time : str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_cec() -> None:
	log.info("Initializing CEC controller")
	cec_config = cec.libcec_configuration()
	cec_config.strDeviceName = "Raspberry Pi"
	cec_config.bActivateSource = 0
	cec_config.deviceTypes.Add(cec.CEC_DEVICE_TYPE_PLAYBACK_DEVICE)
	cec_config.clientVersion = cec.LIBCEC_VERSION_CURRENT

	global cec_controller
	cec_controller = cec.ICECAdapter_Create(cec_config)
	log.debug("Successfully created CEC controller")
	adapters = cec_controller.DetectAdapters()
	if (adapters):
		log.debug("Found " + str(len(adapters)) + " CEC adapters")
		for i, adapter in enumerate(adapters):
			log.debug("  " + str(i + 1) + ": " + adapter.strComName)

		connected : bool = False
		log.debug("Trying to connect to adapters...")
		for adapter in adapters:
			port = adapter.strComName
			log.debug("Attempting to connect to adapter at port " + port)
			if (cec_controller.Open(port)):
				log.info("Connected to CEC adapter at port " + port)
				connected = True
				break
			else:
				log.error("Failed to open CEC adapter at port " + port)

		if (connected):
			log.info("Finished setting up CEC controller - success")
			power_status = cec_controller.GetDevicePowerStatus(cec.CEC_DEVICE_TYPE_TV)
			log.info("Reported screen power status at startup: " + cec_controller.PowerStatusToString(power_status) + " (" + str(power_status) + ")")
		else:
			log.error("Failed to set up CEC controller: Could not connect to any CEC adapters")
	else:
		log.error("Failed to set up CEC controller: No CEC adapters found")

	set_last_action("Initialized CEC", "Init")

@route("/divera/manual", method="GET")
def manual() -> str:
	global last_action
	global last_action_source
	global last_action_time
	return template("templates/divera_alarm/manual.tpl", last_action=last_action, last_action_time=last_action_time, last_action_source=last_action_source, power_status=power_status())

@route("/divera/manual/on", method="GET")
def screen_on_manual() -> HTTPResponse:
	screen_on("Manually")
	return HTTPResponse(status=200, body="OK")

@route("/divera/manual/off", method="GET")
def screen_off_manual() -> HTTPResponse:
	screen_off("Manually")
	return HTTPResponse(status=200, body="OK")

@route("/divera/alarm", method="POST")
def handle_alarm() -> HTTPResponse:
	log.info("Incoming message to /divera/alarm")
	try:
		if (request.query["secret"] != config["secret"]):
			log.warning("Skipping request with invalid secret: " + request.query["secret"])
			raise HTTPError(status=403, body="Invalid secret")
	
	except KeyError as error:
			log.info("Skipping request with missing secret")
			raise HTTPError(status=401, body="Missing secret")

	try:
		if (request.json is None):
			log.error("Skipping empty json payload")
			raise HTTPError(status=400, body="Empty json payload")

		if (any(element in request.json["title"] for element in config["skipTitles"])):
			log.info("Skipping alarm with ignored keyword in title: \"" + request.json["title"] + "\"")
			return HTTPResponse(status=200, body="OK (Skipped)")
	
	except UnicodeDecodeError as error:
		log.error("Unicode error: " + error.reason)
		raise HTTPError(status=400, body=error.reason)
	except JSONDecodeError as error:
		log.error("Decode error: " + error.msg)
		raise HTTPError(status=400, body=error.msg)
	except KeyError as error:
		log.error("Key error: " + str(error))
		raise HTTPError(status=400, body="Missing required json element: " + str(error))

	global screen_shutoff_timer
	if (screen_shutoff_timer is not None):
		log.debug("Cancelling existing screen shutoff timer")
		screen_shutoff_timer.cancel()

	shutoff_time : int = config["shutoffTime"] * 60
	power_status : int = cec_controller.GetDevicePowerStatus(cec.CEC_DEVICE_TYPE_TV)
	log.debug("Reported screen power status: " + str(power_status))

	if (config["trustReportedPowerStatus"]):
		#Power status: 0 = On, 1 = Standby, 2 = StandbyToOn, 3 = OnToStandby, 99 = Unknown
		global screen_previously_on
		if (screen_previously_on is None):
			if (power_status in (cec.CEC_POWER_STATUS_ON, cec.CEC_POWER_STATUS_IN_TRANSITION_STANDBY_TO_ON)):
				log.info("Screen already on")
				if (shutoff_time > 0):
					screen_previously_on = True
			else:
				screen_on("Alarm: " + request.json["title"])
				if (shutoff_time > 0):
					screen_previously_on = False
	else:
		log.info("Can't trust reported power status, force turning on screen")
		screen_on("Alarm: " + request.json["title"])

	log.debug("Setting self to active source")
	cec_controller.SetActiveSource(cec.CEC_DEVICE_TYPE_TV)

	if (shutoff_time > 0):
		log.info("Starting screen shutoff timer")
		screen_shutoff_timer = Timer(shutoff_time, shutoff_screen)
		screen_shutoff_timer.start()
	else:
		log.debug("Skipping screen shutoff timer, shutoff time in config set to <= 0")

	return HTTPResponse(status=200, body="OK")

# @route("/divera/debug/powerstatus", method="GET")
def power_status() -> str:
	global cec_controller
	power_status = cec_controller.GetDevicePowerStatus(cec.CEC_DEVICE_TYPE_TV)
	power_status_reliability : str = ": [" if config["trustReportedPowerStatus"] else " (unreliable!): ["
	return "Reported power status" + power_status_reliability + cec_controller.PowerStatusToString(power_status) + " (" + str(power_status) + ")]"

# @route("/divera/debug/scan", method="GET")
def scan() -> str:
	global cec_controller
	print("requesting CEC bus information ...")
	strLog : str = "CEC bus information\r\n===================\n"
	addresses = cec_controller.GetActiveDevices()
	x = 0
	while x < 15:
		if addresses.IsSet(x):
			vendorId        = cec_controller.GetDeviceVendorId(x)
			physicalAddress = cec_controller.GetDevicePhysicalAddress(x)
			active          = cec_controller.IsActiveSource(x)
			cecVersion      = cec_controller.GetDeviceCecVersion(x)
			power           = cec_controller.GetDevicePowerStatus(x)
			osdName         = cec_controller.GetDeviceOSDName(x)
			strLog += "device #" + str(x) +": " + cec_controller.LogicalAddressToString(x) + "\n"
			strLog += "address:       " + str(physicalAddress) + "\n"
			strLog += "active source: " + str(active) + "\n"
			strLog += "vendor:        " + cec_controller.VendorIdToString(vendorId) + "\n"
			strLog += "CEC version:   " + cec_controller.CecVersionToString(cecVersion) + "\n"
			strLog += "OSD name:      " + osdName + "\n"
			strLog += "power status:  " + cec_controller.PowerStatusToString(power) + "\n\r\n\r\n"
		x += 1
	log.debug(strLog)
	return template("templates/divera_alarm/cec_scan.tpl", message=strLog)

def shutoff_screen() -> None:
	global screen_shutoff_timer
	screen_shutoff_timer = None

	global screen_previously_on
	if (screen_previously_on):
		log.info("Setting self as inactive source")
		cec_controller.SetInactiveView()
		set_last_action("Set inactive", "Shutoff timer")
	else:
		screen_off("Shutoff timer")
	screen_previously_on = None

def screen_on(source : str) -> None:
	log.info("Turning on screen")
	cec_controller.PowerOnDevices(cec.CECDEVICE_BROADCAST)

	set_last_action("Screen on", source)

def screen_off(source : str) -> None:
	log.info("Shutting off screen")
	cec_controller.StandbyDevices(cec.CEC_DEVICE_TYPE_TV)

	set_last_action("Screen off", source)

def set_last_action(action : str, source : str) -> None:
	global last_action
	global last_action_source
	global last_action_time
	last_action = action
	last_action_source = source
	last_action_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	log.debug("Setting last action as [" + last_action + "] at [" + last_action_time + "] from source [" + last_action_source + "]")


def init() -> None:
	log.info("Initializing " + __name__.strip("_"))
	init_cec()
