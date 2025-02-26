% rebase("./templates/maintenance/base.tpl", title="Login")
<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 60vh;">
% if defined("failed"):
    <div style="margin-bottom: 10px;">
        Falsches Passwort!
    </div>
% end
    <div>
        <form action="/maintenance/login" method="post">
            Passwort: <input name="Password" type="password" />
            <input value="Login" type="submit" />
        </form>
    </div>
</div>