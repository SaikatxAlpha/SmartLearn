from flask import Flask, render_template, request, jsonify
from flask import session, redirect, url_for
from functools import wraps
import requests
import os
from tavily import TavilyClient
#from duckduckgo_search import DDGS

#from flask_sqlalchemy import SQLAlchemy
#from flask_mail import Mail, Message
#from itsdangerous import URLSafeTimedSerializer
#from models import db, User
import random


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



# QUIZ 

# Temporary sample question generator
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
def generate_quiz(topic):
    response = tavily.search(query=topic, search_depth="basic", max_results=3)
    
    content = ""
    for result in response["results"]:
        content += result["content"] + " "

    sentences = content.split(".")
    sentences = [s.strip() for s in sentences if len(s.strip()) > 40]

    questions = []

    for i in range(min(5, len(sentences))):
        sentence = sentences[i]

        question = f"What does this statement describe?\n\n'{sentence}'"

        correct_answer = topic

        options = [
            topic,
            "Artificial Intelligence",
            "A programming language",
            "A scientific theory"
        ]

        random.shuffle(options)

        questions.append({
            "question": question,
            "options": options,
            "answer": topic
        })

    return questions


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        topic = request.form["topic"]
        questions = generate_quiz(topic)
        return render_template("quiz.html", questions=questions, topic=topic)
    return render_template("quiz.html", questions=None)


@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    score = 0
    total = int(request.form["total"])

    for i in range(total):
        selected = request.form.get(f"q{i}")
        correct = request.form.get(f"correct{i}")
        if selected == correct:
            score += 1

    return render_template("result.html", score=score, total=total)





# ================= SUMMARIZE =================

@app.route("/summary", methods=["GET", "POST"])
def summarize():
    summary = None

    if request.method == "POST":
        try:
            text = request.form.get("topic")

            if not text:
                summary = "Please enter text."
                return render_template("summarize.html", summary=summary)

            # If short input → use Tavily search
            if len(text) <= 400:
                response = tavily.search(
                    query=text,
                    search_depth="basic",
                    max_results=3
                )

                content = ""
                if response and response.get("results"):
                    for result in response["results"]:
                        content += result.get("content", "") + " "
                text = content

            # Now summarize the text directly
            import re

            # Clean markdown links
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'\s+', ' ', text)

            sentences = re.split(r'\.\s+', text)

            cleaned = []
            seen = set()

            for s in sentences:
                s = s.strip()
                if len(s) > 60:
                    key = s.lower()
                    if key not in seen:
                        seen.add(key)
                        cleaned.append(s)

            if not cleaned:
                summary = "Not enough meaningful content to summarize."
            else:
                summary = ". ".join(cleaned[:3]) + "."

        except Exception as e:
            summary = f"Error occurred: {str(e)}"

    return render_template("summarize.html", summary=summary)





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


