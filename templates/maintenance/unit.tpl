% rebase("./templates/maintenance/base.tpl", title=unit)
% from datetime import date
% today = date.today()
<header class="page_header">
    <div>
        <button onclick="window.location.href='/maintenance/overview'" style="margin-top: 10px;">Zur Übersicht</button>
    </div>
    <h1 class="unit_name">
        {{unit}}
    </h1>
</header>
<div class="tasks_unit" style="align-items: center; margin-top: 10px;">
<% 
    for task in tasks:
    id = task["Id"]
    task_state = "task_inactive" if not task["Active"] else "task_overdue" if today >= task["OverdueDate"] else "task_due" if today >= task["DueDate"] else "task_notify" if today >= task["NotifyDate"] else "task_done"
%>
    <div class="tasks_item shrink_aware" onclick="window.location.href='/maintenance/unit/{{unit}}/task/{{id}}'">
        <div class="tasks_element {{task_state}}">
            <div>
                <div class="task_name">{{task["Name"]}}</div>
                <div class="task_desc">{{task["Description"]}}</div>
            </div>
        </div>
        <div class="tasks_element {{task_state}}">
            <div>
                <div class="table_centered date_header">
                    Fällig am
                </div>
                <div class="table_centered date">
                    {{task["DueDate"].strftime("%d.%m.%Y")}}
                </div>
            </div>
        </div>
        <div class="tasks_element {{task_state}}">
            <div>
                <div class="table_centered date_header">
                    Überfällig ab
                </div>
                <div class="table_centered date">
                    {{task["OverdueDate"].strftime("%d.%m.%Y")}}
                </div>
            </div>
        </div>
        <div class="tasks_element {{task_state}}" onclick="event.stopPropagation()">
            <div>
                <form action="/maintenance/unit/{{unit}}/task/{{id}}/done" method="post">
                    <div class="table_centered">
                        <input type="date" name="DoneDate" value="{{today}}" max="{{today}}" required style="text-align: center;">
                    </div>
                    <div class="table_centered" style="margin-top: 5px;">
                        <input type="submit" value="Erledigt"/>
                    </div>
                </form>
            </div>
        </div>
    </div>
% end
</div>
<div class="table_centered">
    <input type="button" onclick="window.location.href='/maintenance/unit/{{unit}}/new'" value="Neue Aufgabe" style="margin-top: 20px;"/>
</div>