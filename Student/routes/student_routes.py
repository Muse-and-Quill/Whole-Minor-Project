# Student/routes/student_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from services.mongo_client import get_mongo_db
from services.email_service import send_email
from utils.auth_helpers import login_required_student, set_nocache
from utils.validators import is_valid_registration
from datetime import datetime, timedelta
import random
import bson
from bson import ObjectId

student_bp = Blueprint("student_bp", __name__, template_folder="../../templates/student", static_folder="../../static")

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

@student_bp.route("/")
def index():
    return render_template("index.html")

@student_bp.route("/login", methods=["GET", "POST"])
def login():
    db = get_mongo_db()
    if request.method == "GET":
        return render_template("login.html")

    mode = request.form.get("mode", "password")  # password or otp
    reg_no = request.form.get("registration_number", "").strip().upper()

    if not is_valid_registration(reg_no):
        flash("Please enter a valid registration number.", "danger")
        return render_template("login.html")

    student = db["students"].find_one({"registration_number": reg_no})
    if not student or not student.get("is_active", True):
        flash("User not found or inactive.", "danger")
        return render_template("login.html")

    # PASSWORD MODE
    if mode == "password":
        password = request.form.get("password", "")
        if not password:
            flash("Enter password.", "danger")
            return render_template("login.html")
        if not student.get("password_hash") or not check_password_hash(student["password_hash"], password):
            flash("Invalid credentials.", "danger")
            return render_template("login.html")
        # success -> create session
        session["role"] = "student"
        session["reg_no"] = student["registration_number"]
        session["student_id"] = str(student["_id"])
        flash("Logged in successfully.", "success")
        return redirect(url_for("student_bp.dashboard"))

    # OTP MODE (send OTP)
    if mode == "otp":
        otp = f"{random.randint(100000, 999999)}"
        _save_otp(db, reg_no, otp, purpose="login")
        to_email = student.get("email")
        subj = "UAP Student Login OTP"
        body = f"Dear {student.get('name','Student')},\n\nYour OTP is {otp}. It expires in {__import__('config').Config.OTP_EXPIRE_MINUTES} minutes.\n\nUAP"
        send_email(subj, body, to_email)
        return render_template("login.html", otp_sent=True, reg_no=reg_no)

    flash("Invalid login mode.", "danger")
    return render_template("login.html")

@student_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    db = get_mongo_db()
    reg_no = request.form.get("registration_number", "").strip().upper()
    otp = request.form.get("otp", "").strip()
    if not is_valid_registration(reg_no) or not otp:
        flash("Invalid request.", "danger")
        return redirect(url_for("student_bp.login"))
    ok, msg = _verify_and_consume_otp(db, reg_no, otp, purpose="login")
    if not ok:
        flash(msg or "OTP verification failed.", "danger")
        return redirect(url_for("student_bp.login"))

    student = db["students"].find_one({"registration_number": reg_no})
    if not student:
        flash("User not found.", "danger")
        return redirect(url_for("student_bp.login"))

    # create session
    session["role"] = "student"
    session["reg_no"] = student["registration_number"]
    session["student_id"] = str(student["_id"])
    flash("Logged in successfully (via OTP).", "success")
    return redirect(url_for("student_bp.dashboard"))

@student_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    db = get_mongo_db()
    if request.method == "GET":
        return render_template("forgot_password.html", step="request")
    step = request.form.get("step", "request")
    if step == "request":
        reg_no = request.form.get("registration_number", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        if not is_valid_registration(reg_no) or not email:
            flash("Enter registration number and email.", "danger")
            return render_template("forgot_password.html", step="request")
        student = db["students"].find_one({"registration_number": reg_no, "email": email})
        if not student:
            flash("No matching student record found.", "danger")
            return render_template("forgot_password.html", step="request")
        otp = f"{random.randint(100000, 999999)}"
        _save_otp(db, reg_no, otp, purpose="reset")
        subj = "UAP Student Password Reset OTP"
        body = f"Dear {student.get('name','Student')},\n\nYour password reset OTP is {otp}. It expires in {__import__('config').Config.OTP_EXPIRE_MINUTES} minutes.\n\nUAP"
        send_email(subj, body, email)
        flash("OTP sent to your email.", "info")
        return render_template("forgot_password.html", step="verify", reg_no=reg_no)
    elif step == "verify":
        reg_no = request.form.get("registration_number", "").strip().upper()
        otp = request.form.get("otp", "").strip()
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")
        if not (reg_no and otp and new_pw and confirm_pw):
            flash("All fields are required.", "danger")
            return render_template("forgot_password.html", step="verify", reg_no=reg_no)
        if new_pw != confirm_pw:
            flash("Passwords do not match.", "danger")
            return render_template("forgot_password.html", step="verify", reg_no=reg_no)
        ok, msg = _verify_and_consume_otp(db, reg_no, otp, purpose="reset")
        if not ok:
            flash(msg or "OTP invalid or expired.", "danger")
            return render_template("forgot_password.html", step="verify", reg_no=reg_no)
        # update password
        pw_hash = generate_password_hash(new_pw)
        res = db["students"].update_one({"registration_number": reg_no}, {"$set": {"password_hash": pw_hash}})
        if res.matched_count:
            flash("Password updated. You may now log in.", "success")
            return redirect(url_for("student_bp.login"))
        flash("Unable to update password.", "danger")
        return render_template("forgot_password.html", step="verify", reg_no=reg_no)

@student_bp.route("/dashboard")
@login_required_student
def dashboard():
    db = get_mongo_db()
    reg_no = session.get("reg_no")
    student = db["students"].find_one({"registration_number": reg_no})
    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for("student_bp.login"))

    # profile data
    profile = {
        "name": student.get("name"),
        "registration_number": student.get("registration_number"),
        "roll_number": student.get("roll_number"),
        "department": student.get("department"),
        "session_start": student.get("session_start_year"),
        "session_end": student.get("session_end_year"),
    }

    # read semester registration open/closed from settings
    settings = db["settings"].find_one({"key": "semester_registration_status"})
    registration_open = settings and settings.get("value") == "open"

    # load recent attendance items (limit 100)
    attendance_cursor = db["attendance"].find({"student_reg_no": reg_no}).sort("date", -1).limit(100)
    attendance = list(attendance_cursor)

    # ------------------ NEW: load assignments via assignment_submissions ------------------
    # Fetch student's assignment_submissions
    submissions = list(db["assignment_submissions"].find({"student_reg_no": reg_no}))
    assignments = []
    if submissions:
        # collect assignment ObjectIds
        assignment_object_ids = []
        for s in submissions:
            aid = s.get("assignment_id")
            if aid:
                # ensure ObjectId
                try:
                    if isinstance(aid, ObjectId):
                        assignment_object_ids.append(aid)
                    else:
                        assignment_object_ids.append(ObjectId(aid))
                except Exception:
                    # skip if invalid
                    continue
        # fetch assignment documents in one query
        assign_docs = {}
        if assignment_object_ids:
            for a in db["assignments"].find({"_id": {"$in": assignment_object_ids}}):
                assign_docs[a["_id"]] = a
        # build final list joining submission + assignment
        for sub in submissions:
            aid = sub.get("assignment_id")
            a_doc = None
            try:
                a_doc = assign_docs.get(aid) if aid else None
            except Exception:
                a_doc = None
            if not a_doc:
                continue
            assignments.append({
                "assignment_id": str(a_doc.get("_id")),
                "title": a_doc.get("assignment_title"),
                "subject": a_doc.get("subject_name") or a_doc.get("subject_code"),
                "due_date": a_doc.get("due_date"),
                "description": a_doc.get("description"),
                "status": sub.get("status", "Pending"),
                "faculty_reg_no": a_doc.get("faculty_reg_no")
            })
    # else assignments remain empty list

    return render_template("dashboard.html",
                           profile=profile,
                           registration_open=registration_open,
                           attendance=attendance,
                           assignments=assignments)

@student_bp.route("/semester-register", methods=["POST"])
@login_required_student
def semester_register():
    db = get_mongo_db()
    reg_no = session.get("reg_no")
    student = db["students"].find_one({"registration_number": reg_no})
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("student_bp.dashboard"))

    settings = db["settings"].find_one({"key": "semester_registration_status"})
    if not (settings and settings.get("value") == "open"):
        flash("Registration is currently closed.", "warning")
        return redirect(url_for("student_bp.dashboard"))

    semester = request.form.get("semester") or request.json.get("semester")
    subjects = request.form.getlist("subject_name[]") or request.json.get("subjects", [])
    subject_codes = request.form.getlist("subject_code[]") or []
    subject_depts = request.form.getlist("subject_dept[]") or []

    if not semester or not subjects:
        flash("Semester and subjects required.", "danger")
        return redirect(url_for("student_bp.dashboard"))

    subj_list = []
    if isinstance(subjects, list) and subjects and isinstance(subjects[0], dict):
        subj_list = subjects
    else:
        for i, name in enumerate(subjects):
            subj_list.append({
                "subject_name": name,
                "subject_code": subject_codes[i] if i < len(subject_codes) else "",
                "department": subject_depts[i] if i < len(subject_depts) else student.get("department")
            })
    doc = {
        "student_reg_no": reg_no,
        "student_roll_no": student.get("roll_number"),
        "department": student.get("department"),
        "semester": semester,
        "subjects": subj_list,
        "timestamp": datetime.utcnow()
    }
    db["semester_registrations"].insert_one(doc)
    flash("Semester registration submitted.", "success")
    return redirect(url_for("student_bp.dashboard"))

@student_bp.route("/logout")
def logout():
    session_keys = ["role", "reg_no", "student_id"]
    for k in session_keys:
        session.pop(k, None)
    resp = make_response(redirect(url_for("student_bp.login")))
    resp = set_nocache(resp)
    return resp
