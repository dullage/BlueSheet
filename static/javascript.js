function toggle_element_by_id(id) {
    var x = document.getElementById(id);
    if (x.style.display === "none" || x.style.display === "" || x.style.display === null) {
      x.style.display = "block";
    } else {
      x.style.display = "none";
    }
  }

function load_starling_data() {
  var request = new XMLHttpRequest();

  request.onreadystatechange = function() { 
      if (request.readyState == 4 && request.status == 200) {
          var response = JSON.parse(request.response);
          var starling_table = document.getElementById("starling-table");
          document.getElementById("starling-loading").remove();

          for (key in response) {
            if (key == "Main Balance") {
              // First Row
              var row = starling_table.insertRow(0);
              row.className = "bold";
            }
            else {
              var row = starling_table.insertRow();
            }
            
            var cell1 = row.insertCell(0);
            var cell2 = row.insertCell(1);
            cell1.innerHTML = key;
            cell1.className = "stretch";
            cell2.innerHTML = response[key]
          }
      }
  }

  request.open("GET", "./get-starling-data", true); // true for asynchronous 
  request.send(null);
}

function outgoing_saving_checkbox_handle() {
  var saving_checkbox = document.getElementById("saving_checkbox");
  var saving_checkbox_content = document.getElementById("saving_checkbox_content");

  var saving_id = document.getElementById("saving_id");
  var self_loan_checkbox = document.getElementById("self_loan_checkbox");

  if (saving_checkbox.checked == true) {
    saving_checkbox_content.style.display = "block";
    saving_id.required = true;
  }
  else {
    saving_checkbox_content.style.display = "none";
    saving_id.required = false;

    // Clear Values
    saving_id.value = "";
    self_loan_checkbox.checked = false;
  }
}

function self_loan_checkbox_handle() {
  var self_loan_checkbox = document.getElementById("self_loan_checkbox");
  var start_month = document.getElementById("start_month");
  var end_month = document.getElementById("end_month");

  if (self_loan_checkbox.checked == true) {
    start_month.required = true;
    end_month.required = true;
  }
  else {
    start_month.required = false;
    end_month.required = false;
  }
}
