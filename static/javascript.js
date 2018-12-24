function toggle_element_by_id(id) {
    var x = document.getElementById(id);
    if (x.style.display === "none" || x.style.display === "" || x.style.display === null) {
      x.style.display = "block";
    } else {
      x.style.display = "none";
    }
  }