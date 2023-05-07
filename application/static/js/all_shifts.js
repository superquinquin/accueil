
socket.on('connect', function() {
    console.log('has connected');

    if (!charged) {
        console.log("filling page");
        socket.emit("all-shift-init");
    }
});



socket.on('load-init-data', function(context) {
    console.log(context)
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

