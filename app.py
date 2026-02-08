from flask import Flask, render_template, request
from flask import session, redirect, url_for
from functools import wraps
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
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("topic", "")

        #with DDGS() as ddgs:
            #for r in ddgs.text(query, max_results=5):
                #results.append({
                    #"title": r.get("title"),
                    #"link": r.get("href"),
                    #"snippet": r.get("body")
               #})

    return render_template("search.html", results=results, query=query)


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




