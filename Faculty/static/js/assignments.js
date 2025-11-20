// Faculty/static/js/assignments.js
document.addEventListener("DOMContentLoaded", function() {
  const allSubmittedBtn = document.getElementById("selectAllSubmitted");
  const allNotSubmittedBtn = document.getElementById("selectAllNotSubmitted");

  function setAllStatuses(value) {
    document.querySelectorAll('select[name="status[]"]').forEach(sel => {
      sel.value = value;
    });
  }

  if (allSubmittedBtn) {
    allSubmittedBtn.addEventListener("click", function() { setAllStatuses("Submitted"); });
  }
  if (allNotSubmittedBtn) {
    allNotSubmittedBtn.addEventListener("click", function() { setAllStatuses("Not Submitted"); });
  }
});
