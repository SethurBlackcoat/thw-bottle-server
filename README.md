# Übersicht
## Allgemein
Der Appserver wird gestartet indem man `main.py` mit Python ausführt. Er besteht aus einzelnen Modulen, welche jeweils eine bestimmte Aufgabe übernehmen bzw. Dienst bereitstellen und einzeln aktiviert oder deaktiviert werden können. Jedes Modul benötigt etwas an Konfiguration um es auf die OV-eigenen Daten anzupassen (siehe unten, Abschnitt `Konfiguration`), ohne dieser wird es nicht starten. Die Konfiguration zu den jeweiligen Modulen befindet sich im Ordner `config`, jeweils in der Datei `<modulname>.conf`.

Das `main.py` Grundmodul konfiguriert das Logging, lädt und initialisiert die anderen Module, und startet den unterliegenden Webserver.

Das `divera_alarm` Modul kann bei einem einkommenden Divera-Alarm automatisch einen angeschlossen Bildschirm anschalten bzw. auf seinen Input umschalten (via HDMI-CEC), um z.B. eine Übersicht mit Rückmeldungen anzuzeigen. Optional wird der Bildschirm nach einer einstellbaren Zeit auch wieder automatisch abgeschalten bzw. auf den vorherigen Input zurückgeschalten.

Das `divera_vehicle_status` Modul liest in einem Postfach ankommende Emails aus um STEIN Statusmeldung zu verarbeiten und die entsprechenden Fahrzeuge in Divera ebenfalls auf den respektiven Status zu setzen.

Das `scheduled_maintenance` Modul ermöglicht es für die einzelnen Einheiten Aufgaben anzulegen welche regelmäßig wiederkehrend erledigt werden müssen (Akkus aufladen, Aggregate problelaufen lassen, etc.). Die anstehenden Aufgaben können auf einem Monitor angezeigt werden oder eine Divera-Benachrichtigung an eine pro Einheit hinterlegte Person auslösen, und mit einem einfachen Klick als erledigt markiert werden.

Weitere Module können einfach selbst erstellt werden: Das entsprechende Python-Skript in den Hauptordner legen, Konfigurationsdatei mit in den `config` Ordner, in die `main.conf` unter `modules` den Modulnamen hinzufügen und als aktiv markieren. Beim nächsten Start des Servers wird das Modul mitgeladen und initialisiert.

## divera_alarm
Das Modul initialisiert beim Start einen CEC Controller, mittels dem der Bildschirm angesteuert wird. Zum Debuggen kann die URL `/divera/debug/scan` einkommentiert werden indem in `divera_alarm.py` das `# ` vor der Zeile entfernt wird (sollte danach dann wieder auskommentiert werden). Über diese lässt sich dann mittels eines Webbrowsers das detektierte CEC-Netzwerk anzeigen. Es kann auf selber Weise die URL `/divera/debug/powerstatus` einkommentiert werden, welche den vom Bildschirm gemeldeten Zustand (angeschalten, anschaltend, ausschaltend, ausgeschalten, unbekannt) anzeigt.

Die Hauptansteuerung findet via POST-Request an die URL `/divera/alarm` mit einer JSON-Nachricht statt. Das Format entspricht dem des Divera-Webhooks welcher in Divera unter `Verwaltung > Schnittstellen > Datenübergabe > Webhooks` mit dem Inhalt `Vollständiges Objekt` angelegt werden kann. Es wird zur Zeit allerdings lediglich das `title` Element ausgewertet. Das in der Konfiguration angelegte secret (siehe unten, Einstellung `secret` in `divera_alarm.conf`) muss als URL-Parameter angefügt sein (`/divera/alarm?secret=...`), sonst wird der Request ignoriert.

Zusätzlich existiert noch die URL `/divera/manual`, welche bei Zugriff via Webbrowser den aktuellen Zustand kurz zusammenfässt und eine einfache Oberfläche zum manuellen an-/ausschalten des Bildschirms anbietet. Die entsprechenden URLs `/divera/manual/on` und `/divera/manual/off` können zur externen Automatisierung auch direkt mit GET-Requests angesteuert werden.

## divera_vehicle_status
Das Modul verbindet sich beim Start mit dem konfigurierten Email-Postfach, ruft vorhandene ungelesene Emails ab, bearbeitet diese und geht dann in eine Ruhezustand (IMAP IDLE) in dem es darauf wartet von dem Emailserver benachrichtigt zu werden dass eine neue Email eingetroffen ist. Beim Erhalt einer solchen Nachricht werden wieder alle ungelesenen Emails abgerufen und bearbeitet. Um eine Mehrfachbearbeitung von Emails zu vermeiden müssen Emails nach dem bearbeiten entweder auf gelesen gesetzt, in einen anderen Ordner verschoben, und/oder gelöscht werden. Wie mit Emails unter bestimmten Umständen umgegangen werden soll lässt sich in der Konfiguration festlegen (siehe unten, Einstellung `imapPostProcess` in `divera_vehicle_status.conf`).

Zum debuggen kann die URL `/vehicle_status/listvehicles` einkommentiert werden indem in `divera_vehicle_status.py` das `# ` vor der Zeile entfernt wird (sollte danach dann wieder auskommentiert werden). Über diese lässt sich dann mittels eines Webbrowsers eine Liste der in Divera hinterlegten Fahrzeuge inklusive deren Divera-ID anzeigen; die Divera-IDs werden für die Fahrzeugzuordnung zwischen STEIN und Divera benötigt (siehe unten, Einstellung `vehicleMapping` in `divera_vehicle_status.conf`).

## scheduled_maintenance
Das Modul ermöglicht es wiederkehrende Aufgaben wie z.B. regelmäßig Wartung zu hinterlegen und kurz vor deren Fälligkeit via Anzeige auf einem Monitor oder per Divera-Benachrichtigung informiert zu werden. Für jede Aufgabe können ein Name und eine optionalen Bemerkung hinterlegt werden, sowie das Datum der nächsten Fälligkeit, wie oft sie wiederholt werden soll, ab wann nach überschreiten der Fälligkeit sie als überfällig gilt, wie lange vor der Fälligkeit daran erinnert wird, und ob die Erinnerung per Anzeige und/oder Benachrichtigung geschehen soll. Die Option zur Benachrichtigung per Divera wird nur angezeigt wenn für die jeweilige Einheit ein Empfänger konfiguriert ist (siehe unten, Einstellung `units` in `scheduled_maintenance.conf`).

Das Modul generiert automatisch eine Anzeige für alle konfigurierten Einheiten (siehe unten, Einstellung `units` in `scheduled_maintenance.conf`) und deren anstehende Aufgaben. Diese kann über die URL `/maintenance` via Webbrowser aufgerufen werden. Standardmäßig kommt man hier zur Vollansicht, welche alle Daten anzeigt (alle Einheiten, alle Aufgaben unabhängig deren Zustands). Mit dem Link `Kurzansicht` kommt man auf eine Variante in welcher nur bald fällige Aufgaben angezeigt werden. Der Link `Vollansicht` wechselt wieder auf die vorherige Ansicht zurück.

Aufgaben werden pro Einheit immer in der Reihenfolge der nächsten Fälligkeit angezeigt; ihre Farbe zeigt an in welchem Zustand sie sind.
* Grüne Aufgaben sind erledigt und stehen noch nicht wieder an.
* Blaue Aufgaben befinden sich bereits innerhalb des Erinnerungszeitraums vor der Fälligkeit; wenn eine Divera-Benachrichtigung für sie konfiguriert ist wird oder wurde diese bereits verschickt.
* Gelbe Aufgaben haben ihr Fälligkeitsdatum bereits erreicht, aber noch nicht das Überfälligkeitsdatum.
* Rote Aufgaben sind überfällig.
* Graue Aufgaben sind deaktiviert; sie werden weder in der Gesamtübersicht angezeigt noch werden für sie Benachrichtigungen verschickt, unabhängig ihrer Fälligkeit.

Die Namen der Einheiten können angeklickt werden um zur Übersicht der Aufgaben dieser Einheit zu gelangen; dort werden immer alle Aufgaben der Einheit angezeigt. Hier können Aufgaben als erledigt markiert werden. Standardmäßig ist der aktuelle Tag ausgewählt, aber man kann die Erledigung auch rückdatieren. Mit einem Klick auf den Button `Erledigt` wird das nächste Fälligkeitsdatum auf den Tag gesetzt, welcher dem selektierte Erledigungsdatum plus der in der Aufgabe eingestellten Wiederholungsdauer entspricht. Ebenso können hier neue Aufgaben für die Einheit angelegt werden.

Mit einem Klick auf eine Aufgabe, entweder von der Gesamtübersicht oder einer Einheitsübersicht, kann man die Aufgabe bearbeiten. Alle Daten können geändert, sowie die gesamte Aufgabe aktiviert/deaktiviert oder gelöscht werden.

Zum Anlegen, Bearbeiten oder Löschen von Aufgaben muss das Bearbeitungspasswort eingegeben werden (siehe unten, `editPassword` in `scheduled_maintenance.conf`). Wenn dies einmal geschehen ist wird die Anmeldung im Browser gespeichert und muss fortan nicht mehr eingegeben werden. Sie kann durch löschen der cookies für die Seite wieder zurückgesetzt werden.  

Mittels der URLs `/maintenance/overview/full/embed` bzw. `/maintenance/overview/concise/embed` können respektive die Vollansicht oder Kurzansicht in einen Divera-Monitor oder eine eigene Webseite zur Anzeige via iFrame eingebunden werden. Bei den embeds werden alle interaktiven Elemente (Link zum wechseln zwischen Voll- und Kurzansicht, klicken auf Einheiten und Aufgaben, Änderung des Mauszeigers) entfernt bzw. deaktiviert sowie der Hintergrund auf transparent gesetzt.

Die URL `/maintenance/cron_notify` dient dem Auslösen der Divera-Benachrichtigung. Beim Aufruf dieser URL via POST-Request wird für Aufgaben, welche ihr Erinnerungsdatum erreicht haben, für deren Einheit ein Empfänger hinterlegt ist (siehe unten, Einstellung `units` in `scheduled_maintenance.conf`), für die ausgewählt ist dass die Erinnerung per Divera geschehen soll, und noch keine Benachrichtigung für dieses Fälligkeitsdatum verschickt wurde, eine Benachrichtigung an den hinterlegten Divera-Benutzer verschickt. Die Benachrichtigungen sind nur für den Empfänger sichtbar und werden nach einem konfigurierbaren Zeitraum (siehe unten, `archiveAfter` in `scheduled_maintenance.conf`) automatisch archiviert. Es empfiehlt sich diese URL automatisiert regelmäßig aufzurufen, z.B. einmal pro Tag via eines cron job mit `curl -X POST https://<hostname:port>/maintenance/cron_notify`.

# Konfiguration
## Allgemein
Für alle Module sind Beispielkonfigurationen mitgeliefert. Diese befinden sich im `config` Ordner mit dem Dateinamenpräfix `example_` vor dem Namen des entsprechenden Moduls. Um sie zu verwenden die Datei umbenennen oder kopieren, `example_` aus dem Dateinamen entfernen sodass der Name dem des Moduls gleicht, und die Konfiguration mit den OV-eigenen Daten anpassen (Details zu spezifischen Modulen siehe unten).

**Fett** gedruckte Einstellungen müssen zwingend auf die OV-eigenen Daten angepasst werden damit das Modul funktioniert. Gewisse Grundkenntnisse in der Funktionsweise und Konfiguration von Servern werden hier leider vorausgesetzt; eine volle Erklärung der Grundlagen würde den Rahmen sprengen. Es sollte aber selbst recht minimales Wissen ausreichen.  

## main.conf
* `hostname` und `port`: Einstellungen auf welchem host und port der Server läuft. `0.0.0.0` entspricht IPv4; um unter IPv6 zu laufen ist `hostname` in eckigen Klammern anzugeben, z.B. `[::]`. Der Server sollte entsprechend gängiger best practices nicht als root laufen, stattdessen sollte eine reverse proxy vorgeschaltet werden um einen Zugang via Port 80 (HTTP) oder 443 (HTTPS) zu ermöglichen.
* `keyfile` und `certfile`: Respektive private key und certificate für HTTPS-Verbindungen. Ein automatisches Zertifikatsmanagment via LetsEncrypt + certbot o.ä. ist empfohlen.
* **`modules`**: Vorhandene Module und ob sie geladen werden sollen (`true`) oder nicht (`false`). In der Beispielkonfiguration sind standardmäßig alle deaktiviert; gewünschte als aktiv markieren. Es wird empfohlen dies initial schrittweise zu tun um die Modul-Konfigurationen einzeln testen zu können.
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

## scheduled_maintenance.conf
* **`units`**: Für welche Einheiten es möglich sein soll Aufgaben anzulegen. Pro Einheit kann zur Zeit der Fremdschlüssel eine Person hinterlegt werden welche für Aufgaben dieser Einheit, wenn konfiguriert, Erinnerungsmitteilungen per Divera erhält wenn eine Aufgabe fällig wird. Wenn keiner hinterlegt ist ist es für Aufgaben dieser Einheit nicht möglich die Option der Benachrichtigung auszuwählen. Fremdschlüssel können in Divera in der Benutzerverwaltung durch Bearbeiten des Benutzers unter `Extras` hinterlegt werden.
* **`editPassword`**: Passwort das benötigt wird um Aufgaben anzulegen, zu ändern, und zu löschen. Nicht notwendig um eine Aufgabe als erledigt zu markieren. Es wird empfohlen das Passwort sehr einfach zu halten.
* **`cookieSecret`**: Zeichenketten mit dem das Passwort im Browser automatisch verschlüsselt wird um nicht im Klartext auslesbar zu sein. Kann eine zufällige Zeichenkette sein, muss nie von Benutzern selbst eingegeben werden.
* `refreshEmbed`: Dauer in Minuten nach dem sich die Übersichten im embed-Modus selbst neu aufrufen, um Änderungen anzuzeigen.
* `notify`: Einstellungen zur Benachrichtigung via Divera
  * `usersEndpoint`: API-URL zum Abruf der in Divera hinterlegten Benutzer. Sollte nur angepasst werden müssen falls Divera seine API ändert.
  * `notifyEndpoint`: API-URL zum Versenden der Divera-Benachrichtigungen. Sollte nur angepasst werden müssen falls Divera seine API ändert.
  * **`accesskey`**: Der Accesskey eines Divera-Systembenutzers welcher die Benachrichtigungen versendet (anlegen in Divera unter `Verwaltung > Schnittstellen > System-Benutzer`).
  * `httpTimeout`: Dauer in Sekunden bis ein Versuch eine Benachrichtigung per Divera zu versenden fehlschlägt.
  * `archiveAfter`: Dauer in Tagen bis eine Benachrichtigung automatisch archiviert wird.
  * `json`: Struktur der an Divera zur Benachrichtigung übergebenen Daten. Sollte nur angepasst werden müssen falls Divera seine API ändert.
* `logLevel`: Ab welchem Level dieses Modul Logmeldung weiterreichen soll. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
* `logLevelUrllib`: Ab welchem Level die Logmeldungen der verwendeten Urllib-Library weitergereicht werden sollen. Loglevel sind `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

# Dependencies
* Python 3.10+

## Python packages (Installation via pip o.ä.)
Werden nur benötigt wenn das jeweilige Modul aktiviert ist.
### Allgemein
* bottle

### divera_alarm
* cec
* simplejson

### divera_vehicle_status
* IMAPClient

### scheduled_maintenance
* python-dateutil
* simplejson
