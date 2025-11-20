// Faculty/static/js/attendance.js
document.addEventListener("DOMContentLoaded", function() {
  const addBtn = document.getElementById("addStudent");
  const studentsArea = document.getElementById("studentsArea");
  const subjectInput = document.querySelector('input[name="subject_name"]');
  const semesterInput = document.querySelector('input[name="semester"]');
  const batchInput = document.querySelector('input[name="batch"]');
  const departmentInput = document.querySelector('input[name="department"]');
  const fetchBtn = document.getElementById("fetchEnrolled");

  function addStudentRow(student) {
    const row = document.createElement("div");
    row.className = "student-row";
    row.innerHTML = `
      <input name="student_reg_no[]" value="${student ? student.registration_number : ''}" placeholder="Registration number" required>
      <input name="student_name[]" value="${student ? (student.name||'') : ''}" placeholder="Student name" readonly>
      <select name="status[]">
        <option>Present</option>
        <option>Absent</option>
        <option>Late</option>
      </select>
      <button type="button" class="remove">-</button>
    `;
    studentsArea.appendChild(row);
    row.querySelector(".remove").addEventListener("click", () => row.remove());
  }

  // attach remove to existing rows
  document.querySelectorAll(".student-row .remove").forEach(btn => {
    btn.addEventListener("click", (e) => e.target.closest(".student-row").remove());
  });

  if (addBtn) {
    addBtn.addEventListener("click", function() {
      addStudentRow(null);
    });
  }

  if (fetchBtn) {
    fetchBtn.addEventListener("click", async function() {
      const subject = subjectInput ? subjectInput.value.trim() : "";
      const semester = semesterInput ? semesterInput.value.trim() : "";
      const batch = batchInput ? batchInput.value.trim() : "";
      const department = departmentInput ? departmentInput.value.trim() : "";
      if (!subject) {
        alert("Enter subject name to fetch enrolled students.");
        return;
      }
      const params = new URLSearchParams({ subject_name: subject });
      if (semester) params.append("semester", semester);
      if (batch) params.append("batch", batch);
      if (department) params.append("department", department);

      try {
        const resp = await fetch(`/faculty/api/enrolled-students?${params.toString()}`, { credentials: "same-origin" });
        if (!resp.ok) {
          const text = await resp.text();
          alert("Error fetching students: " + text);
          return;
        }
        const data = await resp.json();
        if (!data.ok) {
          alert(data.error || "Could not fetch students");
          return;
        }
        // clear current area and add rows
        studentsArea.innerHTML = "";
        data.students.forEach(st => addStudentRow(st));
        if (data.students.length === 0) {
          alert("No enrolled students found for this subject/semester/batch.");
        }
      } catch (err) {
        console.error(err);
        alert("Error fetching students. See console.");
      }
    });
  }
});
