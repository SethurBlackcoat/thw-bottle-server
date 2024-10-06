<div style="background-color: rgb(0, 8, 15); font-size: 24; font-family: Arial; color: rgb(255, 255, 255)">
    <p>Last action: [{{last_action}}] at [{{last_action_time}}] from source [{{last_action_source}}]</p>
    <p>{{power_status}}</p>

    <p>
        <button type="button" onclick="submitOn()" style="height: 50px; width: 100px;">Screen On</button>
        <button type="button" onclick="submitOff()" style="height: 50px; width: 100px;">Screen Off</button>
    </p>
</div>


<script type="application/javascript">
    function submitOn() {
        const request = new XMLHttpRequest();
        request.onreadystatechange = () => { if (request.readyState == XMLHttpRequest.DONE) { reload(); } }
        request.open("GET", location.href + "/on");
        request.send();
    }
    
    function submitOff() {
        const request = new XMLHttpRequest();
        request.onreadystatechange = () => { if (request.readyState == XMLHttpRequest.DONE) { reload(); } }
        request.open("GET", location.href + "/off");
        request.send();
    }

    function reload() {
        setTimeout(() => { location.reload(); }, 2000)
    }
</script>