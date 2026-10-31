% name = row["Name"]
% rebase("./templates/maintenance/base.tpl", title=f"Aufgabe {name} von {unit} bearbeiten")
<header class="page_header">
    <div>
        <button onclick="window.location.href='/maintenance'" style="margin-top: 10px;">Zurück</button>
    </div>
    <h1 class="unit_name">
        <span style="color: #AAA;">Aufgabe</span><span> {{name}} </span><span style="color: #AAA;">von</span><span> {{unit}} </span><span style="color: #AAA;">bearbeiten</span>
    </h1>
    <form action="/maintenance/unit/{{unit}}/task/{{task}}/delete" method="post" onsubmit="return window.confirm('Sind Sie sicher dass Sie Aufgabe {{name}} von {{unit}} löschen wollen?')">
        <button type="submit" value="delete" class="delete">(<span style="text-decoration: underline;">Löschen</span>)</button>
    </form>
</header>
<form action="/maintenance/unit/{{unit}}/task/{{task}}/edit" method="post">
    <table class="t_tasks" style="margin-top: 20px;">
        <tr>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="TaskActive">Aktiv</label>
                </div>
            </td>
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
                    <label for="TaskType">Aufgabenart</label>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <label for="DueDate">Nächste Fälligkeit</label>
                </div>
            </td>
            <td class="td_edit" id="RepeatHeader">
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
                    <input type="checkbox" name="TaskActive" {{"checked" if row["Active"] else ""}}>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <input type="text" name="Name" id="TaskName" value="{{name}}" size="25" required>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <textarea name="Description" id="TaskDescription" rows="2" cols="30" placeholder="(optional, z.B. Aufbewahrungsort Ladekabel, Füllhöhe, etc.)">{{row['Description']}}</textarea>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <select name="TaskType" id="TaskType">
                        <option value="recurring" {{"selected" if row["TaskType"] == "recurring" else ""}}>Wiederkehrend</option>
                        <option value="one_time" {{"selected" if row["TaskType"] == "one_time" else ""}}>Einmalig</option>
                    </select>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    <input type="date" name="DueDate" id="DueDate" value="{{row['DueDate']}}" required>
                </div>
            </td>
            <td class="td_edit" id="RepeatFields">
                <div class="table_centered">
                    % v, u = row["RepeatOffset"].split(" ")
                    % repeat_value = v if row["TaskType"] == "recurring" else "1"
                    <input type="number" name="RepeatValue" id="RepeatOffset" value="{{repeat_value}}" min="1" size="2" required style="text-align: center;">
                    <select name="RepeatUnit" id="RepeatUnit" required style="margin-left: 5px;">
                        <option value="days" {{"selected" if u == "days" else ""}}>Tage</option>
                        <option value="weeks" {{"selected" if u == "weeks" else ""}}>Wochen</option>
                        <option value="months" {{"selected" if u == "months" else ""}}>Monate</option>
                        <option value="years" {{"selected" if u == "years" else ""}}>Jahre</option>
                    </select>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    % v, u = row["OverdueOffset"].split(" ")
                    <input type="number" name="OverdueValue" id="OverdueOffset" value="{{v}}" min="0" size="2" required style="text-align: center;">
                    <select name="OverdueUnit" required style="margin-left: 5px;">
                        <option value="days" {{"selected" if u == "days" else ""}}>Tage</option>
                        <option value="weeks" {{"selected" if u == "weeks" else ""}}>Wochen</option>
                        <option value="months" {{"selected" if u == "months" else ""}}>Monate</option>
                        <option value="years" {{"selected" if u == "years" else ""}}>Jahre</option>
                    </select>
                </div>
            </td>
            <td class="td_edit">
                <div class="table_centered">
                    % v, u = row["NotifyOffset"].split(" ")
                    <input type="number" name="NotifyValue" id="NotifyOffset" value="{{v}}" min="0" size="2" required style="text-align: center;">
                    <select name="NotifyUnit" required style="margin-left: 5px;">
                        <option value="days" {{"selected" if u == "days" else ""}}>Tage</option>
                        <option value="weeks" {{"selected" if u == "weeks" else ""}}>Wochen</option>
                        <option value="months" {{"selected" if u == "months" else ""}}>Monate</option>
                        <option value="years" {{"selected" if u == "years" else ""}}>Jahre</option>
                    </select>
                </div>
            </td>
            <td class="td_edit" rowspan="{{'2' if notify_receiver else '1'}}" style="padding-left: 0px;">
                <div class="table_centered" {{!"style=\"margin-bottom: 8px;\"" if notify_receiver else ""}}>
                    <table style="border-collapse: collapse;">
                        <tr>
                            <td>
                                <input type="checkbox" id="NotifyShow" name="NotifyShow" {{"checked" if row["NotifyShow"] else ""}}>
                            </td>
                            <td>
                                <label for="NotifyShow">Anzeige in Kurzansicht</label>
                            </td>
                        </tr>
                    % if notify_receiver:
                        <tr>
                            <td style="vertical-align: top;">
                                <input type="checkbox" id="NotifyMessage" name="NotifyMessage" {{"checked" if row["NotifyMessage"] else ""}}>
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
            <td colspan="5" class="td_edit"></td>
            <td class="td_edit" id="RepeatExplanation">
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
            <td colspan="9" class="td_edit">
                <div class="table_centered">
                    <input value="Speichern" type="submit" style="margin-top: 20px;"/>
                </div>
            </td>
        </tr>
    </table>
</form>
<script>
    function toggleRepeatFields() {
        const recurring = document.getElementById("TaskType").value === "recurring";
        document.getElementById("RepeatOffset").disabled = !recurring;
        document.getElementById("RepeatUnit").disabled = !recurring;
        document.getElementById("RepeatHeader").hidden = !recurring;
        document.getElementById("RepeatFields").hidden = !recurring;
        document.getElementById("RepeatExplanation").hidden = !recurring;
    }
    document.getElementById("TaskType").addEventListener("change", toggleRepeatFields);
    toggleRepeatFields();
</script>