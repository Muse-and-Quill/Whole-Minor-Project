# Faculty/app.py
import os
from flask import Flask, redirect, url_for
from routes.faculty_routes import faculty_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object("config.Config")
    app.secret_key = os.getenv("SECRET_KEY", app.config.get("SECRET_KEY", "dev-secret"))

    # Register faculty blueprint
    app.register_blueprint(faculty_bp, url_prefix="/faculty")

    # root redirect to faculty landing
    @app.route("/")
    def root():
        return redirect(url_for("faculty_bp.index"))

    @app.after_request
    def add_no_cache_headers(resp):
        # Use resp.nocache set by logout helpers if needed
        if getattr(resp, "nocache", False):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
        return resp

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 5002)), debug=True)
