function allValidate() {
    if (!validateTime()) {
        return false;
    }
    if (!validateEventName()) {
        return false;
    }
    return true;
}

function validateEventName() {
    var x = document.getElementsByName("eventname");
    x = x[0];
    re = /[^a-zA-Z0-9_ ]/g;
    if(x.value.match(re)) {
      alert("Event name may only contain letters, numbers, underscores and spaces.");
      x.focus();
      x.style="color:red";
      return false;
    }
    return true;
}

function validateTime() {
  var x = document.getElementsByName("start_time");
  x = x[0];
  re = /^(\d{1,2}):(\d{2})\s*([ap]m)/i;
  if (x.value != '' && !x.value.match(re)) {
    alert("Invalid time format: " + x.value);
    x.focus();
    x.value = "HH:MM AM/PM";
    x.style = "color:red";
    return false;
  }
  // Modify it for the server
  var matches = re.exec(x.value);
  x.value = matches[1] + ":" + matches[2] + " " + matches[3];
  x = document.getElementsByName("end_time");
  x = x[0];
  re = /^(\d{1,2}):(\d{2})\s*([ap]m)/i;
  if (x.value != '' && !x.value.match(re)) {
    alert("Invalid time format: " + x.value);
    x.focus();
    x.value = "HH:MM AM/PM";
    x.style = "color:red";
    return false;
  }
  matches = re.exec(x.value);
  x.value = matches[1] + ":" + matches[2] + " " + matches[3];
  return true;
}