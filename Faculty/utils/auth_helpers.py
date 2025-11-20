# Faculty/utils/auth_helpers.py
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required_faculty(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "faculty" or not session.get("reg_no"):
            flash("Please log in as faculty to continue.", "warning")
            return redirect(url_for("faculty_bp.login"))
        return f(*args, **kwargs)
    return decorated

def set_nocache(response):
    response.nocache = True
    return response
