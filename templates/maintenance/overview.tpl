% rebase("./templates/maintenance/base.tpl", title="Übersicht")
% from datetime import date
% today = date.today()
<header class="page_header">
% if embed:
    <script>
        setTimeout(() => { window.location.reload() }, "{{refresh}}")
    </script>
% else:
    <div>
        <button {{!f"onclick=\"window.location.href='/maintenance/overview{'/full' if concise else '/concise'}'\""}} style="margin-top: 10px;">{{'Vollansicht' if concise else 'Kurzansicht'}}</button>
    </div>
% end
</header>
<div class="tasks_container" {{!"style='height: auto'" if len(tasks) + sum(max(1, len(l)) for l in tasks.values()) > 24 else ""}}>
<%
    for unit in tasks:
    if tasks[unit] or not concise:
%>
    <div class="tasks_unit">
        <header class="unit_header" {{!"" if embed else f"onclick=\"window.location.href='/maintenance/unit/{unit}'\""}}>
            <h1 class="unit_name">
                {{unit}}
            </h1>
        </header>
    % if not tasks[unit]:
        <div class="tasks_item noninteractive">
            <div class="tasks_element task_inactive">
                <div style="margin: auto; font-size: 1.5em;">
                    Nichts anstehend
                </div>
            </div>
        </div>
    % else:
    <%
        for task in tasks[unit]:
        id = task["Id"]
        task_state = "task_inactive" if not task["Active"] else "task_overdue" if today >= task["OverdueDate"] else "task_due" if today >= task["DueDate"] else "task_notify" if today >= task["NotifyDate"] else "task_done"
    %>
        <div class="tasks_item" {{!"" if embed else f"onclick=\"window.location.href='/maintenance/unit/{unit}/task/{id}/view'\""}}>
            <div class="tasks_element {{task_state}}">
                <div>
                    <div class="task_name">
                        {{task["Name"]}}
                    </div>
                    <div class="task_desc">
                        {{task["Description"]}}
                    </div>
                </div>
            </div>
            <div class="tasks_element date {{task_state}}" style="display:flex; align-items:center; justify-content: right;">
                <div>
                    {{task["DueDate"].strftime("%d.%m.%Y")}}
                </div>
            </div>
        </div>
    % end
    % end
    </div>
% end
% end
</div>