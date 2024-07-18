
color_counter();

function color_counter() {
    let ftopc = document.getElementsByClassName("ftopc");
    let stdc = document.getElementsByClassName("stdc");

    for (var elm of ftopc) {
        let val = parseInt(elm.innerHTML);
        if (val >= 0) {
            elm.style.backgroundColor = "#6FD8BA";
        } else if (val < 0 && val >= -2) {
            elm.style.backgroundColor = "#E0C867";
        } else {
            elm.style.backgroundColor = "#F06449";
        }
    }

    for (var elm of stdc) {
        let val = parseInt(elm.innerHTML);
        if (val == 0) {
            elm.style.backgroundColor = "#6FD8BA";
        } else if (val < 0 && val >= -2) {
            elm.style.backgroundColor = "#E0C867";
        } else {
            elm.style.backgroundColor = "#F06449";
        }
    }

}