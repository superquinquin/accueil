
var charged = isItCharged()
const socket = io.connect(config.ADDRESS);


function isItCharged() {
    let charged;
    let body = document.getElementById("body");
    let shifts = body.getElementsByClassName("shift");
    if (shifts.length > 0) {
        charged = true;
    } else {
        charged = false;
    }
    return charged
}

function createShiftBubble(context) {

    let shift = document.createElement('div');
    shift.classList.add('shift');
    shift.setAttribute('id',context.shift_id);

    let title = document.createElement('h2');
    title.innerHTML = context.display_shift_name;
    shift.appendChild(title);

    let ul = document.createElement('ul');
    for (var m of context.members) {
        let li = document.createElement('li');
        li.setAttribute('shift_id', context.shift_id)
        li.setAttribute('partner_id', m.id);
        li.setAttribute('state', m.state);
        li.setAttribute('id', m.registration_id);

        li.innerHTML = m.display_name;
        if (m.state != "done") {
            li.setAttribute('onclick', "askConfirmation("+m.registration_id+")");
            li.classList.add("open");
        } else {
            li.classList.add("done");
            let span = document.createElement("span");
            span.innerHTML = "✓";
            li.appendChild(span);
        }
        ul.appendChild(li);
    }
    shift.appendChild(ul);
    document.body.appendChild(shift);
}






/////// CONFIRMATION MODAL
function rescaleCModalContainer(action) {
    let ch = document.getElementById('confirmation-container').clientHeight;
    let cw = document.getElementById('confirmation-container').clientWidth;
    let h = document.getElementById('confirmation-container').style.height;
    let w = document.getElementById('confirmation-container').style.width;
    // apply rescaling for computer screen on error modal
    if (action == "open" && ch == 250 && cw == 300) {
      document.getElementById('confirmation-container').style.height = "80%";
      document.getElementById('confirmation-container').style.width = "50%";
    } else if (action == "open" && h == "80%" && w == "50%") {
      document.getElementById('confirmation-container').style.height = "250px";
      document.getElementById('confirmation-container').style.width = "300px";
    } else if (action == "close") {
      document.getElementById('confirmation-container').style.height = "250px";
      document.getElementById('confirmation-container').style.width = "300px";
    }
  }


function openCModal(headerMsg, bodyMsg, closeFunc) {
    console.log('modal open')
    window.scrollTo(0, window.scrollY); 
    document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
    document.getElementById('confirmation-hub-modal').style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    document.getElementById('heading-message').innerHTML = headerMsg;
    document.getElementById('content-message').innerHTML = bodyMsg;
    // rescaleCModalContainer()
    document.getElementById('accept-confirmation').setAttribute('onclick', closeFunc);
}

function CloseCModal() {
    document.getElementById('confirmation-hub-modal').style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    document.getElementById('cancel-confirmation').hidden = false;
    document.getElementById('accept-confirmation').hidden = false;
    // rescaleCModalContainer("close")
}


function askConfirmation(registration_id) {
    let row = document.getElementById(registration_id);
    let member_id = parseInt(row.getAttribute('partner_id'));
    let shift_id = parseInt(row.getAttribute('shift_id'));

    let body = "Bonjour "+row.innerHTML.split('-')[1]+ "\nVeuillez confirmer votre présence";
    let payload = registration_id+", "+member_id+", "+shift_id;
    openCModal(
        "Confirmation de présence",
        body,
        "confirmedPresence("+payload+")"
    );
}


function confirmedPresence(reg_id, partner_id, shift_id) {
    socket.emit("confirm-presence", {"registration_id":reg_id, "partner_id": partner_id, "shift_id": shift_id})
    CloseCModal()
}
