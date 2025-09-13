from flask import Flask, render_template
from .routes import main
import os

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Register blueprint
    app.register_blueprint(main)

    # Serve the main page
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
