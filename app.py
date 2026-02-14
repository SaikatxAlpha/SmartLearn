from flask import Flask, render_template, request, jsonify
from flask import session, redirect, url_for
from functools import wraps
import requests
import os
#from duckduckgo_search import DDGS

#from flask_sqlalchemy import SQLAlchemy
#from flask_mail import Mail, Message
#from itsdangerous import URLSafeTimedSerializer
#from models import db, User
#import random


app = Flask(__name__)
app.secret_key = "change-this-later"

# ---------------- LOGIN REQUIRED DECORATOR ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")


# LEARN / SEARCH
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
@app.route("/search")
def search_page():
    return render_template("search.html")

@app.route("/api/search")
def api_search():
    query = request.args.get("q")

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 10
    }

    response = requests.post(url, json=payload)
    data = response.json()

    results = []

    for item in data.get("results", []):
        content = item.get("content", "")
        short_snippet = " ".join(content.split()[:7]) + "..."

        results.append({
            "title": item.get("title"),
            "snippet": short_snippet,
            "link": item.get("url")
        })

    return jsonify({"items": results})




# QUIZ (no DB for now)
@app.route("/quiz")
@login_required
def quiz():
    return render_template("quiz.html")


@app.route("/result", methods=["POST"])
def result():
    name = request.form.get("name")
    score = request.form.get("score")
    return render_template("result.html", name=name, score=score)


# SUMMARY
@app.route("/summary", methods=["GET", "POST"])
@login_required
def summary():
    summarized = ""
    if request.method == "POST":
        text = request.form.get("text", "")

    return render_template("summary.html", summarized=summarized)


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# DOCUMENTATION
@app.route("/docs")
def docs():
    return render_template("docs.html")


# CONVERTER
@app.route("/converter")
@login_required
def converter():
    return render_template("converter.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")

        # simple login for now
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))

    return render_template("login.html")

#LOGOUT ROUTE
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


