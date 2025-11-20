# student/app.py
import os
from flask import Flask, redirect, url_for
from routes.student_routes import student_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object("config.Config")

    # Secret key (override with env var in production)
    app.secret_key = os.getenv("SECRET_KEY", app.config.get("SECRET_KEY", "LeSserafim"))

    # Register blueprints
    app.register_blueprint(student_bp, url_prefix="/student")

    @app.route("/")
    def root():
        # redirect root to student landing page
        return redirect(url_for("student_bp.index"))
    # After request: optional global no-cache (we mark responses with resp.nocache = True in logout)
    @app.after_request
    def add_no_cache_headers(resp):
        # Only add no-cache if view set attribute
        if getattr(resp, "nocache", False):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
        return resp

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
