% rebase("./templates/maintenance/base.tpl", title=f"Neue Aufgabe für {unit}")
% from datetime import date
% today = date.today()
<header class="page_header">
    <div>
        <button onclick="window.location.href='/maintenance/unit/{{unit}}'" style="margin-top: 10px;">Zurück</button>
    </div>
    <h1 class="unit_name">
        <span style="color: #AAA;">Neue Aufgabe für</span> {{unit}}
    </h1>
</header>
<form action="/maintenance/unit/{{unit}}/new" method="post">
    <table class="t_tasks" style="margin-top: 20px;">
        <tr>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="TaskName">Aufgabe</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="TaskDescription">Bemerkung</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="DueDate">Nächste Fälligkeit</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="RepeatOffset">Wiederholen alle</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="OverdueOffset">Überfällig ab</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="NotifyOffset">Erinnern ab</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label>Erinnern per</label>
                </div>
            </td>
        </tr>
        <tr>
            <td class="td_edit">
                <div class="table_centered">
                    <input type="text" name="Name" id="TaskName" size="25" required>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <textarea name="Description" id="TaskDescription" rows="2" cols="30" placeholder="(optional, z.B. benötigter Füllstand, Aufbewahrungsort Ladekabel, etc.)"></textarea>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <input type="date" name="DueDate" id="DueDate" value="{{today}}" required>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <input type="number" name="RepeatValue" id="RepeatOffset" min="1" size="2" required style="text-align: center;">
                    <select name="RepeatUnit" required style="margin-left: 5px;">
                        <option value="days">Tage</option>
                        <option value="weeks">Wochen</option>
                        <option value="months" selected>Monate</option>
                        <option value="years">Jahre</option>
                    </select>
                </div>
            </td>
            <td class="td_edit">                
                <div class="table_centered">
                    <input type="number" name="OverdueValue" id="OverdueOffset" min="0" size="2" required style="text-align: center;">
                    <select name="OverdueUnit" required style="margin-left: 5px;">
                        <option value="days">Tage</option>
                        <option value="weeks">Wochen</option>
                        <option value="months" selected>Monate</option>
                        <option value="years">Jahre</option>
                    </select>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <input type="number" name="NotifyValue" id="NotifyOffset" min="0" size="2" required style="text-align: center;">
                    <select name="NotifyUnit" required style="margin-left: 5px;">
                        <option value="days">Tage</option>
                        <option value="weeks">Wochen</option>
                        <option value="months" selected>Monate</option>
                        <option value="years">Jahre</option>
                    </select>
                </div>
            </td>
            <td class="td_edit" rowspan="{{'2' if notify_receiver else '1'}}" style="padding-left: 0px;">
                <div class="table_centered" {{!"style=\"margin-bottom: 8px;\"" if notify_receiver else ""}}>
                    <table style="border-collapse: collapse;">
                        <tr>
                            <td>
                                <input type="checkbox" id="NotifyShow" name="NotifyShow" checked>
                            </td>
                            <td>
                                <label for="NotifyShow">Anzeige in Kurzansicht</label>
                            </td>
                        </tr>
                    % if notify_receiver:
                        <tr>
                            <td style="vertical-align: top;">
                                <input type="checkbox" id="NotifyMessage" name="NotifyMessage">
                            </td>
                            <td style="padding-top: 3px;">
                                <label for="NotifyMessage">Benachrichtigung an<br>{{notify_receiver}}</label>
                            </td>
                        </tr>
                    % end
                    </table>
                </div>
            </td>
        </tr>
        <tr>
            <td colspan="3" class="td_edit"></td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="RepeatOffset">nach Erledigung</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="OverdueOffset">nach Fälligkeitsdatum</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="NotifyOffset">vor Fälligkeitsdatum</label>
                </div>
            </td>
            
        </tr>
        <tr>
            <td colspan="7" class="td_edit">
                <div class="table_centered">
                    <input value="Speichern" type="submit" style="margin-top: 20px;"/>
                </div>
            </td>
        </tr>
    </table>
</form>