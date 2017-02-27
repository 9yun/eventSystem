/* Question Class File */

var __working_question_id = "working_question_id";
var __cancel_button_id = "cancel_button_id";
var __approved_questions = [''];

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

    // Add the instructions/label
    var qnumber = document.createElement("label");
    qnumber.style.textAlign = "center";
    qnumber.innerHTML = "Question " + num_total_questions.toString();
    qnumber.style.font = "300 35px/1.3 'Lobster Two', Helvetica, sans-serif";

    // Add the submit button
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

    // Add the cancel button
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
    DisableNewQuestions();
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
    // TODO: Add AJAX here
    __approved_questions += question;
    // Add question to approved questions
    GenOpenQuestionFromHtml(question);
    document.getElementById(__cancel_button_id).click();
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
   for (q in __approved_questions) {
       if (qnText == q.qnText) {
           alert(qnText + ' ' + q.qnText);
           //alert("Duplicate question - please submit another");
           document.getElementById(__working_question_id).value = '';
           document.getElementById(__working_question_id).placeholder = "Submit a different question";
           return true;
       }
   }
   return false; 
}

function GenOpenQuestionFromHtml(question) {

}

function GenChoiceQuestionFromHtml() {

}

/**
 * Yes, this is called Html-ify :D
 */
function HtmlifyQuestion(parent_div) {

}