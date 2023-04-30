
socket.on('connect', function() {
    console.log('has connected');

    if (!charged) {
        console.log("filling page");
        socket.emit("all-shift-init");
    }
});



socket.on('load-init-data', function(context) {
    let body = document.body
    let ids = [];
    for (s of body.getElementsByClassName("shift")) {
        ids.push(s.id)
    }
    for (var shift of context) {
        if (!ids.includes(shift.shift_id)) {
            createShiftBubble(shift);
        }
    }
});


socket.on('update-on-presence', function(context) {
    console.log('updating status')
    let row = document.getElementById(context.registration_id);
    row.setAttribute("state", "done");
    row.setAttribute("state", "done");
    row.classList.remove("open");
    row.classList.add("done");
});