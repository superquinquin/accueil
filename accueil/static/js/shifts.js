

const websocket = new WebSocket("ws://" + location.host + '/registration');


websocket.addEventListener("message", (event) => {
    let payload = JSON.parse(event.data);

    // event shift unrelated & without data. implies an early return.
    switch (payload.message) {
        case "reload":
            window.location.reload();
            return;
    }



    let data = payload.data
    let existing_shifts =  referenced_shifts_ids();

    if (!existing_shifts.includes(data.shift_id)) {
        return;
    }

    switch (payload.message) {
        case "attend":
            member = document.getElementById(data.registration_id);
            member.setAttribute('onclick', "askConfirmationReset("+data.registration_id+")");
            member.setAttribute("state", "done");
            member.className = "";
            member.classList.add("done");
            member.innerHTML += "<span>✓</span>";
            break;
        case "reset":
            member = document.getElementById(data.registration_id);
            member.setAttribute('onclick', "askConfirmation("+data.registration_id+")");
    
            let spans = member.getElementsByTagName("span");
            if (spans.length == 1) {
                spans[0].remove()
            } else {
                spans[1].remove()
            }
    
            member.setAttribute("state", "open");
            member.className = "";
            member.classList.add("open");
            break;
        case "closeCmodal":
            CloseCModal();
            break;
        case "registrate":
            console.log(data);
            let shift = document.getElementById(data.shift_id.toString());
            let container = shift.getElementsByTagName("ul")[0];
            container.innerHTML += data.html;
            break;
        case "CloseCatchingUpModal":
            CloseCatchingUpModal();
            break;
        case "error":
            break;
        default:
            console.log("unknown case.");
    }
  });


// NOTING ATTENDANCIES
function askConfirmation(registration_id) {
    let member = document.getElementById(registration_id);
    let partner_id = parseInt(member.getAttribute('partner_id'));
    let shift_id = parseInt(member.getAttribute('shift_id'));

    let body = "Bonjour "+member.innerHTML.split('-')[1]+ "\nVeuillez confirmer votre présence";
    let payload = registration_id+", "+partner_id+", "+shift_id;
    openCModal(
        "Confirmation de présence",
        body,
        "confirmedPresence("+payload+")"
    );
}

async function confirmedPresence(registration_id, partner_id, shift_id) {
    websocket.send(JSON.stringify({"message": "attend", data: {"registration_id": registration_id, "partner_id": partner_id, "shift_id": shift_id}}));
}

// NOTING RESET ATTENDANCIES
function askConfirmationReset(registration_id) {
    let member = document.getElementById(registration_id);
    let partner_id = parseInt(member.getAttribute('partner_id'));
    let shift_id = parseInt(member.getAttribute('shift_id'));

    let body = "Bonjour, Voullez vous annuler la présence de "+member.innerHTML.split('-')[1].split("✓")[0];
    let payload = registration_id+", "+partner_id+", "+shift_id;
    openCModal(
        "Annuler sa présence",
        body,
        "confirmedReset("+payload+")"
    );
}

async function confirmedReset(registration_id, partner_id, shift_id) {
    websocket.send(JSON.stringify({"message": "reset", data: {"registration_id": registration_id, "partner_id": partner_id, "shift_id": shift_id}}));
}



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

function referenced_shifts_ids() {
    let shifts = document.getElementsByClassName("shift");
    let shift_ids = [];
    for (var shift of shifts) {
        shift_ids.push(parseInt(shift.getAttribute("shift_id")));
    }
    return shift_ids;
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

async function searchMember(id) {
    let loading = document.getElementById("loading");
    loading.style.display = "block";

    let value = document.getElementById(id).value;
    payload = {
        method: "POST", 
        mode: "cors", 
        cache: "no-cache", 
        credentials: "same-origin", 
        headers: {"Content-Type": "application/json"}, 
        redirect: "follow", 
        referrerPolicy: "no-referrer",
        body: JSON.stringify({"input": value})
    };
    const response = await fetch("./registration/search_member", payload);
    const data = await response.json();

    loading.style.display = "none";

    if (response.status != 200) {
        console.log(data.data);

    } else {
        console.log(data.data);
        if (data.data.length > 0) {
            let container = document.getElementById("member-list");
            let ul = document.createElement("ul");
            for (var member of data.data) {
                let display_name = member.barcode_base+" - "+member.name
                let elm = '<li class="li-member" partner_id="'+member.partner_id+'" barcode="'+member.barcode_base+'"><input type="checkbox" onclick="OnlyOneCheckRemain(this)"><span>'+display_name+'</span></li>';
                ul.innerHTML += elm;
            }
            container.appendChild(ul);
        } else {
            let container = document.getElementById("member-list");
            let ul = document.createElement("ul");
            let elm = "<li>Aucun résultat</li>"
            ul.innerHTML += elm;
            container.appendChild(ul);
        }
    }

}

function registerCatchUp() {
    let container = document.getElementById('member-list');
    for (li of container.getElementsByClassName("li-member")) {
        if (li.firstChild.checked) {
            let context = {
                "shift_id": parseInt(container.classList[0]),
                "partner_id": parseInt(li.getAttribute("partner_id")),
            }
            websocket.send(JSON.stringify({"message": "registrate", "data": context}));
        }
    }
    // CloseCatchingUpModal()
}

function OnlyOneCheckRemain(elm) {
    let ul = elm.parentNode.parentNode
    let id = elm.parentNode.getAttribute("partner_id");
    for (li of ul.getElementsByClassName('li-member')) {
        let other_id = li.getAttribute("partner_id");
        if (id != other_id) {
            li.firstChild.checked = false;
        }
    }
}