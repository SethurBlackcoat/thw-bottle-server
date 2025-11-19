from logging import Logger
from common import load_config, get_logger
from sqlite3 import Connection, register_adapter, register_converter, connect, Row, PARSE_DECLTYPES
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from bottle import route, template, HTTPError, request, response, redirect
from functools import wraps
from typing import Callable
from simplejson.errors import JSONDecodeError
from threading import Lock
import requests

config = load_config(__name__)
log : Logger = get_logger(__name__, config["logLevel"])
db : Connection
db_lock : Lock
receiver_cache : dict[str, str]
use_notify : bool

def require_auth(redirect_location : str) -> Callable[[Callable[[str], str]], Callable[[], str]]:
    def auth_decorator(fn : Callable[[str], str]) -> Callable[[], str]:
        @wraps(fn)
        def auth_wrapper(*args, **kwargs) -> str:
            if not request.get_cookie("authentication", secret=config["cookieSecret"]):
                response.set_cookie("redirect-after-auth", redirect_location.format(**kwargs), secure="on", path="/maintenance/login", samesite="strict")
                return template("templates/maintenance/login.tpl")
            else:
                return fn(*args, **kwargs)
        return auth_wrapper
    return auth_decorator

def validate_unit(fn : Callable[[str], str]) -> Callable[[], str]:
    @wraps(fn)
    def validate_wrapper(*args, **kwargs) -> str:
        if kwargs["unit"] not in config["units"]:
            return HTTPError(404, f"Einheit '{kwargs['unit']}' nicht in scheduled_maintenance.conf konfiguriert")
        else:
            return fn(*args, **kwargs)
    return validate_wrapper

def catch_forms_exceptions(fn : Callable[[str], str]) -> Callable[[], str]:
    @wraps(fn)
    def catch_exceptions(*args, **kwargs) -> str:
        try:
            return fn(*args, **kwargs)
        except KeyError as error:
            return f"Error with form parameter: {str(error)}"
        except Exception as error:
            return f"Error: {str(type(error))} - {str(error)}"
    return catch_exceptions

def parse_relativedelta(string : str) -> relativedelta:
    split = string.split(" ")
    return relativedelta(**{split[1] : int(split[0])})

def adapt_date_iso(date : date) -> str:
    return date.isoformat()

def convert_date(value : bytes) -> date:
    return date.fromisoformat(value.decode())

def get_notify_receiver(unit : str) -> dict[str, str]:
    if receiver_cache is None:
        if not build_receiver_cache():
            return {"ID": None, "Name": None}

    return receiver_cache.get(unit, {"ID": None, "Name": None})

def build_receiver_cache() -> bool:
    global receiver_cache
    if not use_notify:
        receiver_cache = {}
        return True
    
    try:
        try:
            response = requests.get(url=config["notify"]["usersEndpoint"], params={"accesskey": config["notify"]["accesskey"]}, timeout=config["notify"]["httpTimeout"])
            response.raise_for_status()
            json = response.json()

            if (json is None):
                log.error("Skipping empty json payload")
                raise HTTPError(status=400, body="Empty json payload")
                
            if not json.get("success", False):
                raise HTTPError(status=json["status"], body=f"Request failed: {json['message']}")
                
            receiver_cache = { unit : next(({"ID": user['foreign_id'], "Name": f"{user['lastname']}, {user['firstname']}"} for user in json["data"] 
                                            if user.get("foreign_id", None) == config["units"][unit]), None) for unit in config["units"] if config["units"][unit] }

        except requests.HTTPError as error:
            log.error("HTTP Error: " + str(error))
            raise
        except requests.Timeout as error:
            log.error("Request timed out: " + str(error))
            raise
        except requests.ConnectionError as error:
            log.error("Connection failed: " + str(error))
            raise
        except UnicodeDecodeError as error:
            log.error("Unicode error: " + error.reason)
            raise
        except JSONDecodeError as error:
            log.error("Decode error: " + error.msg)
            raise
        except KeyError as error:
            log.error("Key error: " + str(error))
            raise
        except Exception as error:
            log.error("Unknown error: " + str(type(error)) + " - " + str(error))
            raise
        
        for f in ((unit, config['units'][unit]) for unit in config["units"] if config["units"][unit] and not receiver_cache.get(unit, None)):
            log.error(f"Failed to match notification receiver from scheduled_maintenance.conf to user in Divera: Group \"{f[0]}\", User ID \"{f[1]}\"")
            receiver_cache.pop(f[0])

        return True
    
    except Exception as error:
        log.error("Failed to build receiver cache: " + str(type(error)) + " - " + str(error))
        receiver_cache = None
        return False

def notify_for_task(task : Row) -> bool:
    receiver = get_notify_receiver(task["Unit"])
    if not receiver["ID"]:
        return False
    
    payload = config["notify"]["json"].copy()
    payload["News"]["title"] = f"Erinnerung: \"{task['Name']}\" ist bald fällig"
    payload["News"]["text"] = (f"""Aufgabe: {task["Name"]}\n{f"Beschreibung: {task['Description']}" if task["Description"] else ""}\nFälligkeit: {task["DueDate"]}\n"""
                               f"""Anzeige auf Monitor: {"Ja" if task["NotifyShow"] else "Nein"}""")
    payload["News"]["user_cluster_relation"] = [receiver["ID"]]
    payload["News"]["ts_archive"] = int((datetime.today() + relativedelta(days=config["notify"]["archiveAfter"])).timestamp())
    
    try:
        response = requests.post(url=config["notify"]["notifyEndpoint"], params={"accesskey": config["notify"]["accesskey"]}, json=payload, timeout=config["notify"]["httpTimeout"])
        log.info(f"Sending notification to user {receiver['ID']} ({receiver['Name']}) for task {task['Id']} ({task['Name']})")
        log.debug(f"Payload: {str(payload)}")
        log.debug(f"Response: {str(response.json())}")
        response.raise_for_status()
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

@route("/maintenance/overview", method="GET")
@route("/maintenance/overview/", method="GET")
def overview(concise = False, embed = False) -> str:
    if not embed:
        response.set_cookie("return-to", f"/maintenance/overview", path="/maintenance", samesite="lax")
        concise = concise or request.get_cookie("concise-overview", False)

    due_tasks : dict[str, list[Row]] = {}
    with db_lock:
        for unit in config["units"]:
            due_tasks[unit] = db.execute(f"SELECT Id, Active, Name, Description, DueDate, NotifyDate, OverdueDate FROM Tasks WHERE Active = 1 AND Unit = ? {'AND (date() >= DueDate OR (NotifyShow = 1 AND date() >= NotifyDate))' if concise else ''} ORDER BY DueDate ASC", (unit,)).fetchall()

    return template("templates/maintenance/overview.tpl", tasks=due_tasks, concise=concise, embed=embed, refresh=config["refreshEmbed"] * 60 * 1000)

@route("/maintenance/overview/full", method="GET")
def overview_full() -> str:
    response.delete_cookie("concise-overview", path="/maintenance")
    response.status = 302
    response.set_header("Location", f"/maintenance/overview")
    return

@route("/maintenance/overview/concise", method="GET")
def overview_concise() -> str:
    response.set_cookie("concise-overview", "True", path="/maintenance", samesite="lax", max_age=(60 * 60 * 24 * 90))
    response.status = 302
    response.set_header("Location", f"/maintenance/overview")
    return

@route("/maintenance/overview/full/embed", method="GET")
def overview_full_embed() -> str:
    return overview(embed=True)

@route("/maintenance/overview/concise/embed", method="GET")
def overview_concise_embed() -> str:
    return overview(concise=True, embed=True)

@route("/maintenance/unit/<unit>", method="GET")
@route("/maintenance/unit/<unit>/", method="GET")
@validate_unit
def show_unit(unit : str) -> str:
    with db_lock:
        unit_tasks = db.execute("SELECT Id, Active, Name, Description, DueDate, NotifyDate, OverdueDate, NotifyShow, NotifyMessage FROM Tasks WHERE Unit = ? ORDER BY Active DESC, DueDate ASC", (unit,))
    response.set_cookie("return-to", f"/maintenance/unit/{unit}", path="/maintenance", samesite="lax")
    return template("templates/maintenance/unit.tpl", unit=unit, tasks=unit_tasks)

@route("/maintenance/unit/<unit>/new", method="GET")
@validate_unit
@require_auth(redirect_location="/maintenance/unit/{unit}/new")
def create_task(unit : str) -> str:
    return template("templates/maintenance/new_task.tpl", unit=unit, notify_receiver=get_notify_receiver(unit)["Name"])

@route("/maintenance/unit/<unit>/new", method="POST")
@validate_unit
@catch_forms_exceptions
@require_auth(redirect_location="/maintenance/unit/{unit}/new")
def save_created_task(unit : str) -> str:
    due_date : date = date.fromisoformat(request.forms.DueDate)
    repeat_offset : str = f"{request.forms.RepeatValue} {request.forms.RepeatUnit}"
    notify_offset : str = f"{request.forms.NotifyValue} {request.forms.NotifyUnit}"
    overdue_offset : str = f"{request.forms.OverdueValue} {request.forms.OverdueUnit}"
    with db_lock:
        db.execute("INSERT INTO Tasks (Unit, Name, Description, DueDate, NotifyDate, OverdueDate, RepeatOffset, NotifyOffset, OverdueOffset, NotifyShow, NotifyMessage) VALUES (:unit, :name, :description, :dueDate, :notifyDate, :overdueDate, :repeatOffset, :notifyOffset, :overdueOffset, :notifyShow, :notifyMessage)", 
                {"unit": unit, "name": request.forms.Name, "description": request.forms.Description, "dueDate": due_date, "notifyDate": due_date - parse_relativedelta(notify_offset), "overdueDate": due_date + parse_relativedelta(overdue_offset), "repeatOffset": repeat_offset, "notifyOffset": notify_offset, "overdueOffset": overdue_offset, "notifyShow": "NotifyShow" in request.forms, "notifyMessage": "NotifyMessage" in request.forms})
    response.status = 303
    response.set_header("Location", f"/maintenance/unit/{unit}")
    return "Creation successful, redirecting..."

@route("/maintenance/unit/<unit>/task/<task:int>/view", method="GET")
@validate_unit
def view_task(unit : str, task : int) -> str:
    with db_lock:
        row = db.execute("SELECT Active, Name, Description, DueDate, OverdueDate, NotifyDate FROM Tasks WHERE Id = ?", (task,)).fetchone()
    response.set_cookie("return-to", f"/maintenance/unit/{unit}/task/{task}/view", path="/maintenance", samesite="lax")
    return template("templates/maintenance/view_task.tpl", unit=unit, id=task, task=row, notify_receiver=get_notify_receiver(unit)["Name"]) 

@route("/maintenance/unit/<unit>/task/<task:int>/edit", method="GET")
@validate_unit
@require_auth(redirect_location="/maintenance/unit/{unit}/task/{task}/edit")
def edit_task(unit : str, task : int) -> str:
    with db_lock:
        row = db.execute("SELECT Active, Name, Description, DueDate, NotifyDate, OverdueDate, RepeatOffset, NotifyOffset, OverdueOffset, NotifyShow, NotifyMessage FROM Tasks WHERE Id = ?", (task,)).fetchone()
    return template("templates/maintenance/edit_task.tpl", unit=unit, task=task, row=row, notify_receiver=get_notify_receiver(unit)["Name"]) 

@route("/maintenance/unit/<unit>/task/<task:int>/edit", method="POST")
@validate_unit
@catch_forms_exceptions
@require_auth(redirect_location="/maintenance/unit/{unit}/task/{task}/edit")
def save_edited_task(unit : str, task : int) -> str:
    dueDate = date.fromisoformat(request.forms.DueDate)
    repeat_offset : str = f"{request.forms.RepeatValue} {request.forms.RepeatUnit}"
    notify_offset : str = f"{request.forms.NotifyValue} {request.forms.NotifyUnit}"
    overdue_offset : str = f"{request.forms.OverdueValue} {request.forms.OverdueUnit}"
    with db_lock:
        db.execute("UPDATE Tasks SET Active = :active, Name = :name, Description = :description, DueDate = :dueDate, NotifyDate = :notifyDate, OverdueDate = :overdueDate, RepeatOffset = :repeatOffset, NotifyOffset = :notifyOffset, OverdueOffset = :overdueOffset, NotifyShow = :notifyShow, NotifyMessage = :notifyMessage, MessageSent = :messageSent WHERE Id = :id", 
                {"id": task, "active": "TaskActive" in request.forms, "name": request.forms.Name, "description": request.forms.Description, "dueDate": dueDate, "notifyDate": dueDate - parse_relativedelta(notify_offset), "overdueDate": dueDate + parse_relativedelta(overdue_offset), "repeatOffset": repeat_offset, "notifyOffset": notify_offset, "overdueOffset": overdue_offset, "notifyShow": "NotifyShow" in request.forms, "notifyMessage": "NotifyMessage" in request.forms, "messageSent": 0})
    response.status = 303
    response.set_header("Location", "/maintenance")
    return "Edit successful, redirecting..."

@route("/maintenance/unit/<unit>/task/<task:int>/done", method="POST")
@validate_unit
@catch_forms_exceptions
def mark_task_done(unit : str, task : int) -> str:
    with db_lock:
        row = db.execute("SELECT RepeatOffset, NotifyOffset, OverdueOffset FROM Tasks WHERE Id = ?", (task,)).fetchone()
        new_due_date = date.fromisoformat(request.forms.DoneDate) + parse_relativedelta(row["RepeatOffset"])
        db.execute("UPDATE Tasks SET DueDate = :dueDate, NotifyDate = :notifyDate, OverdueDate = :overdueDate, MessageSent = :messageSent WHERE Id = :id", 
                {"id": task, "dueDate": new_due_date, "notifyDate": new_due_date - parse_relativedelta(row["NotifyOffset"]), "overdueDate": new_due_date + parse_relativedelta(row["OverdueOffset"]), "messageSent": 0})
    response.status = 303
    response.set_header("Location", f"/maintenance/unit/{unit}")
    return "Complete successful, redirecting..."

@route("/maintenance/unit/<unit>/task/<task:int>/delete", method="POST")
@validate_unit
@require_auth(redirect_location="/maintenance/unit/{unit}/task/{task}")
def delete_task(unit : str, task : int) -> str:
    with db_lock:
        db.execute("DELETE FROM Tasks WHERE ID = ?", (task,))
    response.status = 303
    response.set_header("Location", f"/maintenance/unit/{unit}")
    return "Deletion successful, redirecting..."

@route("/maintenance/login", method="GET")
def show_login() -> str:
    if request.get_cookie("authentication", secret=config["cookieSecret"]):
        return redirect("/maintenance/overview")
    else:
        return template("templates/maintenance/login.tpl")

@route("/maintenance/login", method="POST")
@catch_forms_exceptions
def process_auth() -> str:
    if request.forms.Password == config["editPassword"]:
        response.status = 303
        response.set_header("Location", request.get_cookie("redirect-after-auth") or "/maintenance/overview")
        response.set_cookie("authentication", "true", secret=config["cookieSecret"], secure="on", path="/maintenance", samesite="strict")
        response.delete_cookie("redirect-after-auth", path="/maintenance/login")
        return "Authentication successful, redirecting..."
    else:
        return template("templates/maintenance/login.tpl", failed=True)
    
@route("/maintenance/cron_notify", method="POST")
def cron_notify() -> str:
    with db_lock:
        rows = db.execute("SELECT Id, Unit, Name, Description, DueDate, NotifyShow FROM Tasks WHERE Active = 1 AND NotifyMessage = 1 AND MessageSent = 0 AND date() >= NotifyDate").fetchall()
        for row in rows:
            try:
                if notify_for_task(row):
                    db.execute("UPDATE Tasks SET MessageSent = 1 WHERE Id = ?", (row["Id"],))
                else:
                    log.error(f"Failed to notify for task {row['Id']} ({row['Name']}): No or invalid receiver configured for unit {row['Unit']}")
            except Exception as error:
                log.error(f"Failed to notify for task {row['Id']} ({row['Name']}): " + str(type(error)) + " - " + str(error))

    return "Ok"

@route("/maintenance", method="GET")
@route("/maintenance/", method="GET")
@route("/maintenance/unit", method="GET")
@route("/maintenance/unit/", method="GET")
@route("/maintenance/unit/<>/task", method="GET")
@route("/maintenance/unit/<>/task/", method="GET")
def redirect_to_return_location() -> str:
    redirect(request.get_cookie("return-to", "/maintenance/overview"))


def init() -> None:
    global db
    global db_lock
    global use_notify
    log.info("Initializing " + __name__.strip("_"))

    get_logger("urllib3.connectionpool", config["logLevelUrllib"])

    register_adapter(date, adapt_date_iso)
    register_converter("Date", convert_date)
    db = connect("db/scheduled_maintenance.db", detect_types=PARSE_DECLTYPES, check_same_thread=False)
    db.isolation_level = None
    db.row_factory = Row
    db_lock = Lock()
    
    use_notify = bool(config["notify"]["usersEndpoint"]) and bool(config["notify"]["notifyEndpoint"]) and bool(config["notify"]["accesskey"])
    if not use_notify:
        log.info("Starting with notify functionality disabled due to scheduled_maintenance.conf settings")
    build_receiver_cache()
