<!DOCTYPE html>
% embedded = defined("embed") and embed
<html>
    <head>
        <title>{{title}}</title>
        <style>
            .tasks_container {
                display: flex;
                flex-direction: column;
                flex-wrap: wrap;
                align-content: space-evenly;
                height: 92vh;
            }
            .tasks_unit {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .tasks_item {
                display: flex;
                cursor: default;
                min-width: 20vw;
                max-width: 60vw;
                word-break: break-word;
            }
            .tasks_element {
                padding: 5px 25px;
                text-shadow: 1px 1px 1px rgba(0,0,0,.5);
                display: flex;
                align-items: center;
            }
            .tasks_item .tasks_element:first-child {
                border-bottom-left-radius: 5px;
                border-top-left-radius: 5px;
                padding-left: 10px;
                flex-grow: 1;
            }
            .tasks_item .tasks_element:last-child {
                border-bottom-right-radius: 5px;
                border-top-right-radius: 5px;
                padding: 10px;
                padding-left: 25px;
            }
            .t_tasks {
                margin: auto;
                border-spacing: 0px 5px;
            }
            .td_edit {
                padding: 0px 10px;
            }
            .page_header, .unit_header {
                text-align: center;
            }
            .unit_name {
                font-size: 3em;
                margin: 25px 0px 0px;
                cursor: default;
            }
            .task_name {
                font-size: 2em;
            }
            .task_desc {
                font-size: 0.8em;
                font-weight: normal;
            }
            .task_inactive {
                background-color: #3e3e3e;
            }
            .task_done {
                background-color: #009329;
            }
            .task_notify {
                background-color: blue;
            }
            .task_due {
                background-color: #ffca00;
            }
            .task_overdue {
                background-color: #800035;
            }
            .date {
                font-size: 1.5em;
                word-break: normal;
            }
            .date_header {
                letter-spacing: 0.02em;
            }
            .table_centered {
                display: flex;
                justify-content: center;
                white-space: nowrap;
            }
            input, textarea, select {
                font-family: Arial,sans-serif;
            }
            input[type="number"] {
                max-width: 5ch;
            }
            input, select, button {
                font-size: 1.2em;
                line-height: 1.5em;
            }
            button {
                background: none;
                border: none;
                padding: 0;
                color: white;
                text-decoration: underline;
                cursor: pointer;
            }
            button:hover {
                color: #AAA;
            }
            button.delete {
                text-decoration: none;
                color: #800035;
                font-weight: bold;
            }
            button.delete:hover {
                color: red;
            }
            textarea {
                font-size: 0.8em;
                line-height: 1.05em;
            }
            body {
                font-family: Arial,sans-serif;
                font-weight: bold;
                color: white;
            }
            body.background {
                background-color: #00080F;
            }
            div.background::before {
                position: fixed;
                top: -80%;
                right: -20%;
                left: -20%;
                z-index: -1;
                height: 150%;
                min-height: 400px;
                background-image: radial-gradient(#00378a 0,#00080F 70%,#00080F);
                content: "";
            }
            div.noninteractive:hover {
                filter: none;
            }
        </style>
        % if not embedded:
        <style>
            .unit_header .unit_name:hover {
                cursor: pointer;
                color: #AAA;
            }
            .tasks_item:hover {
                filter: drop-shadow(0px 0px 2px white);
            }
            .shrink_aware {
                width: 75%;
            }
            @media (max-width: 1280px), (max-height: 720px) {
                .tasks_container {
                    height: auto;
                }
            }
            @media (max-width: 1600px) {
                .shrink_aware {
                    width: 90%;
                    max-width: none;
                    word-break: normal;
                }
            }
        </style>
        % end
    </head>
    <body {{!'' if embedded else 'class="background"'}}>
        <div id="content" {{!'' if embedded else 'class="background"'}}>
            {{!base}}
        </div>
    </body>
</html>