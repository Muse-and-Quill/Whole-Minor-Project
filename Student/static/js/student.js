// student/static/js/student.js
document.addEventListener("DOMContentLoaded", function() {
  // Tabs for login
  const pwTab = document.getElementById("pwTab");
  const otpTab = document.getElementById("otpTab");
  const pwForm = document.getElementById("passwordForm");
  const otpForm = document.getElementById("otpForm");
  if (pwTab && otpTab) {
    pwTab.addEventListener("click", () => {
      pwTab.classList.add("active"); otpTab.classList.remove("active");
      pwForm.style.display = ""; otpForm.style.display = "none";
    });
    otpTab.addEventListener("click", () => {
      otpTab.classList.add("active"); pwTab.classList.remove("active");
      otpForm.style.display = ""; pwForm.style.display = "none";
    });
  }

  // Dynamic subject rows in registration form
  const addBtn = document.getElementById("addSubject");
  if (addBtn) {
    addBtn.addEventListener("click", function() {
      const container = document.getElementById("subjects");
      const row = document.createElement("div");
      row.className = "subject-row";
      row.innerHTML = `
        <input name="subject_name[]" placeholder="Subject name" required>
        <input name="subject_code[]" placeholder="Code (optional)">
        <input name="subject_dept[]" placeholder="Department (optional)">
        <button type="button" class="remove">-</button>
      `;
      container.appendChild(row);
      row.querySelector(".remove").addEventListener("click", () => row.remove());
    });

    // attach remove to existing rows
    document.querySelectorAll(".subject-row .remove").forEach(btn => {
      btn.addEventListener("click", (e) => e.target.closest(".subject-row").remove());
    });
  }
});
