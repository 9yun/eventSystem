/* Question Class File */

var __working_question_id = "working_question_id";
var __cancel_button_id = "cancel_button_id";
var __question_div_id = "div_question_";
var __approved_questions = [];

num_total_questions = 1;

function Question(qnText, qnType, Choices, qnNumber) {
    this.qnText = qnText;
    this.qnType = qnType;
    this.Choices = Choices;
    this.qnNumber = qnNumber;
}

function GenOpenQuestionHtml() {
    DisableNewQuestions();

    var parent = document.getElementById("working_dynamic_question");

    // Add input box for question text
    var input = document.createElement("input");
    input.type = "text";
    input.id = __working_question_id;
    input.placeholder = "Type your free response question";
    input.style.font = "300 25px/1.3 'Lobster Two', Helvetica, sans-serif";

    // Add the label
    var qnumber = GetQNumberLabel();

    // Add the submit button
    var submit = GetSubmitButton();

    // Add the cancel button
    var cancel = GetCancelButton();
    cancel.onclick = function () {
        EnableNewQuestions();
        while (parent.firstChild) {
            parent.removeChild(parent.firstChild);
        }
    }
    
    // Add to parent
    parent.appendChild(qnumber);
    parent.appendChild(input);
    parent.appendChild(submit);
    parent.appendChild(cancel);
}

function GenChoiceQuestionHtml() {
    alert("Not ready :)");
    //DisableNewQuestions();
}

function GetQuestionDiv(num) {
    var div = document.createElement("div");
    div.id = __question_div_id + num.toString();
    return div;
}

function GetQNumberLabel(opt) {
    var qnumber = document.createElement("label");
    qnumber.style.textAlign = "center";
    if (opt == null) {
        qnumber.innerHTML = "Question " + num_total_questions.toString();
    } else {
        qnumber.innerHTML = "Question " + opt.qnNumber.toString();
    }
    qnumber.style.font = "300 35px/1.3 'Lobster Two', Helvetica, sans-serif";
    return qnumber;
}

function GetSubmitButton() {
    var submit = document.createElement("input");
    submit.type = "button";
    submit.value = "Submit Question"
    submit.style.font = "300 25px/1.3 'Lobster Two', Helvetica, sans-serif";
    submit.style.backgroundColor = "skyblue";
    submit.style.borderBottomLeftRadius = "10px";
    submit.style.borderBottomRightRadius = "10px";
    submit.style.borderTopLeftRadius = "10px";
    submit.style.borderTopRightRadius = "10px";
    submit.onclick = function () {
        VerifyOpenQuestion();
    }
    return submit;
}

function QuestionTextToHtmlLabel(question_text) {
    var question = document.createElement("label");
    question.style.textAlign = "center";
    question.innerHTML = question_text;
    question.style.font = "300 27px/1.3 'Lobster Two', Helvetica, sans-serif";
    return question;
}

function GetCancelButton() {
    var cancel = document.createElement("input");
    cancel.type = "button";
    cancel.value = "Cancel"
    cancel.id = __cancel_button_id;
    cancel.style.font = "300 25px/1.3 'Lobster Two', Helvetica, sans-serif";
    cancel.style.backgroundColor = "lightcoral";
    cancel.style.borderBottomLeftRadius = "10px";
    cancel.style.borderBottomRightRadius = "10px";
    cancel.style.borderTopLeftRadius = "10px";
    cancel.style.borderTopRightRadius = "10px";
    return cancel;
}

function GetDeleteButton() {
    var db = document.createElement("input");
    db.type = "button";
    db.value = "Delete"
    db.style.font = "300 25px/1.3 'Lobster Two', Helvetica, sans-serif";
    db.style.backgroundColor = "lightcoral";
    db.style.borderBottomLeftRadius = "10px";
    db.style.borderBottomRightRadius = "10px";
    db.style.borderTopLeftRadius = "10px";
    db.style.borderTopRightRadius = "10px";
    return db;
}

function GetBreak() {
    return document.createElement("br");
}

function VerifyOpenQuestion() {
    var question = new Question(document.getElementById(__working_question_id).value,
        'Open',
        null,
        num_total_questions);
    if (question.qnText == '') {
        return;
    }
    // Check if internal duplicate
    if (isDuplicate(question.qnText)) {
        return;
    }
    // TODO: Add AJAX here? Yeah probs
    __approved_questions.push(question);
    // Add question to approved questions
    GenOpenQuestionFromHtml(question);
    document.getElementById(__cancel_button_id).click();
    num_total_questions++;
}

function DisableNewQuestions() {
    var newOpen = document.getElementById("newOpenQbutton");
    var newChoice = document.getElementById("newChoiceQbutton");
    newOpen.style.backgroundColor = "#cdd2d8";
    newChoice.style.backgroundColor = "#cdd2d8";
    newOpen.disabled = true;
    newChoice.disabled = true;
}

function EnableNewQuestions() {
    var newOpen = document.getElementById("newOpenQbutton");
    var newChoice = document.getElementById("newChoiceQbutton");
    newOpen.style.backgroundColor = "#e5b66b";
    newChoice.style.backgroundColor = "#e5b66b";
    newOpen.disabled = false;
    newChoice.disabled = false;
}

function isDuplicate(qnText) {
   for (i = 0; i < __approved_questions.length; i++) {
       if (qnText == __approved_questions[i].qnText) {
           alert("Duplicate question - please submit another");
           document.getElementById(__working_question_id).value = '';
           document.getElementById(__working_question_id).placeholder = "Submit a different question";
           return true;
       }
   }
   return false; 
}

function RenumberQuestions() {
    var question_number = 1;
    for (i = 0; i < __approved_questions.length; i++) {
        if (__approved_questions[i].qnNumber != i + 1) {
            __approved_questions[i].qnNumber = i + 1;
        }
        question_number++;
    }
}

function DeleteQuestion(question) {
    // Remove from list
    var index = __approved_questions.indexOf(question);
    if (index > -1) {
        __approved_questions.splice(index, 1);
    }
    // Remove html
    var look = __question_div_id + question.qnNumber.toString();
    var to_delete = document.getElementById(__question_div_id + question.qnNumber.toString());
    to_delete.parentNode.removeChild(to_delete);
}

function GenOpenQuestionFromHtml(question) {
    var parent = document.getElementById("okay_dynamic_questions");
    // Get outer div
    var div = GetQuestionDiv(question.qnNumber);
    // Get label
    var label = GetQNumberLabel(question);
    // Get Question text
    var question_text = QuestionTextToHtmlLabel(question.qnText);
    // Get Delete button
    var db = GetDeleteButton();
    db.onclick = function() {
        DeleteQuestion(question);
        num_total_questions--;
        var tmp = JSON.parse(JSON.stringify(__approved_questions));
        for (i = 0; i < tmp.length; i++) {
            DeleteQuestion(tmp[i]);
        }
        RenumberQuestions();
        for (i = 0; i < __approved_questions.length; i++) {
            GenOpenQuestionFromHtml(__approved_questions[i]);
        }
    }
    
    div.appendChild(label);
    div.appendChild(GetBreak());
    div.appendChild(question_text);
    div.appendChild(GetBreak());
    div.appendChild(db);
    div.appendChild(GetBreak());
    parent.appendChild(div);
}

function GenChoiceQuestionFromHtml() {

}