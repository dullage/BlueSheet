function toggle_element_by_id(id) {
    var x = document.getElementById(id);
    if (x.style.display === "none" || x.style.display === "" || x.style.display === null) {
      x.style.display = "block";
    } else {
      x.style.display = "none";
    }
  }

function delete_warning(type, id, name) {
  if (type == "account") {
    if (window.confirm(`Are you sure you want to delete the account '${name}'?\n\nNote: Any outgoings for this account will also be deleted.`) == true) {
      window.location.href = `/delete-account-handler/${id}`;
    }
  }

  if (type == "outgoing") {
    if (window.confirm(`Are you sure you want to delete the outgoing '${name}'?`) == true) {
      window.location.href = `/delete-outgoing-handler/${id}`;
    }
  }

  if (type == "annual-expense") {
    if (window.confirm(`Are you sure you want to delete the annual expense '${name}'?`) == true) {
      window.location.href = `/delete-annual-expense-handler/${id}`;
    }
  }
}
