from flask import Flask, render_template, request, jsonify , send_file
from flask import session, redirect, url_for
from functools import wraps
import requests
import os
from tavily import TavilyClient
import random
from werkzeug.utils import secure_filename
from PIL import Image
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from docx import Document
import fitz  # PyMuPDF


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



# ======================= QUIZ =======================

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
            import re

            # Markdown links
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





# ======================= DASHBOARD =======================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ======================= DOCUMENTATION =======================
@app.route("/docs")
def docs():
    return render_template("docs.html")


# ======================= CONVERTER =======================
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CONVERTED_FOLDER"] = CONVERTED_FOLDER
# ================= CONVERTER PAGE =================
@app.route("/converter")
def converter():
    return render_template("converter.html")


# ================= JPG → PDF =================
@app.route("/convert/jpg-to-pdf", methods=["POST"])
def jpg_to_pdf():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    image = Image.open(filepath).convert("RGB")
    output_path = os.path.join(app.config["CONVERTED_FOLDER"], filename.rsplit(".", 1)[0] + ".pdf")
    image.save(output_path)

    return send_file(output_path, as_attachment=True)


# ================= PDF → JPG =================
@app.route("/convert/pdf-to-jpg", methods=["POST"])
def pdf_to_jpg():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    doc = fitz.open(filepath)
    page = doc[0]
    pix = page.get_pixmap()

    output_path = os.path.join(app.config["CONVERTED_FOLDER"], filename.rsplit(".", 1)[0] + ".jpg")
    pix.save(output_path)

    return send_file(output_path, as_attachment=True)


# ================= WORD → PDF =================
@app.route("/convert/word-to-pdf", methods=["POST"])
def word_to_pdf():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    doc = Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])

    output_path = os.path.join(app.config["CONVERTED_FOLDER"], filename.rsplit(".", 1)[0] + ".pdf")
    pdf = SimpleDocTemplate(output_path)
    styles = getSampleStyleSheet()
    elements = [Paragraph(text, styles["Normal"])]
    pdf.build(elements)

    return send_file(output_path, as_attachment=True)


# ================= PDF → WORD =================
@app.route("/convert/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()

    output_path = os.path.join(app.config["CONVERTED_FOLDER"], filename.rsplit(".", 1)[0] + ".docx")

    document = Document()
    document.add_paragraph(text)
    document.save(output_path)

    return send_file(output_path, as_attachment=True)



# ======================= LOGIN =======================
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


