# Faculty/routes/faculty_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from services.mongo_client import get_mongo_db
from services.email_service import send_email
from utils.auth_helpers import login_required_faculty, set_nocache
from utils.validators import is_valid_registration
from datetime import datetime, timedelta
import random
import bson

faculty_bp = Blueprint("faculty_bp", __name__, template_folder="../../templates/faculty", static_folder="../../static")

OTP_COLLECTION = "login_otps"

def _save_otp(db, reg_no, otp, purpose="login"):
    expires_at = datetime.utcnow() + timedelta(minutes=int(__import__("config").Config.OTP_EXPIRE_MINUTES))
    db[OTP_COLLECTION].insert_one({
        "registration_number": reg_no,
        "otp": otp,
        "purpose": purpose,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    })

def _verify_and_consume_otp(db, reg_no, otp, purpose="login"):
    doc = db[OTP_COLLECTION].find_one({"registration_number": reg_no, "otp": otp, "purpose": purpose})
    if not doc:
        return False, "Invalid OTP."
    if doc.get("expires_at") < datetime.utcnow():
        return False, "OTP expired."
    db[OTP_COLLECTION].delete_one({"_id": doc["_id"]})
    return True, None

@faculty_bp.route("/")
def index():
    return render_template("index.html")

@faculty_bp.route("/login", methods=["GET", "POST"])
def login():
    db = get_mongo_db()
    if request.method == "GET":
        return render_template("login.html")
    mode = request.form.get("mode", "password")
    reg_no = request.form.get("registration_number", "").strip().upper()
    if not is_valid_registration(reg_no):
        flash("Enter a valid registration number.", "danger")
        return render_template("login.html")
    teacher = db["teachers"].find_one({"registration_number": reg_no})
    if not teacher or not teacher.get("is_active", True):
        flash("Teacher not found or inactive.", "danger")
        return render_template("login.html")

    if mode == "password":
        password = request.form.get("password", "")
        if not password or not teacher.get("password_hash") or not check_password_hash(teacher["password_hash"], password):
            flash("Invalid credentials.", "danger")
            return render_template("login.html")
        session["role"] = "faculty"
        session["reg_no"] = teacher["registration_number"]
        session["faculty_id"] = str(teacher["_id"])
        flash("Logged in.", "success")
        return redirect(url_for("faculty_bp.dashboard"))

    if mode == "otp":
        otp = f"{random.randint(100000,999999)}"
        _save_otp(db, reg_no, otp, purpose="login")
        subj = "UAP Faculty Login OTP"
        body = f"Dear {teacher.get('name','Faculty')},\n\nYour login OTP is {otp}. It expires in {__import__('config').Config.OTP_EXPIRE_MINUTES} minutes.\n\nUAP"
        send_email(subj, body, teacher.get("email"))
        return render_template("login.html", otp_sent=True, reg_no=reg_no)

    flash("Invalid login mode.", "danger")
    return render_template("login.html")

@faculty_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    db = get_mongo_db()
    reg_no = request.form.get("registration_number", "").strip().upper()
    otp = request.form.get("otp", "").strip()
    if not reg_no or not otp:
        flash("Invalid request.", "danger")
        return redirect(url_for("faculty_bp.login"))
    ok, msg = _verify_and_consume_otp(db, reg_no, otp, purpose="login")
    if not ok:
        flash(msg or "OTP failed.", "danger")
        return redirect(url_for("faculty_bp.login"))
    teacher = db["teachers"].find_one({"registration_number": reg_no})
    if not teacher:
        flash("Teacher record not found.", "danger")
        return redirect(url_for("faculty_bp.login"))
    session["role"] = "faculty"
    session["reg_no"] = teacher["registration_number"]
    session["faculty_id"] = str(teacher["_id"])
    flash("Logged in via OTP.", "success")
    return redirect(url_for("faculty_bp.dashboard"))

@faculty_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    db = get_mongo_db()
    if request.method == "GET":
        return render_template("forgot_password.html", step="request")
    step = request.form.get("step", "request")
    if step == "request":
        reg_no = request.form.get("registration_number", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        if not reg_no or not email:
            flash("Provide registration number and email.", "danger")
            return render_template("forgot_password.html", step="request")
        teacher = db["teachers"].find_one({"registration_number": reg_no, "email": email})
        if not teacher:
            flash("No matching teacher found.", "danger")
            return render_template("forgot_password.html", step="request")
        otp = f"{random.randint(100000,999999)}"
        _save_otp(db, reg_no, otp, purpose="reset")
        subj = "UAP Faculty Password Reset OTP"
        body = f"Your reset OTP is {otp}. It expires in {__import__('config').Config.OTP_EXPIRE_MINUTES} minutes."
        send_email(subj, body, email)
        flash("OTP sent.", "info")
        return render_template("forgot_password.html", step="verify", reg_no=reg_no)
    else:
        reg_no = request.form.get("registration_number", "").strip().upper()
        otp = request.form.get("otp", "").strip()
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")
        if not (reg_no and otp and new_pw and confirm_pw):
            flash("All fields required.", "danger")
            return render_template("forgot_password.html", step="verify", reg_no=reg_no)
        if new_pw != confirm_pw:
            flash("Passwords do not match.", "danger")
            return render_template("forgot_password.html", step="verify", reg_no=reg_no)
        ok, msg = _verify_and_consume_otp(db, reg_no, otp, purpose="reset")
        if not ok:
            flash(msg or "OTP invalid/expired.", "danger")
            return render_template("forgot_password.html", step="verify", reg_no=reg_no)
        pw_hash = generate_password_hash(new_pw)
        res = db["teachers"].update_one({"registration_number": reg_no}, {"$set": {"password_hash": pw_hash}})
        if res.matched_count:
            flash("Password updated. You may log in now.", "success")
            return redirect(url_for("faculty_bp.login"))
        flash("Unable to update password.", "danger")
        return render_template("forgot_password.html", step="verify", reg_no=reg_no)

@faculty_bp.route("/dashboard")
@login_required_faculty
def dashboard():
    db = get_mongo_db()
    reg_no = session.get("reg_no")
    teacher = db["teachers"].find_one({"registration_number": reg_no})
    # stats
    total_regs = db["semester_registrations"].count_documents({"department": teacher.get("department")})
    total_batches = db["batches"].count_documents({"faculty_reg_no": reg_no})
    upcoming_assignments = list(db["assignments"].find({"faculty_reg_no": reg_no}).sort("due_date", 1).limit(5))
    return render_template("dashboard.html", teacher=teacher, total_regs=total_regs, total_batches=total_batches, upcoming_assignments=upcoming_assignments)

@faculty_bp.route("/registrations")
@login_required_faculty
def registrations():
    db = get_mongo_db()
    semester = request.args.get("semester")
    department = request.args.get("department")
    query = {}
    if semester:
        query["semester"] = semester
    if department:
        query["department"] = department
    regs = list(db["semester_registrations"].find(query).sort("timestamp", -1).limit(200))
    return render_template("registrations.html", regs=regs)

@faculty_bp.route("/batches", methods=["GET", "POST"])
@login_required_faculty
def batches():
    db = get_mongo_db()
    if request.method == "GET":
        subject = request.args.get("subject")
        batches = list(db["batches"].find({"subject_name": subject}) if subject else db["batches"].find().limit(200))
        return render_template("batches.html", batches=batches)
    # POST: create enrollment mappings
    data = request.form
    subject_name = data.get("subject_name")
    subject_code = data.get("subject_code")
    semester = data.get("semester")
    batch = data.get("batch")
    # student_reg_no[] form array OR textarea input (handle both)
    students = request.form.getlist("student_reg_no[]")
    # If textarea (single string) present, split lines
    if not students or (len(students) == 1 and "\n" in students[0]):
        raw = data.get("student_reg_no[]", "") or data.get("student_reg_no", "")
        if raw:
            students = [s.strip() for s in raw.splitlines() if s.strip()]
    docs = []
    for reg in students:
        docs.append({
            "student_reg_no": reg,
            "subject_name": subject_name,
            "subject_code": subject_code,
            "semester": semester,
            "batch": batch,
            "faculty_reg_no": session.get("reg_no"),
            "department": data.get("department"),
            "assigned_at": datetime.utcnow()
        })
    if docs:
        db["batches"].insert_many(docs)
        flash("Batches/enrollments created.", "success")
    else:
        flash("No students selected.", "warning")
    return redirect(url_for("faculty_bp.batches"))

@faculty_bp.route("/attendance/mark", methods=["GET", "POST"])
@login_required_faculty
def mark_attendance():
    db = get_mongo_db()
    if request.method == "GET":
        # show form to pick subject/semester/batch
        return render_template("attendance_mark.html")
    # POST: payload includes date, time_period, subject_name, and students statuses
    subject_name = request.form.get("subject_name")
    subject_code = request.form.get("subject_code")
    date = request.form.get("date")  # expected YYYY-MM-DD
    time_period = request.form.get("time_period")
    # students as parallel arrays
    student_regs = request.form.getlist("student_reg_no[]")
    statuses = request.form.getlist("status[]")
    docs = []
    for i, reg in enumerate(student_regs):
        docs.append({
            "student_reg_no": reg,
            "faculty_reg_no": session.get("reg_no"),
            "subject_name": subject_name,
            "subject_code": subject_code,
            "date": datetime.strptime(date, "%Y-%m-%d") if date else datetime.utcnow(),
            "time_period": time_period,
            "status": statuses[i] if i < len(statuses) else "Absent",
            "created_at": datetime.utcnow()
        })
    if docs:
        db["attendance"].insert_many(docs)
        flash("Attendance recorded.", "success")
    else:
        flash("No attendance data submitted.", "warning")
    return redirect(url_for("faculty_bp.dashboard"))

@faculty_bp.route("/assignments", methods=["GET", "POST"])
@login_required_faculty
def assignments():
    db = get_mongo_db()
    if request.method == "GET":
        # Fetch assignments created by this faculty and convert to plain dicts for the template
        raw_assignments = list(db["assignments"].find({"faculty_reg_no": session.get("reg_no")}).sort("created_at", -1))
        assignments_for_template = []
        for a in raw_assignments:
            assignments_for_template.append({
                "assignment_id": str(a.get("_id")),
                "assignment_title": a.get("assignment_title"),
                "subject_name": a.get("subject_name"),
                "subject_code": a.get("subject_code"),
                "due_date": a.get("due_date"),
                "semester": a.get("semester"),
                "created_at": a.get("created_at")
            })
        return render_template("assignments.html", assignments=assignments_for_template)

    # ----------------- POST branch (create assignment + submissions) -----------------
    subject_name = (request.form.get("subject_name") or "").strip()
    subject_code = (request.form.get("subject_code") or "").strip()
    semester = (request.form.get("semester") or "").strip()
    title = request.form.get("assignment_title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")  # optional YYYY-MM-DD
    department = request.form.get("department") or None

    doc = {
        "subject_name": subject_name if subject_name else None,
        "subject_code": subject_code if subject_code else None,
        "semester": semester if semester else None,
        "assignment_title": title,
        "description": description,
        "due_date": datetime.strptime(due_date, "%Y-%m-%d") if due_date else None,
        "faculty_reg_no": session.get("reg_no"),
        "department": department,
        "created_at": datetime.utcnow()
    }
    res = db["assignments"].insert_one(doc)
    assignment_id = res.inserted_id

    # ---------- Determine enrolled students ----------
    enrolled_set = set()

    batch_query = {}
    if subject_code:
        batch_query["subject_code"] = subject_code
    elif subject_name:
        batch_query["subject_name"] = subject_name

    if semester:
        batch_query["semester"] = semester
    if department:
        batch_query["department"] = department

    try:
        batch_cursor = list(db["batches"].find(batch_query))
    except Exception:
        batch_cursor = []

    if batch_cursor:
        for b in batch_cursor:
            if b.get("student_reg_no"):
                enrolled_set.add(b.get("student_reg_no"))
    else:
        reg_query = {}
        if semester:
            reg_query["semester"] = semester
        if department:
            reg_query["department"] = department

        regs = db["semester_registrations"].find(reg_query)
        for r in regs:
            for s in r.get("subjects", []):
                s_code = (s.get("subject_code") or "").strip()
                s_name = (s.get("subject_name") or "").strip()
                matched = False
                if subject_code and s_code and s_code.lower() == subject_code.lower():
                    matched = True
                elif subject_name and s_name and s_name.lower() == subject_name.lower():
                    matched = True
                if matched:
                    enrolled_set.add(r.get("student_reg_no"))

    submission_docs = []
    if enrolled_set:
        students_cursor = db["students"].find({"registration_number": {"$in": list(enrolled_set)}})
        for st in students_cursor:
            submission_docs.append({
                "assignment_id": assignment_id,
                "student_reg_no": st.get("registration_number"),
                "student_name": st.get("name"),
                "student_roll_number": st.get("roll_number"),
                "faculty_reg_no": session.get("reg_no"),
                "status": "Not Submitted",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

    if submission_docs:
        existing_cursor = db["assignment_submissions"].find({"assignment_id": assignment_id})
        existing_students = set([e.get("student_reg_no") for e in existing_cursor])
        to_insert = [d for d in submission_docs if d["student_reg_no"] not in existing_students]
        if to_insert:
            db["assignment_submissions"].insert_many(to_insert)

    flash("Assignment created and submissions prepared.", "success")
    return redirect(url_for("faculty_bp.assignments"))

@faculty_bp.route("/assignments/<assignment_id>/mark", methods=["POST"])
@login_required_faculty
def mark_assignment(assignment_id):
    db = get_mongo_db()
    student_regs = request.form.getlist("student_reg_no[]")
    statuses = request.form.getlist("status[]")
    for i, reg in enumerate(student_regs):
        db["assignment_submissions"].update_one(
            {"assignment_id": bson.ObjectId(assignment_id), "student_reg_no": reg},
            {"$set": {"status": statuses[i], "updated_at": datetime.utcnow()}},
            upsert=False
        )
    flash("Assignment statuses updated.", "success")
    return redirect(url_for("faculty_bp.assignments"))

@faculty_bp.route("/toggle-registration", methods=["POST"])
@login_required_faculty
def toggle_registration():
    db = get_mongo_db()
    action = request.form.get("action")  # "open" or "close"
    val = "open" if action == "open" else "closed"
    db["settings"].update_one({"key": "semester_registration_status"}, {"$set": {"value": val}}, upsert=True)
    flash(f"Semester registration set to {val}.", "success")
    return redirect(url_for("faculty_bp.dashboard"))

@faculty_bp.route("/api/enrolled-students")
@login_required_faculty
def api_enrolled_students():
    """
    Returns JSON: { ok: True, students: [ { registration_number, name, roll_number, department } ] }
    Query params: subject_name (required), semester (optional), batch (optional), department (optional)
    """
    db = get_mongo_db()
    subject_name = request.args.get("subject_name")
    semester = request.args.get("semester")
    batch = request.args.get("batch")
    department = request.args.get("department")

    if not subject_name:
        return jsonify({"ok": False, "error": "subject_name required"}), 400

    enrolled_reg_nos = set()

    # Prefer explicit batches/enrollments
    batch_query = {"subject_name": subject_name}
    if semester:
        batch_query["semester"] = semester
    if batch:
        batch_query["batch"] = batch
    if department:
        batch_query["department"] = department

    batch_cursor = list(db["batches"].find(batch_query))
    if batch_cursor:
        for b in batch_cursor:
            enrolled_reg_nos.add(b.get("student_reg_no"))
    else:
        # Fallback to semester_registrations
        reg_query = {}
        if semester:
            reg_query["semester"] = semester
        if department:
            reg_query["department"] = department
        regs = db["semester_registrations"].find(reg_query)
        for r in regs:
            for s in r.get("subjects", []):
                if s.get("subject_name", "").strip().lower() == subject_name.strip().lower():
                    enrolled_reg_nos.add(r.get("student_reg_no"))

    students = []
    if enrolled_reg_nos:
        cursor = db["students"].find({"registration_number": {"$in": list(enrolled_reg_nos)}})
        for st in cursor:
            students.append({
                "registration_number": st.get("registration_number"),
                "name": st.get("name"),
                "roll_number": st.get("roll_number"),
                "department": st.get("department")
            })

    return jsonify({"ok": True, "students": students})

@faculty_bp.route("/assignments/<assignment_id>/review", methods=["GET"])
@login_required_faculty
def review_assignment(assignment_id):
    db = get_mongo_db()

    try:
        aid = bson.ObjectId(assignment_id)
    except Exception:
        flash("Invalid assignment ID.", "danger")
        return redirect(url_for("faculty_bp.assignments"))

    # Ensure faculty owns the assignment
    assignment = db["assignments"].find_one({
        "_id": aid,
        "faculty_reg_no": session.get("reg_no")
    })

    if not assignment:
        flash("Assignment not found or unauthorized access.", "danger")
        return redirect(url_for("faculty_bp.assignments"))

    # Fetch submissions
    submissions = list(
        db["assignment_submissions"].find({"assignment_id": aid}).sort("student_reg_no", 1)
    )

    # Convert ObjectId to string BEFORE passing to template
    assignment["assignment_id_str"] = str(assignment["_id"])

    return render_template(
        "assignment_mark.html",
        assignment=assignment,
        submissions=submissions
    )


@faculty_bp.route("/logout")
def logout():
    session_keys = ["role", "reg_no", "faculty_id"]
    for k in session_keys:
        session.pop(k, None)
    resp = make_response(redirect(url_for("faculty_bp.login")))
    resp = set_nocache(resp)
    return resp
