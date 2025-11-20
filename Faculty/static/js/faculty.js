// Faculty/static/js/faculty.js
document.addEventListener("DOMContentLoaded", function() {
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
});
