function validateTime() {
    var x = document.forms["input_form"]["starttime"];
    re = /^\d{1,2}:\d{2}\s*([ap]m)?$/i;
    if(x.value != '' && !x.value.match(re)) {
      alert("Invalid time format: " + x.value);
      x.focus();
      document.forms["input_form"]["starttime"].value = "HH:MM AM/PM";
      document.forms["input_form"]["starttime"].style="color:red";
      return false;
    }
    x = document.forms["input_form"]["endtime"];
    re = /^\d{1,2}:\d{2}\s*([ap]m)?$/i;
    if(x.value != '' && !x.value.match(re)) {
      alert("Invalid time format: " + x.value);
      x.focus();
      document.forms["input_form"]["endtime"].value = "HH:MM AM/PM";
      document.forms["input_form"]["endtime"].style="color:red";
      return false;
    }
    return true;
}