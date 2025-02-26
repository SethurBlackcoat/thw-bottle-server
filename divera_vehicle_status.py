from logging import Logger
from common import load_config, get_logger
from re import Pattern, Match, compile
from typing import Optional, Any
from bottle import route, HTTPError # type: ignore
from threading import Thread
from imapclient import IMAPClient	# type: ignore
from imaplib import IMAP4
from email import message_from_bytes, policy
from time import sleep
from socket import gaierror
import requests

config : dict = load_config(__name__)
log : Logger = get_logger(__name__, config["logLevel"])
from_regex : Pattern[str] = compile(r'^"?(.*?)"?\s*<?(\S+?@\S+?\.\S+?)>?$')
subject_regex : Pattern[str] = compile(config["subjectRegex"])
body_regex : Pattern[str] = compile(config["bodyRegex"])
vehicle_mapping : dict[str, int] = config["vehicleMapping"]
status_mapping : dict[str, int] = config["statusMapping"]
ignored_vehicles : set[str] = set(config["ignoredVehicles"])

def run_imapclient() -> None:
    sleep(10) # wait at startup to let rest of the server finish setup before we start writing stuff to the log
    while True:
        try:
            with IMAPClient(host=config["imapServer"], port=config["imapPort"], ssl=True) as imap:
                log.debug("Logging in to IMAP Server " + config["imapServer"])
                imap.login(config["imapUser"], config["imapPassword"])
                log.debug("Opening IMAP folder " + config["imapFolder"])
                imap.select_folder(config["imapFolder"])

                imap_read_loop(imap)
        
        except gaierror as error:
            log.error("Error resolving \"" + config["imapServer"] + "\": " + str(error))
            log.info("Waiting " + str(config["imapWaitRetry"]) + " seconds before restarting IMAP connection")
            sleep(config["imapWaitRetry"])
        except Exception as error:
            log.critical("Error while connecting to IMAP server: " + str(type(error)) + " - " + str(error))
            log.critical("Waiting " + str(config["imapWaitRetry"]) + " seconds before restarting IMAP connection")
            sleep(config["imapWaitRetry"])
        
        log.info("Attempting to restart IMAP connection")

def imap_read_loop(imap : IMAPClient):
    log.info("Checking for unread IMAP messages at connect")
    try:
        read_messages(imap)
    
    except Exception as error:
        log.error("Error while reading IMAP messages: " + str(type(error)) + " - " + str(error))
        return
            
    log.info("Entering IMAP IDLE mode")
    while True:
        try:
            imap.idle()
            responses = imap.idle_check(config["imapIdleDuration"] * 60)
            imap.idle_done()
        
        except IMAP4.abort as error:
            log.error("Aborted IMAP idling: " + str(error))
            return
        except IMAP4.error as error:
            log.error("IMAP error while idling: " + str(error))
            return
        except OSError as error:
            log.error("OS-Level error while IMAP idling: " + str(error))
            return
        except Exception as error:
            log.error("Error while IMAP idling: " + str(type(error)) + " - " + str(error))
            return

        if (responses):
            log.debug("Got IMAP responses, checking for unread messages")
            try:
                sleep(5) # wait in case multiple mails come in at once, so we can process them all together
                read_messages(imap)
                responses = None
            
            except Exception as error:
                log.error("Error while reading IMAP messages: " + str(type(error)) + " - " + str(error))
                return
                
        log.debug("Reentering IMAP IDLE mode")

def read_messages(imap : IMAPClient) -> None:
    while True: # repeat read as long as there are still mails to process; prevents us from missing new mails that come in during processing 
        mail_IDs = imap.search("UNSEEN")
        if (len(mail_IDs) > 0):
            log.info(str("Downloading " + str(len(mail_IDs))) + " new IMAP messages")
            mails : list[tuple[int, dict]] = sorted(imap.fetch(mail_IDs, "RFC822").items(), key=lambda e : e[1][b"SEQ"]) # sort by sequence number so we process from oldest to newest
            for i, (uid, data) in enumerate(mails):
                message : Any = message_from_bytes(data[b"RFC822"], policy=policy.default)
                subject : str = message["subject"]
                match_from : Optional[Match[str]] = from_regex.match(message["from"])

                if (not match_from):
                    log.error("Failed to extract sender email address!")
                    postprocess_actions(imap, uid, "failed")
                    continue
                
                log.info("Message " + str(i + 1) + " from: " + match_from.group(2) + " (\"" + match_from.group(1) + "\"), subject: \"" + subject + "\"")
                if (match_from.group(2) == config["mailFrom"] and subject_regex.match(subject)):
                    text : Optional[str] = None
                    if (message.is_multipart()):
                        for part in message.walk():
                            if (part.get_content_type() == "text/plain"):
                                text = part.get_content()
                    else:
                        text = message.get_content()
                    
                    log.debug(text)
                    
                    if (text is None):
                        log.error("IMAP message is empty - empty mail or parse error")
                        postprocess_actions(imap, uid, "failed")
                        continue

                    try:
                        if (process_message(text)):
                            postprocess_actions(imap, uid, "matched")
                        else:
                            postprocess_actions(imap, uid, "ignored")
                    
                    except Exception as error:
                        log.error("Error parsing IMAP message: " + str(type(error)) + " - " + str(error))
                        postprocess_actions(imap, uid, "failed")
                else:
                    log.info("Skipping message - No match for either sender \"" + config["mailFrom"] + "\" or subject regex \"" + subject_regex.pattern + "\"")
                    postprocess_actions(imap, uid, "skipped")
        else:
            break

def process_message(message : str) -> bool:
    processed_message = match(message)
    
    params : dict[str, str] = dict()
    params["accesskey"] = config["accesskey"]

    if (processed_message["vehicle"] in ignored_vehicles):
        log.info("Skipping message - Vehicle ignored: " + processed_message["vehicle"])
        return False
    
    try:
        params["id"] = str(vehicle_mapping[processed_message["vehicle"]])
    
    except KeyError as error:
        log.error("Failed to map vehicle: " + str(error))
        raise
    
    payload : dict[str, Any] = dict()
    payload["status_note"] = processed_message["status_new"]
    
    try:
        payload["status_id"] = status_mapping[processed_message["status_new"]]
    
    except KeyError as error:
        log.error("Failed to map status: " + str(error))
        raise
    
    try:
        response = requests.post(url=config["updateEndpoint"], params=params, json=payload, timeout=config["httpTimeout"])
        log.debug("Request: Update vehicle id " + params["id"] + " with payload " + str(response.request.body))
        log.debug("Response: " + str(response.json()))
        response.raise_for_status()
        log.info("Updated vehicle " + processed_message["vehicle"] + " to status " + processed_message["status_new"])
        return True
    
    except requests.HTTPError as error:
        log.error("HTTP Error: " + str(error))
        raise
    except requests.Timeout as error:
        log.error("Request timed out: " + str(error))
        raise
    except requests.ConnectionError as error:
        log.error("Connection failed: " + str(error))
        raise
    except Exception as error:
        log.error("Unknown error: " + str(type(error)) + " - " + str(error))
        raise
    
def match(message : str) -> dict[str, Any]:
    match : Optional[Match[str]] = body_regex.search(message)
    if match is None:
       raise ValueError("Failed to find match for \"" + body_regex.pattern + "\" in message \"" + message + "\"") 
    else:
        log.debug("Vehicle: " + match.group(1))
        log.debug("User: " + match.group(2))
        log.debug("Old Status: " + match.group(3))
        log.debug("New Status: " + match.group(4))

        result : dict[str, str] = dict()
        result["vehicle"] = match.group(1)
        result["user"] = match.group(2)
        result["status_old"] = match.group(3)
        result["status_new"] = match.group(4)
        return result

def postprocess_actions(imap : IMAPClient, uid : int, state : str) -> None:
    try:
        if (config["imapPostProcess"][state]["setRead"]):
            imap.add_flags([uid], [br"\SEEN"])
    
    except Exception as error:
        log.error("Failed to execute postprocess action setRead in state " + state + ": " + str(type(error)) + " - " + str(error))
                
    try:
        if (config["imapPostProcess"][state]["move"]):
            imap.move([uid], config["imapPostProcess"][state]["moveFolder"])
    
    except Exception as error:
        log.error("Failed to execute postprocess action moveFolder in state " + state + ": " + str(type(error)) + " - " + str(error))

    try:
        if (config["imapPostProcess"][state]["delete"]):
            imap.delete_messages([uid])
    
    except Exception as error:
        log.error("Failed to execute postprocess action delete in state " + state + ": " + str(type(error)) + " - " + str(error))

# @route("/vehicle_status/listvehicles", method="GET")
def list_vehicles() -> str:
    try:
        response = requests.get(url=config["listEndpoint"], params={"accesskey":config["accesskey"]}, timeout=config["httpTimeout"])
        return response.json()
    
    except requests.RequestException as error:
        raise HTTPError(status=500, body=error.strerror)


def init() -> None:
    log.info("Initializing " + __name__.strip("_"))
    log.debug("Subject regex :" + config["subjectRegex"])
    log.debug("Body regex: " + config["bodyRegex"])

    get_logger("imapclient.imapclient", config["logLevelImapclient"])
    get_logger("imapclient.imaplib", config["logLevelImaplib"])
    get_logger("urllib3.connectionpool", config["logLevelUrllib"])

    imap_thread = Thread(target=run_imapclient, name="IMAP Thread", daemon=True)
    imap_thread.start()
    log.debug(imap_thread.getName() + ": " + str(imap_thread.ident) + " (" + str(imap_thread.native_id) + ")")
