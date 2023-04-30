
socket.on('connect', function() {
    console.log('has connected');

    if (!charged) {
        console.log("filling page");
        socket.emit("shift-init");
    }
});



socket.on('load-init-data', function(context) {

    for (var shift of context) {
        console.log(shift.shift_id)
        createShiftBubble(shift);
    }
})


socket.on('update-on-presence', function(context) {
    console.log('updating status')
    let row = document.getElementById(context.registration_id);
    row.setAttribute("state", "done");
    row.classList.remove("open");
    row.classList.add("done");
});