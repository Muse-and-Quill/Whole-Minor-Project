# student/utils/auth_helpers.py
from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required_student(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "student" or not session.get("reg_no"):
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("student_bp.login"))
        return f(*args, **kwargs)
    return decorated

def set_nocache(response):
    # Mark response for after_request to add headers
    response.nocache = True
    return response
