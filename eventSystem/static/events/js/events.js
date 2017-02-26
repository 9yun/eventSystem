var question_count = 0;

function handleNewFrQ() {
    question_count++;
    // Outer div
    var outer_div = document.createElement("div");
    outer_div.className += "input_container";
    outer_div.style.marginTop = "10px";
    outer_div.style.marginBottom = "10px";
    outer_div.id = "question_div_" + question_count.toString();

    // Question number
    var qnumber = document.createElement("label");
    qnumber.innerHTML = "Question " + (question_count).toString() + ". ";
    qnumber.id = "qlabel_" + question_count.toString();
    qnumber.className += "fancy_text";
    outer_div.appendChild(qnumber);

    // Break
    var br = document.createElement("br");
    outer_div.appendChild(br);

    // Question text
    var question_text = document.createElement("label");
    question_text.innerHTML = "[Your Question Here]";
    question_text.contentEditable = true;
    question_text.className += "fancy_text";
    question_text.style.maxWidth = "800px";
    question_text.style.maxHeight = "100px";
    question_text.style.overflowX = "hidden";
    question_text.style.overflowY = "auto";
    outer_div.appendChild(question_text);

    // Break
    br = document.createElement("br");
    outer_div.appendChild(br);

    // Input box
    var input = document.createElement("input");
    input.type = "text";
    input.disabled = true;
    input.placeholder = "This is where your guests will type";
    input.style.font = "300 25px/1.3 'Lobster Two', Helvetica, sans-serif";
    outer_div.appendChild(input);

    // Break
    br = document.createElement("br");
    outer_div.appendChild(br);

    // Delete button
    var delete_button = document.createElement("input");
    delete_button.type = "button";
    delete_button.value = "Delete";
    delete_button.id = "delete_" + question_count.toString();
    delete_button.onclick = function() {
        delete_question(delete_button.id);
    }
    // Styling
    delete_button.style.backgroundColor = "lightcoral";
    delete_button.style.padding = "5px 5px";
    delete_button.style.cursor = "pointer";
    delete_button.style.borderTopLeftRadius = "15px";
    delete_button.style.borderTopRightRadius = "15px";
    delete_button.style.borderBottomLeftRadius = "15px";
    delete_button.style.borderBottomRightRadius = "15px";
    delete_button.style.font = "300 25px/1.3 'Lobster Two', Helvetica, sans-serif";
    outer_div.appendChild(delete_button);

    document.getElementById("dynamic_questions").appendChild(outer_div);
}

function handleNewMcQ() {

}

function delete_question(id) {
    // Strip the question number
    var regex = /(\d+)/g;
    var matches = id.match(regex);
    var number = matches[0];
    var to_delete = document.getElementById("question_div_" + number.toString());
    to_delete.parentNode.removeChild(to_delete);
    renumber_questions();
}

function renumber_questions() {
    var question_number = 1;
    var label;
    for (i = 1; i <= question_count; i++) {
        label = document.getElementById("qlabel_" + i.toString());
        if (label != null) {
            label.id = "qlabel_" + question_number.toString();
            label.innerHTML = "Question " + question_number.toString() + ". ";
            question_number++;
        }
    }
    question_count = question_number - 1;
}