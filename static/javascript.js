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
            cell2.innerHTML = response[key]
          }
      }
  }

  request.open("GET", "./get-starling-data", true); // true for asynchronous 
  request.send(null);
}
