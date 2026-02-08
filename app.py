from flask import Flask, render_template, request
from duckduckgo_search import DDGS
from nltk.tokenize import sent_tokenize

app = Flask(__name__)

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")


# LEARN / SEARCH
@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("topic", "")

        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })

    return render_template("search.html", results=results, query=query)


# QUIZ (no DB for now)
@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/result", methods=["POST"])
def result():
    name = request.form.get("name")
    score = request.form.get("score")
    return render_template("result.html", name=name, score=score)


# SUMMARY
@app.route("/summary", methods=["GET", "POST"])
def summary():
    summarized = ""
    if request.method == "POST":
        text = request.form.get("text", "")
        sentences = sent_tokenize(text)
        summarized = " ".join(sentences[:3])
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
def converter():
    return render_template("converter.html")


# LOGIN
@app.route("/login")
def login():
    return render_template("login.html")


# ❌ DO NOT USE app.run() ON VERCEL
