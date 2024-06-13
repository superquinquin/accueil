
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

    let header = document.createElement("div");
    header.classList.add("shiftHeader");

    let title = document.createElement('h2');
    title.innerHTML = context.display_shift_name;
    header.appendChild(title);

    let catchUp = document.createElement("button");
    catchUp.classList.add("catchUpBtn");
    catchUp.setAttribute("onclick", "askCatchingUp("+context.shift_id+")");
    catchUp.innerHTML = "S'inscrire";
    header.appendChild(catchUp);

    shift.appendChild(header)

    let ul = document.createElement('ul');
    if (context.members.length > 0) {
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
                li.setAttribute('onclick', "askConfirmationReset("+m.registration_id+")");
                li.classList.add("done");
                let span = document.createElement("span");
                span.innerHTML = "✓";
                li.appendChild(span);
            }
            ul.appendChild(li);
        }
    } else {
        let li = document.createElement('li');
        li.classList.add("open");
        li.classList.add("placeholder");
        li.setAttribute("style", "text-align: center");
        li.innerHTML = "<strong>Aucun membre inscrit</strong>";
        ul.appendChild(li);
    }
    
    shift.appendChild(ul);
    document.body.appendChild(shift);
}


function rm_placeholder(container) {
    let plh = container.getElementsByClassName("placeholder");
    for (li of plh) {
        li.remove()
    }
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

function askConfirmationReset(registration_id) {
    let row = document.getElementById(registration_id);
    let member_id = parseInt(row.getAttribute('partner_id'));
    let shift_id = parseInt(row.getAttribute('shift_id'));

    let body = "Bonjour, Voullez vous annuler la présence de "+row.innerHTML.split('-')[1].split("✓")[0];
    let payload = registration_id+", "+member_id+", "+shift_id;
    openCModal(
        "Annuler sa présence",
        body,
        "confirmedReset("+payload+")"
    );
}


function confirmedPresence(reg_id, partner_id, shift_id) {
    socket.emit("confirm-presence", {"registration_id":reg_id, "partner_id": partner_id, "shift_id": shift_id})
    CloseCModal()
}

function confirmedReset(reg_id, partner_id, shift_id) {
    socket.emit("reset-presence", {"registration_id":reg_id, "partner_id": partner_id, "shift_id": shift_id})
    CloseCModal()
}


function askCatchingUp(shift_id) {
    document.getElementById("member-list").classList.add(shift_id);
    OpenCatchingUpModal()
}

function OpenCatchingUpModal() {
    console.log('modal open')
    window.scrollTo(0, window.scrollY); 
    document.getElementById('catchingUp-modal').style.top = (window.scrollY - 5).toString() + 'px';
    document.getElementById('catchingUp-modal').style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
}

function CloseCatchingUpModal() {
    let shift_id = document.getElementById("member-list").classList[0]
    document.getElementById('catchingUp-modal').style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    document.getElementById("member-list").innerHTML = "";
    document.getElementById("member-list").classList.remove(shift_id);
    document.getElementById("search-CatchinUp").value = "";

}

function searchMember(id) {
    let value = document.getElementById(id).value;
    socket.emit('search-member', {"input": value});
    let list = document.getElementById("member-list");
    list.innerHTML = "";
    list.innerHTML  = "Recherche en cours...";
}

function populateMemberList(context) {
    let container = document.getElementById("member-list");
    container.innerHTML = "";

    let ul = document.createElement("ul");
    for (var m of context.members) {
        let li = createCatchingUpMemberBubble(
            m[0],
            m[1], 
            m[2]
        );
        ul.appendChild(li);
    }
    container.appendChild(ul);
}


function createCatchingUpMemberBubble(p_id, brcd, p_name) {
    let li = document.createElement('li');
    li.setAttribute('partner_id', p_id);
    li.setAttribute('barcode', brcd);
    li.classList.add("li-member");

    let box = document.createElement("input");
    box.setAttribute("type", "checkbox");
    box.setAttribute("onclick", "OnlyOnCheckRemain(this)");

    let span = document.createElement("span");
    span.innerHTML = brcd + " - " + p_name;

    li.appendChild(box);
    li.appendChild(span);

    return li
}


function OnlyOnCheckRemain(elm) {
    let ul = elm.parentNode.parentNode
    let id = elm.parentNode.getAttribute("partner_id");
    for (li of ul.getElementsByClassName('li-member')) {
        let other_id = li.getAttribute("partner_id");
        if (id != other_id) {
            li.firstChild.checked = false;
        }
    }
}



function regiesterCatchUp() {
    let container = document.getElementById('member-list');
    for (li of container.getElementsByClassName("li-member")) {
        if (li.firstChild.checked) {
            let context = {
                "shift_id": container.classList[0],
                "partner_id": li.getAttribute("partner_id"),
            }
            socket.emit("register-catching-up", context);
        }
    }
    CloseCatchingUpModal()
}





// COMMON EVENTS

socket.on('update-on-presence', function(context) {
    console.log('updating status')
    let row = document.getElementById(context.registration_id);
    row.setAttribute('onclick', "askConfirmationReset("+context.registration_id+")");
    let span = document.createElement("span");
    span.innerHTML = "✓";

    row.setAttribute("state", "done");
    row.classList.remove("open");
    row.classList.add("done");
    row.appendChild(span);
});

socket.on('update-on-reset', function(context) {
    console.log('updating status')
    let row = document.getElementById(context.registration_id);
    row.setAttribute('onclick', "askConfirmation("+context.registration_id+")");
    let spans = row.getElementsByTagName("span");
    if (spans.length == 1) {
        spans[0].remove()
    } else {
        spans[1].remove()
    }
    row.setAttribute("state", "open");
    row.classList.add("open");
    row.classList.remove("done");
});



socket.on('populate-search-members', function(context) {
    console.log('updating members list');
    populateMemberList(context);
});


socket.on("add-catching-up-member-to-shift", function(context) {
    let container = document.getElementById(context.shift_id);
    rm_placeholder(container)
    let ul = container.getElementsByTagName('ul')[0];

    let m = context.members
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
        li.setAttribute('onclick', "askConfirmationReset("+m.registration_id+")");
        let span = document.createElement("span");
        span.innerHTML = "✓";
        li.appendChild(span);
    }
    ul.appendChild(li);
});