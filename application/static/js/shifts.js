
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
