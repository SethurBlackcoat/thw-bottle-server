# Übersicht
## Allgemein
Der Appserver besteht aus einzelnen Modulen, welche jeweils eine bestimmte Aufgabe übernehmen bzw. Dienst bereitstellen. Sie können einzeln aktiviert oder deaktiviert werden. Es gibt ein Grundmodul `main.py` welches das Logging konfiguriert, die anderen Module lädt und initialisiert, und den bottle-server selbst startet.

Das `divera_alarm` Modul kann bei einem einkommenden Divera-Alarm automatisch einen angeschlossen Bildschirm anschalten bzw. auf seinen Input umschalten (via HDMI-CEC), um z.B. eine Übersicht mit Rückmeldungen anzuzeigen. Optional wird der Bildschirm nach einer einstellbaren Zeit auch wieder automatisch abgeschalten bzw. auf den vorherigen Input zurückgeschalten.

Das `divera_vehicle_status` Modul liest in einem Postfach ankommende Emails aus um STEIN Statusmeldung zu verarbeiten und die entsprechenden Fahrzeuge in Divera ebenfalls auf den respektiven Status zu setzen.

Konfiguration zu den jeweiligen Modulen befindet sich im Ordner `config`, jeweils in der Datei `<modulname>.conf`.

Weitere Module können einfach selbst erstellt werden: Das entsprechende Python-Skript in den Hauptordner legen, Konfigurationsdatei mit in den `config` Ordner, in die `main.conf` unter `modules` den Modulnamen hinzufügen und als aktiv markieren. Beim nächsten Start des Servers wird das Modul mitgeladen und initialisiert.

## divera_alarm
Das Modul initialisiert beim Start einen CEC Controller, mittels dem der Bildschirm angesteuert wird. Zum Debuggen kann die URL `/divera/debug/scan` einkommentiert werden indem in `divera_alarm.py` das `# ` vor der Zeile entfernt wird (sollte danach dann wieder auskommentiert werden). Über diese lässt sich dann mittels eines Webbrowsers das detektierte CEC-Netzwerk anzeigen. Es kann auf selber Weise die URL `/divera/debug/powerstatus` einkommentiert werden, welche den vom Bildschirm gemeldeten Zustand (angeschalten, anschaltend, ausschaltend, ausgeschalten, unbekannt) anzeigt.

Die Hauptansteuerung findet via POST-Request an die URL `/divera/alarm` mit einer JSON-Nachricht statt. Das Format entspricht dem des Divera-Webhooks welcher in Divera unter `Verwaltung > Schnittstellen > Datenübergabe > Webhooks` mit dem Inhalt `Vollständiges Objekt` angelegt werden kann. Es wird zur Zeit allerdings lediglich das `title` Element ausgewertet. Das in der Konfiguration angelegte secret (siehe unten, Einstellung `secret` in `divera_alarm.conf`) muss als URL-Parameter angefügt sein (`/divera/alarm?secret=...`), sonst wird der Alarm ignoriert.

Zusätzlich existiert noch die URL `/divera/manual`, welche bei Zugriff via Webbrowser den aktuellen Zustand kurz zusammenfässt und eine einfache Oberfläche zum manuellen an-/ausschalten des Bildschirms anbietet. Die entsprechenden URLs `/divera/manual/on` und `/divera/manual/off` können zur externen Automatisierung auch direkt mit GET-Requests angesteuert werden.

## divera_vehicle_status
Das Modul verbindet sich beim Start mit dem konfigurierten Email-Postfach, ruft vorhandene ungelesene Emails ab, bearbeitet diese und geht dann in eine Ruhezustand (IMAP IDLE) in dem es darauf wartet von dem Emailserver benachrichtigt zu werden dass eine neue Email eingetroffen ist. Beim Erhalt einer solchen Nachricht werden wieder alle ungelesenen Emails abgerufen und bearbeitet. Um eine Mehrfachbearbeitung von Emails zu vermeiden müssen Emails nach dem bearbeiten entweder auf gelesen gesetzt, in einen anderen Ordner verschoben, und/oder gelöscht werden. Wie mit Emails unter bestimmten Umständen umgegangen werden soll lässt sich in der Konfiguration festlegen (siehe unten, Einstellung `imapPostProcess` in `divera_vehicle_status.conf`).

Zum debuggen kann die URL `/vehicle_status/listvehicles` einkommentiert werden indem in `divera_vehicle_status.py` das `# ` vor der Zeile entfernt wird (sollte danach dann wieder auskommentiert werden). Über diese lässt sich dann mittels eines Webbrowsers eine Liste der in Divera hinterlegten Fahrzeuge inklusive deren Divera-ID anzeigen; die Divera-IDs werden für die Fahrzeugzuordnung zwischen STEIN und Divera benötigt (siehe unten, Einstallung `vehicleMapping` in `divera_vehicle_status.conf`).

# Konfiguration
## Allgemein
Für alle Module sind Beispielkonfigurationen mitgeliefert. Diese befinden sich im `config` Ordner mit dem Dateinamenpräfix `example_` vor dem Namen des entsprechenden Moduls. Um sie zu verwenden die Datei umbenennen oder kopieren, `example_` aus dem Dateinamen entfernen, und die Konfiguration mit den eigenen Einstellungen anpassen (Details zu spezifischen Modulen siehe unten).

**Fett** gedruckte Einstellungen müssen zwingend auf die eigenen Daten angepasst werden damit das Modul funktioniert. Gewisse Grundkenntnisse in der Funktionsweise und Konfiguration von Servern werden hier leider vorausgesetzt; eine volle Erklärung der Grundlagen würde den Rahmen sprengen. Es sollte aber selbst recht minimales Wissen ausreichen.  

## main.conf
* `hostname` und `port`: Einstellungen auf welchem hostname und port der Server läuft. `0.0.0.0` entspricht IPv4; um unter IPv6 zu laufen ist als hostname `[::]` anzugeben. Der Server sollte entsprechend gängiger best practices nicht als root laufen; um einen Zugang via Port 80 (HTTP) oder 443 (HTTPS) zu ermöglichen sollte stattdessen eine reverse proxy vorgeschaltet werden.
* `keyfile` und `certfile`: Respektive private key und certificate für HTTPS-Verbindungen. Ein automatisches Zertifikatsmanagment via LetsEncrypt + certbot o.ä. ist empfohlen.
* **`modules`**: Vorhandene Module und ob sie geladen werden sollen (`true`) oder nicht (`false`). In der Beispielkonfiguration sind standardmäßig alle deaktiviert; gewünschte als aktiv markieren. Es wird empfohlen dies schrittweise zu tun, um deren einzelne Konfigurationen testen zu können.
* `logToConsole` und `logLevelConsole`: Ob Logausgaben auf die Konsole geleitet werden sollen und ab welchem Level. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
* `logToFile`, `logLevelFile`, und `logfile`: Ob Logausgaben in eine Datei geschrieben werden sollen und ab welchem Level, sowie den Speicherort der Logdatei. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## divera_alarm.conf
* **`secret`**: Eine Zeichenketten welche an den Request angehängt werden muss damit dieser bearbeitet wird. Effektiv ein "Passwort" welches verhindert dass man ohne dieses durch senden eines gefälschten Alarms den Bildschirm anschalten kann.
* `skipTitles`: Liste von Worten welche, wenn sie im Feld `Stichwort` des Alarms enthalten sind, dazu führen dass der Bildschirm nicht angeschalten wird. Nützlich um z.B. zu verhindern dass bei einem monatlichen Probealarm der Bildschirm angeschalten wird.
* `shutoffTime`: Zeit in Minuten bis der Bildschirm wieder abgeschalten wird, falls er bei Eingang des Alarms aus war. Wenn 0 dann ist das automatische Abschalten deaktiviert, d.h. der Bildschirm bleibt an bis er manuell ausgeschalten wird (oder durch eine im Bildschirm integrierte Funktion).
* `trustReportedPowerStatus`: Leider ist der CEC Standard nicht immer zuverlässig implementiert. Manche Bildschirme geben falsche oder ungültige Rückmeldung ob sie an- oder ausgeschalten sind. Falls es sich herausstellt dass dies bei seinem Modell der Fall ist, kann man diese Option auf `false` setzen um immer anzunehmen dass der Bildschirm bei Eingang des Alarms ausgeschalten war.
* `logLevel`: Ab welchem Level dieses Modul Logmeldung weiterreichen soll. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## divera_vehicle_status.conf
* **`imapServer`** und `imapPort`: Verbindungsdaten für den Emailserver auf welchem das zu überwachende Postfach liegt. Alles inklusive spitzen Klammern (`<>`) durch eigene Daten ersetzen. Port 993 ist standardmäßig für IMAP vorgesehen und sollte nur in Ausnahmefällen geändert werden müssen.
* **`imapUser`** und **`imapPassword`**: Zugangsdaten für das zu überwachende Postfach. Alles inklusive spitzen Klammern (`<>`) durch eigene Daten ersetzen.
* `imapFolder`: Welcher Ordner des Postfachs überwacht werden soll. `INBOX` ist standardmäßig der Hauptordner; falls das Postfach aber noch anderweitig verwendet wird (nicht empfohlen) kann auch nur ein Unterordner überwacht und die relevanten Emails dorthin durch eine automatische Eingangsregel verschoben werden.
* `mailFrom`: Absender von dem die Email kommen muss um bearbeitet zu werden. Emails von allen anderen Absendern werden nach der Einstellung `Skipped` behandelt (siehe unten). Sollte nur angepasst werden müssen wenn STEIN die Absenderadresse ihrer Statusemails ändert.
* `subjectRegex`: Regex-Muster dem der Betreff der Email entsprechen muss um bearbeitet zu werden. Emails mit allen anderen Betreffs werden nach der Einstellung `Skipped` behandelt (siehe unten). Sollte nur angepasst werden müssen wenn STEIN den Betreff ihrer Statusemails ändert.
* `bodyRegex`: Regex-Muster nach dem der Inhalt der Email bearbeitet wird und die relevanten Daten (Fahrzeug und neuer Status) extrahiert wird. Sollte nur angepasst werden müssen wenn STEIN das Format ihrer Statusemails ändert.
* `imapPostProcess`: Welche Aktionen durchgeführt werden nachdem eine Email ausgelesen wurde. Jeweils einzeln konfigurierbar je nachdem wie die Email bearbeitet wurde:
  * `matched`: Email wurde erfolgreich bearbeitet und Fahrzeugstatus in Divera angepasst.
  * `ignored`: Email wurde erfolgreich bearbeitet, aber Aufgrund von Konfiguration ignoriert (siehe unten). Kein Änderung an Fahrzeugstatus.
  * `skipped`: Email wurde erfolgreich ausgelesen, aber Absender oder Betreff entsprechen nicht der Konfiguration, daher wurde die weitere Bearbeitung abgebrochen. Keine Änderung an Fahrzeugstatus.
  * `failed`: Während der Bearbeitung der Email ist ein Fehler aufgetreten. Keine Änderung an Fahrzeugstatus. Details zu dem Fehler im Log unter Loglevel ERROR.

  Für jeden dieser Zustände können die folgenden Optionen konfiguriert werden:
  * `setRead`: Email als "gelesen" markieren.
  * `move`: Email in anderen Ordner verschieben.
  * `moveFolder`: Wenn `move` aktiviert, in welchen Ordner die Email zu verschieben ist. Ordner muss im Postfach existieren.
  * `delete`: Email aus dem Postfach löschen.
* `imapIdleDuration`: Dauer in Minuten wie lange die Verbindung zum Emailserver offen gehalten und auf Benachrichtigung einer neuen Email gewartet wird. Nach Ablauf dieser Zeit wird der Emailserver informiert dass die Verbindung noch gültig ist. Manche Emailserver haben ein etwas kürzeres Intervall bevor sie Verbindungen schließen; in diesem Fall sollte diese Einstellung entsprechend herabgesetzt werden.
* `imapWaitRetry`: Dauer in Sekunden zwischen Versuchen die Verbindung zum Emailserver aufzubauen (bei Start des Servers oder Abbruch der Verbindung). Verhindert dass bei kurzzeitigen Störungen der Internetverbindung hunderte von Verbindungsversuchen durchgeführt werden.
* `updateEndpoint`: API-URL um den Fahrzeugstatus zu ändern. Sollte nur angepasst werden müssen falls Divera seine API ändert.
* `listEndpoint`:  API-URL um die in Divera angelegten Fahrzeuge aufzulisten. Sollte nur angepasst werden müssen falls Divera seine API ändert.
* **`accesskey`**: Der Accesskey eines Divera-Systembenutzers welcher die Änderung des Fahrzeugstatus in Divera durchführt (anlegen in Divera unter `Verwaltung > Schnittstellen > System-Benutzer`).
* `httpTimeout`: Dauer in Sekunden bis ein Versuch den Fahrzeugstatus an Divera zu übergeben fehlschlägt.
* `statusMapping`: Welche Statusnummer (entsprechend Leitstellen-Funkstatus) gesetzt wird wenn von STEIN der entsprechende Textstatus gemeldet wird.
* **`vehicleMapping`**: Welche ID in Divera zu den entsprechenden von STEIN gemeldeten Fahrzeugen hinterlegt ist. Der STEIN-Name setzt sich zusammen aus dem Feld `Fahrzeug / Bez.` und dem Feld `THW-Kennzeichen`. Die Divera-ID lässt sich am einfachsten bestimmen indem man den Server mit dem Modul startet und lokal per Webbrowser auf die URL `/vehicle_status/listvehicles` zugreift. `accesskey` muss dazu konfiguriert sein, die URL is standardmäßig deaktiviert und muss in `divera_vehicle_status.py` einkommentiert werden indem das `# ` vor der Zeile entfernt wird (sollte nach initialer Konfiguration dann wieder auskommentiert werden).
* **`ignoredVehicles`**: Welche Fahrzeuge ignoriert werden, d.h. nicht versucht wird diese in Divera anzupassen. Jedes "Kärtchen" in STEIN zählt als ein Fahrzeug, auch wenn unter `Geräte`, `Sonderfunktionen`, `(Teil-)Einheiten` etc. angelegt. Alles was nicht explizit entweder in `vehicleMapping` oder `ignoredVehicles` hinterlegt ist führt dazu dass die Email als `failed` behandelt wird.
* `logLevel`: Ab welchem Level dieses Modul Logmeldung weiterreichen soll. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
* `logLevelImapclient`, `logLevelImaplib`, und `logLevelUrllib`: Ab welchem Level die Logmeldungen der entsprechenden verwendeten Libraries weitergereicht werden sollen. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

# Dependencies
* Python 3.10+

## Python module (Installation via pip o.ä.)
### Allgemein
* bottle

### divera_alarm
* cec
* simplejson

### divera_vehicle_status
* IMAPClient
