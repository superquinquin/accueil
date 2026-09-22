let url = new URL("/registration", window.location.href);
url.protocol = url.protocol.replace("http", "ws");
const websocket = new WebSocket(url.href);

websocket.addEventListener("message", (event) => {
  let payload = JSON.parse(event.data);

  // event shift unrelated & without data. implies an early return.
  switch (payload.message) {
    case "error":
      closeRegistrationModal();
      new MsgFactory(
        "msg-box",
        "err",
        "<strong>" + payload.data.reasons + "</strong>",
        true,
        3000,
        1000,
      );
      break;
    case "reload":
      window.location.reload();
      return;
  }

  let data = payload.data;
  let existing_shifts = referenced_shifts_ids();

  if (!existing_shifts.includes(data.shift_id)) {
    return;
  }

  switch (payload.message) {
    case "attend":
      member = document.getElementById(data.registration_id);
      member.setAttribute("onclick", "askConfirmationReset(" + data.registration_id + ")");
      member.setAttribute("state", "done");
      member.className = "";
      member.classList.add("done", "border-light");
      member.innerHTML += "<span>✓</span>";
      break;
    case "reset":
      member = document.getElementById(data.registration_id);
      member.setAttribute("onclick", "askConfirmation(" + data.registration_id + ")");

      let spans = member.getElementsByTagName("span");
      if (spans.length == 1) {
        spans[0].remove();
      } else {
        spans[1].remove();
      }

      member.setAttribute("state", "open");
      member.className = "";
      member.classList.add("open", "border-light");
      break;
    case "closeCmodal":
      CloseCModal();
      break;
    case "registrate":
      console.log(data);
      let shift = document.getElementById(data.shift_id.toString());
      let container = shift.getElementsByTagName("ul")[0];
      if (container.getElementsByClassName("placeholder").length > 0) {
        container.innerHTML = "";
      }
      container.innerHTML += data.html;
      break;
    case "closeRegistrationModal":
      closeRegistrationModal();
      break;
    default:
      console.log("unknown case.");
  }
});

// NOTING ATTENDANCIES
function askConfirmation(registration_id) {
  let member = document.getElementById(registration_id);
  let partner_id = parseInt(member.getAttribute("partner_id"));
  let shift_id = parseInt(member.getAttribute("shift_id"));

  let name = member.getAttribute("name");
  let associate_name = member.getAttribute("associate_name");
  let display_name = name;
  if (associate_name != "None") {
    display_name = name + " et/ou " + associate_name;
  }

  let body = "Bonjour <strong>" + display_name + "</strong><br>Veuillez confirmer votre présence";
  let payload = registration_id + ", " + partner_id + ", " + shift_id;
  openCModal("Confirmation de présence", body, "confirmedPresence(" + payload + ")");
}

async function confirmedPresence(registration_id, partner_id, shift_id) {
  websocket.send(
    JSON.stringify({
      message: "attend",
      data: { registration_id: registration_id, partner_id: partner_id, shift_id: shift_id },
    }),
  );
  document.getElementById("cancel-confirmation").desabled = true;
  document.getElementById("accept-confirmation").desabled = true;
}

// NOTING RESET ATTENDANCIES
function askConfirmationReset(registration_id) {
  let member = document.getElementById(registration_id);
  let partner_id = parseInt(member.getAttribute("partner_id"));
  let shift_id = parseInt(member.getAttribute("shift_id"));

  let name = member.getAttribute("name");
  let associate_name = member.getAttribute("associate_name");
  let display_name = name;
  if (associate_name != "None") {
    display_name = name + " et/ou " + associate_name;
  }

  let body = "Bonjour, Voullez vous annuler la présence de <strong>" + display_name + "</strong>";
  let payload = registration_id + ", " + partner_id + ", " + shift_id;
  openCModal("Annuler sa présence", body, "confirmedReset(" + payload + ")");
}

async function confirmedReset(registration_id, partner_id, shift_id) {
  websocket.send(
    JSON.stringify({
      message: "reset",
      data: { registration_id: registration_id, partner_id: partner_id, shift_id: shift_id },
    }),
  );
  document.getElementById("cancel-confirmation").disabled = true;
  document.getElementById("accept-confirmation").disabled = true;
}

function openCModal(headerMsg, bodyMsg, closeFunc) {
  window.scrollTo(0, window.scrollY);
  document.getElementById("confirmation-modal").style.top = (window.scrollY - 5).toString() + "px";
  document.getElementById("confirmation-modal").style.display = "flex";
  document.getElementById("html").style.overflowY = "hidden";
  document.getElementById("heading-message").innerHTML = headerMsg;
  document.getElementById("content-message").innerHTML = bodyMsg;
  document.getElementById("accept-confirmation").setAttribute("onclick", closeFunc);
}

function CloseCModal() {
  document.getElementById("confirmation-modal").style.display = "none";
  document.getElementById("html").style.overflowY = "visible";
  document.getElementById("cancel-confirmation").disabled = false;
  document.getElementById("accept-confirmation").disabled = false;
}

function referenced_shifts_ids() {
  let shifts = document.getElementsByClassName("shift");
  let shift_ids = [];
  for (var shift of shifts) {
    shift_ids.push(parseInt(shift.getAttribute("shift_id")));
  }
  return shift_ids;
}

// REGISTRATION
function askRegistration(shift_id) {
  document.getElementById("member-list").setAttribute("shift_id", shift_id);
  openRegistrationModal();
}

function openRegistrationModal() {
  window.scrollTo(0, window.scrollY);
  document.getElementById("registration-modal").style.top = (window.scrollY - 5).toString() + "px";
  document.getElementById("registration-modal").style.display = "flex";
  document.getElementById("html").style.overflowY = "hidden";
}

function closeRegistrationModal() {
  document.getElementById("registration-modal").style.display = "none";
  document.getElementById("html").style.overflowY = "visible";
  document.getElementById("member-list").innerHTML = "";
  document.getElementById("member-list").removeAttribute("shift_id");
  document.getElementById("search-member-input").value = "";
}

async function searchMember() {
  let loading = document.getElementById("loader");
  let container = document.getElementById("member-list");
  container.innerHTML = "";
  container.style.display = "none";
  loading.style.display = "block";

  let value = document.getElementById("search-member-input").value;
  payload = {
    method: "POST",
    mode: "cors",
    cache: "no-cache",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    redirect: "follow",
    referrerPolicy: "no-referrer",
    body: JSON.stringify({ input: value }),
  };
  const response = await fetch("./registration/search_member", payload);
  const data = await response.json();

  if (response.status != 200) {
    new MsgFactory("msg-box", "err", "<strong>" + data.reasons + "</strong>", true, 3000, 1000);
  } else {
    if (data.data.length > 0) {
      let ul = searchMemberListFactory(data.data);
      container.appendChild(ul);
    } else {
      let container = document.getElementById("member-list");
      let elm = "<ul><li>Aucun résultat</li></ul>";
      container.innerHTML += elm;
    }
  }

  loading.style.display = "none";
  container.style.display = "block";
}

function searchMemberListFactory(payload) {
  let ul = document.createElement("ul");
  ul.classList.add("border");
  for (var member of payload) {
    let elm = searchMemberFactory(member);
    ul.appendChild(elm);
  }
  return ul;
}

function searchMemberFactory(data) {
  let display_name = "<strong>" + data.barcode_base + "</strong> - " + data.name;

  let box = document.createElement("input");
  box.setAttribute("type", "checkbox");
  box.setAttribute("onclick", "OnlyOneCheckRemain(this)");
  box.setAttribute("hidden", true);

  let label = document.createElement("label");
  label.classList.add("li-member", "border-light"); //
  label.setAttribute("partner_id", data.partner_id);
  label.setAttribute("barcode", data.barcode_base);
  label.innerHTML = display_name;

  label.appendChild(box);
  return label;
}

function registrateMember() {
  let container = document.getElementById("member-list");
  for (li of container.getElementsByClassName("li-member")) {
    if (li.lastChild.checked) {
      let context = {
        shift_id: parseInt(container.getAttribute("shift_id")),
        partner_id: parseInt(li.getAttribute("partner_id")),
      };
      console.log(context);
      websocket.send(JSON.stringify({ message: "registrate", data: context }));
    }
  }
}

function OnlyOneCheckRemain(elm) {
  let ul = elm.parentNode.parentNode;
  let id = elm.parentNode.getAttribute("partner_id");
  for (li of ul.getElementsByClassName("li-member")) {
    let other_id = li.getAttribute("partner_id");
    if (id != other_id) {
      li.lastChild.checked = false;
      li.classList.remove("selected");
    } else {
      li.classList.add("selected");
    }
  }
}

// NOTIFICATIONS

class MsgFactory {
  constructor(containerId, mtype, msg, fade = false, sleep = 0, speed = 0) {
    const container = document.getElementById(containerId);

    let frame = this.buildFrame(mtype);
    frame.appendChild(this.buildSymbol(mtype));
    frame.appendChild(this.buildMsg(msg));
    frame.appendChild(this.buildExit());

    let node = container.appendChild(frame);
    if (fade) {
      this.fadeOut(node, sleep, speed);
    }
  }

  buildFrame(mtype) {
    let frame = document.createElement("div");
    frame.classList.add(mtype, "msg-container");
    frame.style.opacity = 100;
    return frame;
  }

  buildSymbol(mtype) {
    let elm = document.createElement("img");
    elm.classList.add("msg-symbol", "msg-comp");
    elm.setAttribute("src", "/static/misc/" + mtype + ".png");
    return elm;
  }

  buildMsg(msg) {
    let elm = document.createElement("p");
    elm.classList.add("msg", "msg-comp");
    elm.innerHTML = msg;
    return elm;
  }

  buildExit() {
    let elm = document.createElement("div");
    elm.classList.add("quit-container");

    let btn = document.createElement("button");
    btn.classList.add("msg-quit", "msg-comp");
    btn.setAttribute("onclick", "closeMsg(this)");
    btn.innerText = "x";

    elm.appendChild(btn);
    return elm;
  }

  async fadeOut(node, slp, speed) {
    await sleep(slp);
    node.style.transition = speed + "ms";
    node.style.opacity = 0;
    await sleep(speed);
    node.remove();
  }
}

function closeMsg(elm) {
  let box = elm.parentElement.parentElement;
  box.remove();
}

function sleep(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}
