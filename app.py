from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import nltk
from nltk.tokenize import sent_tokenize
from duckduckgo_search import DDGS
nltk.download('punkt')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- DATABASE ----------------
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    score = db.Column(db.Integer)

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

# LEARN / SEARCH
@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    query = ""

    if request.method == 'POST':
        query = request.form['topic']

        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r["title"],
                    "link": r["href"],
                    "snippet": r["body"]
                })

    return render_template(
        'search.html',
        results=results,
        query=query
    )
# QUIZ
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/result', methods=['POST'])
def result():
    name = request.form['name']
    score = int(request.form['score'])
    db.session.add(QuizResult(name=name, score=score))
    db.session.commit()
    return render_template('result.html', name=name, score=score)

# SUMMARY
@app.route('/summary', methods=['GET', 'POST'])
def summary():
    summarized = ""
    if request.method == 'POST':
        text = request.form['text']
        sentences = sent_tokenize(text)
        summarized = " ".join(sentences[:3])
    return render_template('summary.html', summarized=summarized)

# DASHBOARD (Content Part)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# DOCUMENTATION
@app.route('/docs')
def docs():
    return render_template('docs.html')

# CONVERTER (placeholder)
@app.route('/converter')
def converter():
    return render_template('converter.html')

# LOGIN / SIGNING
@app.route('/login')
def login():
    return render_template('login.html')

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



